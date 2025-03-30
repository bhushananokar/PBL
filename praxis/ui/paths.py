# praxis/ui/paths.py
import streamlit as st
from typing import Callable

def render_paths_page(db, assistant, go_to_page: Callable) -> None:
    """
    Render the learning paths page.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        go_to_page: Function to navigate to a different page
    """
    st.title("Learning Paths")
    
    # Get available learning paths
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT lp.path_id, lp.title, lp.description, lp.difficulty, pl.name as language,
               COUNT(lpi.challenge_id) as challenge_count
        FROM learning_paths lp
        JOIN programming_languages pl ON lp.lang_id = pl.lang_id
        LEFT JOIN learning_path_items lpi ON lp.path_id = lpi.path_id
        GROUP BY lp.path_id
        ORDER BY lp.created_at DESC
    """)
    
    paths = cursor.fetchall()
    
    if not paths:
        st.info("No learning paths available yet. Generate one from your profile!")
    else:
        for path in paths:
            path_id, title, description, difficulty, language, challenge_count = path
            
            difficulty_stars = "⭐" * difficulty
            
            st.markdown(f"""
            <div class="path-card" id="path_{path_id}">
            <h3>{title}</h3>
            <p>Difficulty: {difficulty_stars} | Language: {language} | Challenges: {challenge_count}</p>
            <p>{description}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # View path button
            if st.button("View Path", key=f"view_path_{path_id}"):
                # Get challenges in this path
                path_challenges = db.get_learning_path_challenges(path_id)
                
                st.markdown(f"### {title} - Challenge Sequence")
                
                for i, challenge in enumerate(path_challenges):
                    c_id, c_title, c_desc, c_diff, c_lang = challenge
                    
                    st.markdown(f"""
                    <div class="challenge-card">
                    <h4>Step {i+1}: {c_title}</h4>
                    <p>Difficulty: {"⭐" * c_diff} | Language: {c_lang}</p>
                    <p>{c_desc}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Start Challenge", key=f"start_path_{c_id}"):
                        start_challenge(db, assistant, c_id, c_desc, go_to_page)
    
    # Generate a new learning path
    st.markdown("### Create New Learning Path")
    
    languages = ["Python", "JavaScript", "Java", "C++", "C#", "Go", "Ruby", "PHP", "TypeScript", "Rust", "Swift", "Kotlin"]
    new_path_lang = st.selectbox("Select Language", languages)
    
    focus_areas = ["Algorithms", "Data Structures", "Web Development", "Object-Oriented Programming", 
                 "Functional Programming", "Backend Development", "Frontend Development"]
    selected_focus = st.multiselect("Select Focus Areas", focus_areas)
    
    difficulty = st.slider("Difficulty Level", 1, 5, 3)
    
    if st.button("Generate Path", type="primary"):
        if not selected_focus:
            st.error("Please select at least one focus area")
        else:
            with st.spinner("Generating learning path..."):
                system_prompt = f"""
                You are a programming curriculum designer. Create a learning path for {new_path_lang} focusing on {', '.join(selected_focus)}.
                
                Design a sequence of 5-7 coding challenges that build skills incrementally.
                For each challenge, provide:
                1. A clear title
                2. A brief description of what to implement
                3. The primary skills it develops
                4. Approximate difficulty (1-5, with {difficulty} as the average)
                
                Format as a JSON array of challenge objects.
                """
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create a {new_path_lang} learning path focusing on {', '.join(selected_focus)}"}
                ]
                
                response = assistant._send_request(assistant.llama3_70b, messages, temperature=0.4, max_tokens=4000)
                
                if 'choices' in response and len(response['choices']) > 0:
                    import re
                    import json
                    
                    content = response['choices'][0]['message']['content']
                    
                    # Extract JSON
                    try:
                        json_pattern = r'\[[\s\S]*\]'
                        json_match = re.search(json_pattern, content)
                        if json_match:
                            path_json = json_match.group(0)
                            path_challenges = json.loads(path_json)
                            
                            # Create a learning path
                            path_title = f"{new_path_lang} - {', '.join(selected_focus[:2])}"
                            path_desc = f"A learning path for {new_path_lang} focusing on {', '.join(selected_focus)}"
                            
                            path_id = db.get_or_create_learning_path(path_title, path_desc, new_path_lang, difficulty)
                            
                            # Add challenges to the path
                            for i, challenge in enumerate(path_challenges):
                                # Create the challenge
                                challenge_desc = f"Create code in {new_path_lang} that: {challenge['description']}"
                                enhanced_prompt = assistant.enhance_prompt(challenge_desc)
                                
                                challenge_id = db.store_challenge(
                                    challenge['title'], 
                                    enhanced_prompt, 
                                    new_path_lang, 
                                    difficulty=challenge.get('difficulty', difficulty)
                                )
                                
                                # Map skills to challenge
                                if 'skills' in challenge:
                                    skill_relevance = {skill: 0.8 for skill in challenge['skills']}
                                    db.map_challenge_skills(challenge_id, skill_relevance)
                                
                                # Add to learning path
                                db.add_challenge_to_path(path_id, challenge_id, i)
                            
                            st.success("Learning path created successfully!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error creating learning path: {str(e)}")

def start_challenge(db, assistant, challenge_id: str, description: str, go_to_page: Callable) -> None:
    """
    Start a specific challenge.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        challenge_id: ID of the challenge to start
        description: Description of the challenge
        go_to_page: Function to navigate to a different page
    """
    st.session_state.challenge_id = challenge_id
    st.session_state.problem_desc = description
    
    # Retrieve challenge data
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT enhanced_prompt, solution 
        FROM challenges 
        WHERE challenge_id = ?
    """, (challenge_id,))
    result = cursor.fetchone()
    
    if result:
        enhanced_prompt, solution = result
        
        # Generate challenge if not already done
        if not enhanced_prompt:
            enhanced_prompt = assistant.enhance_prompt(description)
            db.conn.execute("""
                UPDATE challenges 
                SET enhanced_prompt = ? 
                WHERE challenge_id = ?
            """, (enhanced_prompt, challenge_id))
            db.conn.commit()
        
        st.session_state.enhanced_prompt = enhanced_prompt
        
        # Generate challenge text
        st.session_state.challenge = assistant.generate_learning_challenge(enhanced_prompt)
        
        # Set starting point
        st.session_state.attempt_number = 1
        st.session_state.start_time = None  # Will be set in challenge page
        go_to_page("challenge")