# praxis/ui/feedback.py
import streamlit as st
import re
import time
from typing import Callable
from streamlit_ace import st_ace

from utils.visualization import render_mermaid

def render_feedback_page(db, assistant, reset_app: Callable, go_to_page: Callable) -> None:
    """
    Render the feedback page where users can revise their solution.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        reset_app: Function to reset the app state
        go_to_page: Function to navigate to a different page
    """
    st.markdown("<div class='step-badge'>FEEDBACK STEP</div>", unsafe_allow_html=True)
    
    # Show challenge in expander
    with st.expander("Show Challenge", expanded=False):
        st.markdown(f"""
        <div class="challenge-card">
        {st.session_state.challenge}
        </div>
        """, unsafe_allow_html=True)
    
    # Show feedback
    st.markdown("### Code Feedback")
    st.markdown(f"""
    <div class="feedback-card">
    {st.session_state.feedback}
    </div>
    """, unsafe_allow_html=True)
    
    # Get programming language
    lang_match = re.search(r"Create code in (\w+)", st.session_state.problem_desc)
    lang = lang_match.group(1).lower() if lang_match else "python"
    
    st.markdown("### Revise Your Solution")
    
    # Code editor with previous attempt
    revised_code = st_ace(
        language=lang,
        theme="monokai",
        height=300,
        value=st.session_state.user_code,
        key="revised_code_editor"
    )
    
    # First row of buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        submit_revised = st.button("Analyze Revision", type="primary")
    
    with col2:
        get_hint = st.button("Get a Hint")
    
    with col3:
        more_help = st.button("Show Flowchart")
    
    with col4:
        skip_to_solution = st.button("View Solution")
    
    # Handle the button actions
    if submit_revised:
        handle_submit_revised(db, assistant, revised_code, lang)
    
    if get_hint:
        handle_get_hint(assistant, revised_code)
    
    if more_help:
        handle_show_flowchart(assistant, revised_code, go_to_page)
    
    if skip_to_solution:
        handle_view_solution(db, assistant, revised_code, lang, go_to_page)
    
    # Second row of actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Continue Learning"):
            # Update user code
            st.session_state.user_code = revised_code
            go_to_page("flowchart")
    
    with col2:
        if st.button("Go Back to Challenge"):
            # Update user code
            st.session_state.user_code = revised_code
            go_to_page("challenge")
    
    with col3:
        if st.button("Reset / Start New Problem"):
            reset_app()

def handle_submit_revised(db, assistant, revised_code: str, lang: str) -> None:
    """
    Handle the "Analyze Revision" button action.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        revised_code: The user's revised code
        lang: Programming language
    """
    if not revised_code or revised_code.strip() == "":
        st.error("Please update your code before submitting.")
    else:
        with st.spinner("Analyzing your revised code..."):
            # Update user code
            st.session_state.user_code = revised_code
            
            # Generate new feedback
            feedback = assistant.analyze_user_attempt(
                st.session_state.enhanced_prompt,
                revised_code
            )
            st.session_state.feedback = feedback
            
            # If user is logged in, store the attempt
            if st.session_state.user_id and st.session_state.challenge_id:
                # Track time spent
                time_spent = int(time.time() - st.session_state.start_time) if st.session_state.start_time else 0
                
                # Get or generate solution
                cursor = db.conn.cursor()
                cursor.execute('SELECT solution FROM challenges WHERE challenge_id = ?', (st.session_state.challenge_id,))
                solution_result = cursor.fetchone()
                
                solution = None
                if solution_result and solution_result[0]:
                    solution = solution_result[0]
                else:
                    # Generate solution
                    solution = assistant.generate_code(st.session_state.enhanced_prompt)
                    # Store solution in database
                    db.update_challenge_solution(st.session_state.challenge_id, solution)
                
                # Score the attempt
                if solution:
                    score = assistant.score_user_attempt(revised_code, solution, lang)
                    
                    # Check if successful
                    successful = score > 0.8
                    
                    # Store attempt in database
                    db.store_attempt(
                        st.session_state.user_id,
                        st.session_state.challenge_id,
                        revised_code,
                        feedback,
                        score,
                        time_spent,
                        st.session_state.attempt_number,
                        successful
                    )
                    
                    # Update user skills
                    db.update_user_skills(st.session_state.user_id, st.session_state.challenge_id, score)
                    
                    # Increment attempt counter
                    st.session_state.attempt_number += 1
                    
                    # Reset timer
                    st.session_state.start_time = time.time()
            
            # Stay on feedback page but update content
            st.success("Feedback updated!")
            st.markdown("### Updated Analysis")
            st.markdown(f"""
            <div class="feedback-card">
            {feedback}
            </div>
            """, unsafe_allow_html=True)

def handle_get_hint(assistant, revised_code: str) -> None:
    """
    Handle the "Get a Hint" button action.
    
    Args:
        assistant: The LLM assistant
        revised_code: The user's revised code
    """
    with st.spinner("Generating a helpful hint..."):
        system_prompt = """
        You are a coding mentor. The student is working on this programming problem:
        
        {enhanced_prompt}
        
        They have already attempted a solution and received feedback. Based on this, provide ONE short, clear hint 
        that will help them improve their solution. Keep it to 2-3 sentences maximum and focus on addressing 
        a specific issue in their current approach.
        """
        
        messages = [
            {"role": "system", "content": system_prompt.format(enhanced_prompt=st.session_state.enhanced_prompt)},
            {"role": "user", "content": f"My code:\n{revised_code}\n\nFeedback I got:\n{st.session_state.feedback}\n\nCan you give me a targeted hint?"}
        ]
        
        response = assistant._send_request(assistant.mixtral, messages, temperature=0.4, max_tokens=200)
        
        if 'choices' in response and len(response['choices']) > 0:
            hint = response['choices'][0]['message']['content']
            
            st.markdown("### Hint")
            st.info(hint)

def handle_show_flowchart(assistant, revised_code: str, go_to_page: Callable) -> None:
    """
    Handle the "Show Flowchart" button action.
    
    Args:
        assistant: The LLM assistant
        revised_code: The user's revised code
        go_to_page: Function to navigate to a different page
    """
    with st.spinner("Generating visual approach..."):
        # Create flowchart if not already done
        if not st.session_state.flowchart:
            flowchart = assistant.generate_solution_flowchart(st.session_state.enhanced_prompt)
            st.session_state.flowchart = flowchart
            
        # Show flowchart directly
        st.markdown("### Solution Approach Flowchart")
        render_mermaid(st.session_state.flowchart)
        
        # Option to go to flowchart page
        if st.button("Go to Flowchart View"):
            # Update user code first
            st.session_state.user_code = revised_code
            go_to_page("flowchart")

def handle_view_solution(db, assistant, revised_code: str, lang: str, go_to_page: Callable) -> None:
    """
    Handle the "View Solution" button action.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        revised_code: The user's revised code
        lang: Programming language
        go_to_page: Function to navigate to a different page
    """
    with st.spinner("Generating complete solution..."):
        # Update user code
        st.session_state.user_code = revised_code
        
        # Create flowchart if not already done
        if not st.session_state.flowchart:
            flowchart = assistant.generate_solution_flowchart(st.session_state.enhanced_prompt)
            st.session_state.flowchart = flowchart
        
        # Check for solution in database first
        if st.session_state.user_id and st.session_state.challenge_id:
            cursor = db.conn.cursor()
            cursor.execute('SELECT solution FROM challenges WHERE challenge_id = ?', (st.session_state.challenge_id,))
            solution_result = cursor.fetchone()
            
            if solution_result and solution_result[0]:
                st.session_state.solution = solution_result[0]
            else:
                # Generate solution
                solution = assistant.generate_code(st.session_state.enhanced_prompt)
                st.session_state.solution = solution
                
                # Store solution in database
                db.update_challenge_solution(st.session_state.challenge_id, solution)
        else:
            # Generate solution
            if not st.session_state.solution:
                solution = assistant.generate_code(st.session_state.enhanced_prompt)
                st.session_state.solution = solution
        
        # Show solution
        st.markdown("### Complete Solution")
        st.code(st.session_state.solution, language=lang)
        
        # Option to go to solution page for more details
        if st.button("View Detailed Solution"):
            go_to_page("solution")