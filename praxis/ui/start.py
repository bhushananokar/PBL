# praxis/ui/start.py
import streamlit as st
from typing import Callable

def render_start_page(db, assistant, go_to_page: Callable) -> None:
    """
    Render the start page for beginning a new coding challenge.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        go_to_page: Function to navigate to a different page
    """
    st.title("Coding Learning Path")
    
    st.markdown(
        """
        <div class="challenge-card">
        <h3>Learn By Doing</h3>
        <p>Describe a coding problem or function you want to implement. We'll guide you through the learning process step by step, encouraging you to solve it yourself before revealing the solution.</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    programming_language = st.selectbox(
        "Programming Language",
        ["Python", "JavaScript", "Java", "C++", "C#", "Go", "Ruby", "PHP", "TypeScript", "Rust", "Swift", "Kotlin"]
    )
    
    problem_description = st.text_area(
        "Describe the coding problem or function you want to implement:",
        height=150,
        placeholder="E.g., Create a function that finds the longest palindromic substring in a given string."
    )
    
    if st.button("Start Learning", type="primary"):
        if not problem_description:
            st.error("Please describe a coding problem first.")
        else:
            with st.spinner("Preparing your learning challenge..."):
                # Build full description
                full_desc = f"Create code in {programming_language} that: {problem_description}"
                
                # Enhance the prompt
                enhanced_prompt = assistant.enhance_prompt(full_desc)
                
                # Generate challenge
                challenge = assistant.generate_learning_challenge(enhanced_prompt)
                
                # If user is logged in, store the challenge in the database
                if st.session_state.user_id:
                    # Store challenge
                    st.session_state.challenge_id = db.store_challenge(full_desc, enhanced_prompt, programming_language)
                    
                    # Identify skills for this challenge
                    skills = assistant.identify_challenge_skills(enhanced_prompt)
                    if skills:
                        db.map_challenge_skills(st.session_state.challenge_id, skills)
                    
                    # Initialize attempt counter and timer
                    st.session_state.attempt_number = 1
                    st.session_state.start_time = None
                
                # Store in session state
                st.session_state.problem_desc = full_desc
                st.session_state.enhanced_prompt = enhanced_prompt
                st.session_state.challenge = challenge
                
                # Go to challenge page
                go_to_page("challenge")