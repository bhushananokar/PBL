# praxis/ui/dashboard.py
import streamlit as st
from typing import Callable

from utils.visualization import render_progress_chart, render_skill_chart

def render_dashboard(db, assistant, reset_app: Callable, go_to_page: Callable) -> None:
    """
    Render the user dashboard page.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        reset_app: Function to reset the app state
        go_to_page: Function to navigate to a different page
    """
    st.title(f"Your Coding Dashboard")
    
    # Progress metrics
    progress = db.get_user_progress(st.session_state.user_id)
    
    st.markdown("### Your Progress")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
        <div class="metric-value">{progress['total_attempts']}</div>
        <div class="metric-label">Total Attempts</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        success_rate = 0 if progress['total_attempts'] == 0 else (progress['successful_attempts'] / progress['total_attempts']) * 100
        st.markdown(f"""
        <div class="metric-card">
        <div class="metric-value">{success_rate:.1f}%</div>
        <div class="metric-label">Success Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
        <div class="metric-value">{progress['challenges_attempted']}</div>
        <div class="metric-label">Challenges Attempted</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_score = progress['average_score'] * 100
        st.markdown(f"""
        <div class="metric-card">
        <div class="metric-value">{avg_score:.1f}%</div>
        <div class="metric-label">Average Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Skill visualization
    st.markdown("### Your Skills")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Get user skills
        strong_skills = db.get_user_strongest_skills(st.session_state.user_id, limit=5)
        weak_skills = db.get_user_weakest_skills(st.session_state.user_id, limit=5)
        
        if strong_skills:
            fig = render_skill_chart(strong_skills + weak_skills, "Skills Overview")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Complete some challenges to see your skill progress!")
    
    with col2:
        if strong_skills:
            st.markdown("#### Strengths")
            for _, name, _, prof in strong_skills:
                st.markdown(f"""
                <div class="skill-badge">{name}: {prof:.2f}</div>
                """, unsafe_allow_html=True)
            
            st.markdown("#### Areas for Improvement")
            for _, name, _, prof in weak_skills:
                st.markdown(f"""
                <div class="weak-badge">{name}: {prof:.2f}</div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            #### Getting Started
            1. Start a coding challenge
            2. Submit your solution
            3. Get personalized feedback
            4. Track your skill improvement
            """)
    
    # Recent activity
    st.markdown("### Recent Activity")
    recent_attempts = db.get_user_recent_attempts(st.session_state.user_id)
    
    if recent_attempts:
        # Progress chart
        fig = render_progress_chart(st.session_state.user_id, db)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent attempts table
        st.markdown("#### Recent Challenge Attempts")
        for attempt in recent_attempts:
            attempt_id, challenge_id, title, score, attempt_number, successful, created_at = attempt
            
            status = "✅ Success" if successful else "⏳ In Progress"
            score_display = f"{score * 100:.1f}%" if score is not None else "N/A"
            
            st.markdown(f"""
            <div class="challenge-card">
            <h4>{title}</h4>
            <p>Attempt #{attempt_number} | Score: {score_display} | Status: {status} | {created_at}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No challenge attempts yet. Start solving a challenge to see your activity!")
    
    # Recommended next challenges
    st.markdown("### Recommended Challenges")
    
    render_challenge_recommendations(db, assistant, go_to_page)
    
    # Create a new challenge
    st.markdown("### Start a New Challenge")
    if st.button("Create New Challenge", type="primary"):
        reset_app()
        go_to_page("start")

def render_challenge_recommendations(db, assistant, go_to_page: Callable) -> None:
    """
    Render the recommended challenges section.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        go_to_page: Function to navigate to a different page
    """
    weak_skills = db.get_user_weakest_skills(st.session_state.user_id, limit=5)
    
    if weak_skills:
        recommended = db.get_recommended_challenges(st.session_state.user_id)
        
        if recommended:
            for challenge in recommended:
                challenge_id, title, description, difficulty, language, skills = challenge
                
                difficulty_stars = "⭐" * difficulty
                
                st.markdown(f"""
                <div class="recommendation-card">
                <h4>{title}</h4>
                <p>Difficulty: {difficulty_stars} | Language: {language}</p>
                <p>{description[:100]}...</p>
                <p>Skills: {skills}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("Start", key=f"start_{challenge_id}"):
                        start_challenge(db, assistant, challenge_id, description, go_to_page)
        
        # Generate a custom challenge based on weak skills
        if st.button("Generate Custom Challenge for My Skill Gaps"):
            weak_skill_names = [name for _, name, _, _ in weak_skills[:3]]
            
            with st.spinner("Generating custom challenge..."):
                generate_custom_challenge(db, assistant, weak_skill_names, "Python", 3, go_to_page)
    else:
        st.info("Complete some challenges to get personalized recommendations!")

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

def generate_custom_challenge(db, assistant, weak_skill_names: list, language: str, difficulty: int, go_to_page: Callable) -> None:
    """
    Generate a custom challenge based on skill gaps.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        weak_skill_names: List of skill names to target
        language: Programming language for the challenge
        difficulty: Difficulty level (1-5)
        go_to_page: Function to navigate to a different page
    """
    system_prompt = f"""
    You are a programming challenge creator. Create a coding challenge that targets these skills:
    {', '.join(weak_skill_names)}
    
    The challenge should:
    1. Be clear and specific
    2. Have difficulty level: {difficulty}/5
    3. Combine multiple skills in a practical scenario
    4. Include input/output examples
    5. Be relatively self-contained (not requiring external libraries)
    
    Format: Create a function that...
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Create a {language} coding challenge that develops skills in {', '.join(weak_skill_names)}"}
    ]
    
    response = assistant._send_request(assistant.llama3_70b, messages, temperature=0.4, max_tokens=1000)
    
    if 'choices' in response and len(response['choices']) > 0:
        problem_desc = f"Create code in {language} that: {response['choices'][0]['message']['content']}"
        enhanced_prompt = assistant.enhance_prompt(problem_desc)
        challenge = assistant.generate_learning_challenge(enhanced_prompt)
        
        # Save to database
        challenge_id = db.store_challenge(problem_desc, enhanced_prompt, language, difficulty)
        
        # Map skills
        skill_relevance = {skill: 0.9 for skill in weak_skill_names}
        db.map_challenge_skills(challenge_id, skill_relevance)
        
        # Store in session
        st.session_state.problem_desc = problem_desc
        st.session_state.enhanced_prompt = enhanced_prompt
        st.session_state.challenge = challenge
        st.session_state.challenge_id = challenge_id
        st.session_state.attempt_number = 1
        st.session_state.start_time = None  # Will be set in challenge page
        
        go_to_page("challenge")