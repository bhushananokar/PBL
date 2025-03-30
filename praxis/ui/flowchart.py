# praxis/ui/flowchart.py
import streamlit as st
import re
import time
from typing import Callable
from streamlit_ace import st_ace

from utils.visualization import render_mermaid

def render_flowchart_page(db, assistant, reset_app: Callable, go_to_page: Callable) -> None:
    """
    Render the flowchart page where users can view the solution approach visually.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        reset_app: Function to reset the app state
        go_to_page: Function to navigate to a different page
    """
    st.markdown("<div class='step-badge'>VISUAL GUIDE STEP</div>", unsafe_allow_html=True)
    
    # Show challenge in expander
    with st.expander("Show Challenge", expanded=False):
        st.markdown(f"""
        <div class="challenge-card">
        {st.session_state.challenge}
        </div>
        """, unsafe_allow_html=True)
    
    # Show previous feedback in expander
    if st.session_state.feedback:
        with st.expander("Show Previous Feedback", expanded=False):
            st.markdown(f"""
            <div class="feedback-card">
            {st.session_state.feedback}
            </div>
            """, unsafe_allow_html=True)
    
    # Show flowchart
    st.markdown("### Solution Approach Flowchart")
    st.markdown("""
    <div class="flowchart-card">
    <p>Follow this visual guide to implement your solution:</p>
    </div>
    """, unsafe_allow_html=True)
    
    render_mermaid(st.session_state.flowchart)
    
    # Get programming language
    lang_match = re.search(r"Create code in (\w+)", st.session_state.problem_desc)
    lang = lang_match.group(1).lower() if lang_match else "python"
    
    st.markdown("### Your Implementation")
    
    # Code editor with previous attempt
    final_code = st_ace(
        language=lang,
        theme="monokai",
        height=300,
        value=st.session_state.user_code,
        key="final_code_editor"
    )
    
    # Buttons for this page
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        analyze_code = st.button("Analyze Code", type="primary")
    
    with col2:
        get_hint = st.button("Get a Hint")
    
    with col3:
        go_to_feedback = st.button("View Previous Feedback")
    
    with col4:
        show_solution = st.button("View Solution")
    
    if analyze_code:
        handle_analyze_code(db, assistant, final_code, lang)
    
    if get_hint:
        handle_get_hint(assistant, final_code)
    
    if go_to_feedback:
        # Update user code
        st.session_state.user_code = final_code
        go_to_page("feedback")
    
    if show_solution:
        handle_view_solution(db, assistant, final_code, lang, go_to_page)
    
    # Navigation row
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Go Back to Challenge"):
            # Update user code
            st.session_state.user_code = final_code
            go_to_page("challenge")
    
    with col2:
        if st.button("Submit & Continue"):
            # Update user code
            st.session_state.user_code = final_code
            go_to_page("solution")
    
    with col3:
        if st.button("Reset / Start New Problem"):
            reset_app()

def handle_analyze_code(db, assistant, final_code: str, lang: str) -> None:
    """
    Handle the "Analyze Code" button action.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        final_code: The user's implementation code
        lang: Programming language
    """
    if not final_code or final_code.strip() == "":
        st.error("Please write some code before analyzing.")
    else:
        with st.spinner("Analyzing your implementation..."):
            # Update user code
            st.session_state.user_code = final_code
            
            # Generate new feedback
            feedback = assistant.analyze_user_attempt(
                st.session_state.enhanced_prompt,
                final_code
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
                    score = assistant.score_user_attempt(final_code, solution, lang)
                    
                    # Check if successful
                    successful = score > 0.8
                    
                    # Store attempt in database
                    db.store_attempt(
                        st.session_state.user_id,
                        st.session_state.challenge_id,
                        final_code,
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
            
            # Show feedback here
            st.markdown("### Analysis Results")
            st.markdown(f"""
            <div class="feedback-card">
            {st.session_state.feedback}
            </div>
            """, unsafe_allow_html=True)

def handle_get_hint(assistant, final_code: str) -> None:
    """
    Handle the "Get a Hint" button action.
    
    Args:
        assistant: The LLM assistant
        final_code: The user's implementation code
    """
    with st.spinner("Generating a helpful hint..."):
        system_prompt = """
        You are a coding mentor. The student is working on this programming problem:
        
        {enhanced_prompt}
        
        They are looking at a flowchart that shows the solution approach and trying to implement it.
        Provide a specific hint that connects the flowchart concepts to code implementation.
        Keep it short and practical, focusing on translating the visual approach to actual code.
        """
        
        messages = [
            {"role": "system", "content": system_prompt.format(enhanced_prompt=st.session_state.enhanced_prompt)},
            {"role": "user", "content": f"My current code:\n{final_code}\n\nCan you give me a hint on how to implement the solution based on the flowchart?"}
        ]
        
        response = assistant._send_request(assistant.mixtral, messages, temperature=0.4, max_tokens=200)
        
        if 'choices' in response and len(response['choices']) > 0:
            hint = response['choices'][0]['message']['content']
            
            st.markdown("### Implementation Hint")
            st.info(hint)

def handle_view_solution(db, assistant, final_code: str, lang: str, go_to_page: Callable) -> None:
    """
    Handle the "View Solution" button action.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        final_code: The user's implementation code
        lang: Programming language
        go_to_page: Function to navigate to a different page
    """
    with st.spinner("Generating complete solution..."):
        # Update user code
        st.session_state.user_code = final_code
        
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
            # Generate solution if not already done
            if not st.session_state.solution:
                solution = assistant.generate_code(st.session_state.enhanced_prompt)
                st.session_state.solution = solution
        
        # Show solution
        st.markdown("### Complete Solution")
        st.code(st.session_state.solution, language=lang)
        
        # Option to go to solution page for more details
        if st.button("View Detailed Solution"):
            go_to_page("solution")