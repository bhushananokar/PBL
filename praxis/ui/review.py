# praxis/ui/review.py
import streamlit as st
from typing import Callable
from streamlit_ace import st_ace

from utils.visualization import render_mermaid

def render_review_page(db, assistant) -> None:
    """
    Render the code review page.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
    """
    st.title("Code Quality Review")
    st.markdown(
        """
        <div class="feedback-card">
        <h3>Submit Your Code For Review</h3>
        <p>Paste your code below to get feedback on quality, performance, and potential improvements. This is a great way to learn best practices and improve your coding skills.</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    programming_language = st.selectbox(
        "Programming Language",
        ["Python", "JavaScript", "Java", "C++", "C#", "Go", "Ruby", "PHP", "TypeScript", "Rust", "Swift", "Kotlin"]
    )
    
    user_code = st_ace(
        placeholder="Paste your code here...",
        language=programming_language.lower(),
        theme="monokai",
        height=400,
        key="user_code_input"
    )
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        review_code = st.button("Review My Code", type="primary")
    
    with col2:
        # Additional options
        st.markdown("**Analysis Options:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            do_review = st.checkbox("Code Quality", value=True)
        with col2:
            do_complexity = st.checkbox("Complexity", value=True)
        with col3:
            do_learning = st.checkbox("Learning Path", value=True)
    
    if review_code:
        if not user_code:
            st.error("Please enter your code for review.")
        else:
            # Create tabs for different analyses
            tabs = []
            if do_review:
                tabs.append("Code Review")
            if do_complexity:
                tabs.append("Complexity Analysis")
            tabs.append("Visualization")
            if do_learning:
                tabs.append("Learning Path")
            
            # Create tab objects
            tab_objects = st.tabs(tabs)
            
            # Track current tab index
            tab_index = 0
            
            # Code Review tab
            if do_review:
                with tab_objects[tab_index]:
                    st.markdown("### Code Quality Review")
                    with st.spinner("Analyzing your code..."):
                        code_review = assistant.review_code(user_code)
                    
                    if 'overall_rating' in code_review and code_review['overall_rating'] != "N/A" and code_review['overall_rating'] != "Review failed":
                        # Try to convert to numeric if possible
                        try:
                            rating = float(code_review['overall_rating'])
                            st.markdown(f"""
                            #### Overall Rating: <div class="step-badge">{rating}/10</div>
                            """, unsafe_allow_html=True)
                        except:
                            st.markdown(f"""
                            #### Overall Rating: <div class="step-badge">{code_review['overall_rating']}</div>
                            """, unsafe_allow_html=True)
                    
                    if 'strengths' in code_review and isinstance(code_review['strengths'], list):
                        st.markdown("#### Strengths")
                        for strength in code_review['strengths']:
                            st.markdown(f"- {strength}")
                    
                    if 'improvements' in code_review and isinstance(code_review['improvements'], list):
                        st.markdown("#### Improvements")
                        for improvement in code_review['improvements']:
                            st.markdown(f"- {improvement}")
                    
                    if 'optimizations' in code_review and isinstance(code_review['optimizations'], list):
                        st.markdown("#### Optimizations")
                        for optimization in code_review['optimizations']:
                            st.markdown(f"- {optimization}")
                    
                    if 'potential_issues' in code_review and isinstance(code_review['potential_issues'], list):
                        st.markdown("#### Potential Issues")
                        for issue in code_review['potential_issues']:
                            st.markdown(f"- {issue}")
                    
                    if 'review' in code_review and not isinstance(code_review.get('strengths'), list):
                        st.markdown("#### Detailed Review")
                        st.markdown(f"""<div class="feedback-card">{code_review['review']}</div>""", unsafe_allow_html=True)
                    
                    # Code improvement suggestion
                    with st.expander("Suggested Improvements", expanded=False):
                        with st.spinner("Generating improved version..."):
                            system_prompt = """
                            You are a code improvement expert. Given a piece of code:
                            1. Create an improved version of the code that addresses the main issues
                            2. Add clear comments explaining the changes and improvements
                            3. Focus on readability, efficiency, and best practices
                            4. Maintain the original functionality but make it better
                            
                            Format your response as code only, without explanations outside the code.
                            """
                            
                            messages = [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Here's my code in {programming_language}:\n\n{user_code}\n\nPlease provide an improved version with comments explaining the changes."}
                            ]
                            
                            response = assistant._send_request(assistant.llama3_70b, messages, temperature=0.2, max_tokens=4000)
                            
                            if 'choices' in response and len(response['choices']) > 0:
                                improved_code = assistant._extract_code(response['choices'][0]['message']['content'])
                                st.code(improved_code, language=programming_language.lower())
                tab_index += 1
            
            # Complexity Analysis tab
            if do_complexity:
                with tab_objects[tab_index]:
                    st.markdown("### Complexity Analysis")
                    with st.spinner("Analyzing complexity..."):
                        complexity = assistant.analyze_complexity(user_code)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"""
                        #### Time Complexity
                        <div class="step-badge">{complexity['time_complexity']}</div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        #### Space Complexity
                        <div class="step-badge">{complexity['space_complexity']}</div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("#### Explanation")
                    st.markdown(f"""<div class="feedback-card">{complexity['explanation']}</div>""", unsafe_allow_html=True)
                    
                    # Optimization suggestions
                    with st.expander("Optimization Suggestions", expanded=False):
                        with st.spinner("Generating optimization tips..."):
                            system_prompt = """
                            You are an algorithm optimization expert. Given some code and its complexity analysis:
                            1. Identify specific areas where the code could be optimized
                            2. Suggest concrete changes to improve time and/or space complexity
                            3. Explain the theoretical impact of each suggestion on the overall complexity
                            4. If possible, suggest alternative algorithms or data structures
                            
                            Format your response with clear sections and bullet points.
                            """
                            
                            messages = [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Code:\n{user_code}\n\nCurrent complexity analysis:\nTime: {complexity['time_complexity']}\nSpace: {complexity['space_complexity']}\n\nPlease suggest optimizations."}
                            ]
                            
                            response = assistant._send_request(assistant.mixtral, messages, temperature=0.3, max_tokens=2000)
                            
                            if 'choices' in response and len(response['choices']) > 0:
                                optimization_tips = response['choices'][0]['message']['content']
                                st.markdown(optimization_tips)
                tab_index += 1
            
            # Visualization tab - always included
            with tab_objects[tab_index]:
                st.markdown("### Code Visualization")
                with st.spinner("Generating visualization..."):
                    mermaid_code = assistant.generate_solution_flowchart(f"Visualize this code:\n\n{user_code}")
                
                st.markdown("#### Code Structure Diagram")
                render_mermaid(mermaid_code)
                
                with st.expander("View Mermaid Code"):
                    st.code(mermaid_code, language="mermaid")
                
                # Additional visualization options
                with st.expander("Code Structure Explanation", expanded=False):
                    with st.spinner("Generating structure explanation..."):
                        system_prompt = """
                        You are a code structure analyst. Based on the provided code:
                        1. Explain the high-level architecture and structure
                        2. Break down how the different components interact
                        3. Identify the core design patterns or approaches used
                        4. Explain the data flow through the code
                        
                        Focus on structure rather than implementation details.
                        """
                        
                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Please analyze the structure of this {programming_language} code:\n\n{user_code}"}
                        ]
                        
                        response = assistant._send_request(assistant.mixtral, messages, temperature=0.3, max_tokens=2000)
                        
                        if 'choices' in response and len(response['choices']) > 0:
                            structure_explanation = response['choices'][0]['message']['content']
                            st.markdown(structure_explanation)
                tab_index += 1
            
            # Learning Path tab
            if do_learning:
                with tab_objects[tab_index]:
                    st.markdown("### Personalized Learning Path")
                    with st.spinner("Creating personalized learning recommendations..."):
                        try:
                            system_prompt = """
                            You are an educational coding mentor. Based on the user's code:
                            1. Identify the user's current skill level (beginner, intermediate, advanced)
                            2. Recommend 3-4 specific concepts or skills they should learn next
                            3. Suggest resources (documentation, tutorials) for each concept
                            4. Provide a small practice exercise for each concept
                            5. Be encouraging and supportive in your tone
                            """
                            
                            messages = [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Based on this {programming_language} code, create a personalized learning path:\n\n{user_code}"}
                            ]
                            
                            response = assistant._send_request(assistant.mixtral, messages, temperature=0.4, max_tokens=2000)
                            
                            if 'choices' in response and len(response['choices']) > 0:
                                learning_path = response['choices'][0]['message']['content']
                                st.markdown(f"""<div class="challenge-card">{learning_path}</div>""", unsafe_allow_html=True)
                            else:
                                st.warning("Could not generate learning recommendations. Please try again.")
                        except Exception as e:
                            st.error(f"Unable to generate learning recommendations: {str(e)}")
                    
                    # Additional practice problems
                    with st.expander("Practice Problems", expanded=False):
                        with st.spinner("Generating practice problems..."):
                            system_prompt = """
                            You are a programming educator. Based on the user's code skill level:
                            1. Create 3 progressively challenging practice problems
                            2. Each problem should build on skills demonstrated in their code
                            3. Provide clear problem statements with expected inputs/outputs
                            4. Include a hint for each problem (without giving away the solution)
                            5. Format these as numbered problems with clear sections
                            """
                            
                            messages = [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Based on this {programming_language} code, create practice problems:\n\n{user_code}"}
                            ]
                            
                            response = assistant._send_request(assistant.mixtral, messages, temperature=0.4, max_tokens=2000)
                            
                            if 'choices' in response and len(response['choices']) > 0:
                                practice_problems = response['choices'][0]['message']['content']
                                st.markdown(practice_problems)
                    
                    # If logged in, save the skills assessment
                    if st.session_state.user_id:
                        with st.spinner("Analyzing skills in your code..."):
                            # Analyze code to identify skills
                            skills_analysis = assistant.skill_analyzer.analyze_code(user_code, programming_language)
                            
                            if skills_analysis and 'skills' in skills_analysis:
                                st.markdown("### Skills Analysis")
                                
                                skills_data = skills_analysis['skills']
                                strengths = []
                                weaknesses = []
                                
                                for skill, score in skills_data.items():
                                    if score > 0.6:
                                        strengths.append((skill, score))
                                    elif score < 0.4:
                                        weaknesses.append((skill, score))
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("#### Strengths")
                                    for skill, score in sorted(strengths, key=lambda x: x[1], reverse=True):
                                        st.markdown(f"""
                                        <div class="skill-badge">{skill}: {score:.2f}</div>
                                        """, unsafe_allow_html=True)
                                
                                with col2:
                                    st.markdown("#### Areas for Improvement")
                                    for skill, score in sorted(weaknesses, key=lambda x: x[1]):
                                        st.markdown(f"""
                                        <div class="weak-badge">{skill}: {score:.2f}</div>
                                        """, unsafe_allow_html=True)
                                
                                # Option to save to profile
                                if st.button("Save Skills to Profile"):
                                    try:
                                        # Get skill IDs
                                        for skill, score in skills_data.items():
                                            # Check if skill exists
                                            cursor = db.conn.cursor()
                                            cursor.execute('SELECT skill_id FROM skills WHERE name = ?', (skill,))
                                            skill_result = cursor.fetchone()
                                            
                                            if not skill_result:
                                                # Create new skill
                                                cursor.execute('INSERT INTO skills (name, category) VALUES (?, ?)', 
                                                             (skill, "code_review"))
                                                db.conn.commit()
                                                cursor.execute('SELECT skill_id FROM skills WHERE name = ?', (skill,))
                                                skill_result = cursor.fetchone()
                                            
                                            skill_id = skill_result[0]
                                            
                                            # Update user skill
                                            cursor.execute("""
                                                INSERT OR REPLACE INTO user_skills 
                                                (user_id, skill_id, proficiency, last_updated) 
                                                VALUES (?, ?, ?, ?)
                                            """, (st.session_state.user_id, skill_id, score, 
                                                 "datetime('now')"))
                                        
                                        db.conn.commit()
                                        st.success("Skills saved to your profile!")
                                    except Exception as e:
                                        st.error(f"Error saving skills: {str(e)}")