# praxis/ui/challenge.py
import streamlit as st
import time
import re
from typing import Callable
from streamlit_ace import st_ace

from utils.visualization import render_mermaid

# Function implementations for handling button actions
def handle_analyze_code(db, assistant, user_code: str, lang: str, go_to_page: Callable) -> None:
    """
    Handle the "Analyze My Code" button action.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        user_code: The user's code attempt
        lang: Programming language
        go_to_page: Function to navigate to a different page
    """
    if not user_code or user_code.strip() == "":
        st.error("Please write some code before analyzing.")
    else:
        with st.spinner("Analyzing your code..."):
            # Generate feedback
            feedback = assistant.analyze_user_attempt(
                st.session_state.enhanced_prompt, 
                user_code
            )
            st.session_state.feedback = feedback
            
            # If user is logged in, analyze and store the attempt
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
                    score = assistant.score_user_attempt(user_code, solution, lang)
                    
                    # Check if successful
                    successful = score > 0.8
                    
                    # Store attempt in database
                    db.store_attempt(
                        st.session_state.user_id,
                        st.session_state.challenge_id,
                        user_code,
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
            
            # Show feedback here directly
            st.markdown("### Analysis Results")
            st.markdown(f"""
            <div class="feedback-card">
            {st.session_state.feedback}
            </div>
            """, unsafe_allow_html=True)
            
            # Add a button to move to feedback page for more options
            if st.button("Revise Solution"):
                go_to_page("feedback")

def handle_get_hint(assistant) -> None:
    """
    Handle the "Get a Hint" button action.
    
    Args:
        assistant: The LLM assistant
    """
    with st.spinner("Generating a helpful hint..."):
        system_prompt = """
        You are a coding mentor. The student is working on this programming problem:
        
        {enhanced_prompt}
        
        Provide ONE short, clear hint that will help them make progress without giving away the full solution.
        Keep it to 2-3 sentences maximum. Focus on a conceptual insight or a direction they could explore.
        """
        
        messages = [
            {"role": "system", "content": system_prompt.format(enhanced_prompt=st.session_state.enhanced_prompt)},
            {"role": "user", "content": "I'm stuck. Can you give me just one small hint?"}
        ]
        
        response = assistant._send_request(assistant.mixtral, messages, temperature=0.4, max_tokens=200)
        
        if 'choices' in response and len(response['choices']) > 0:
            hint = response['choices'][0]['message']['content']
            
            st.markdown("### Hint")
            st.info(hint)

def handle_show_flowchart(assistant, go_to_page: Callable) -> None:
    """
    Handle the "Show Flowchart" button action.
    
    Args:
        assistant: The LLM assistant
        go_to_page: Function to navigate to a different page
    """
    with st.spinner("Generating solution approach..."):
        # Create flowchart if not already done
        if not st.session_state.flowchart:
            flowchart = assistant.generate_solution_flowchart(st.session_state.enhanced_prompt)
            st.session_state.flowchart = flowchart
        
        # Show flowchart directly
        st.markdown("### Solution Approach Flowchart")
        st.markdown("""
        <div class="flowchart-card">
        <p>This flowchart outlines the approach to solve the problem:</p>
        </div>
        """, unsafe_allow_html=True)
        
        render_mermaid(st.session_state.flowchart)
        
        # Add a button to move to flowchart page for more options
        if st.button("Go to Flowchart View"):
            go_to_page("flowchart")

def handle_show_solution(db, assistant, lang: str, go_to_page: Callable) -> None:
    """
    Handle the "View Solution" button action.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        lang: Programming language
        go_to_page: Function to navigate to a different page
    """
    with st.spinner("Generating complete solution..."):
        # Check if solution exists in database
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
                if st.session_state.challenge_id:
                    db.update_challenge_solution(st.session_state.challenge_id, solution)
        else:
            # Generate solution if not already done
            if not st.session_state.solution:
                solution = assistant.generate_code(st.session_state.enhanced_prompt)
                st.session_state.solution = solution
        
        # Show solution directly
        st.markdown("### Complete Solution")
        st.code(st.session_state.solution, language=lang)
        
        # Add a button to move to solution page for more details
        if st.button("View Detailed Solution"):
            go_to_page("solution")

def handle_submit_continue(db, assistant, user_code: str, lang: str, go_to_page: Callable) -> None:
    """
    Handle the "Submit & Continue" button action.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        user_code: The user's code attempt
        lang: Programming language
        go_to_page: Function to navigate to a different page
    """
    if not user_code or user_code.strip() == "":
        st.error("Please write some code before submitting.")
    else:
        with st.spinner("Analyzing your code for feedback..."):
            # Save user code
            st.session_state.user_code = user_code
            
            # Generate feedback
            feedback = assistant.analyze_user_attempt(
                st.session_state.enhanced_prompt, 
                user_code
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
                    score = assistant.score_user_attempt(user_code, solution, lang)
                    
                    # Check if successful
                    successful = score > 0.8
                    
                    # Store attempt in database
                    db.store_attempt(
                        st.session_state.user_id,
                        st.session_state.challenge_id,
                        user_code,
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
            
            # Go to feedback page
            go_to_page("feedback")

def render_challenge_page(db, assistant, reset_app: Callable, go_to_page: Callable) -> None:
    """
    Render the challenge page where users can work on their coding solution.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        reset_app: Function to reset the app state
        go_to_page: Function to navigate to a different page
    """
    st.markdown("<div class='step-badge'>CHALLENGE STEP</div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="challenge-card">
    {st.session_state.challenge}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Your Code Attempt")
    
    # Get programming language from description
    lang_match = re.search(r"Create code in (\w+)", st.session_state.problem_desc)
    lang = lang_match.group(1).lower() if lang_match else "python"
    
    # Start the timer if not already started
    if not st.session_state.start_time:
        st.session_state.start_time = time.time()
    
    # Code editor
    user_code = st_ace(
        placeholder="Write your code here...",
        language=lang,
        theme="monokai",
        height=300,
        key="code_editor",
        value=st.session_state.user_code if st.session_state.user_code else ""
    )
    
    # Save current code to session state when typing
    if user_code:
        st.session_state.user_code = user_code
    
    # Create multiple columns for more options
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        analyze_code = st.button("Analyze My Code", type="primary")
    
    with col2:
        get_hint = st.button("Get a Hint")
    
    with col3:
        show_flowchart = st.button("Show Flowchart")
    
    with col4:
        show_solution = st.button("View Solution")
    
    # First row of actions
    if analyze_code:
        handle_analyze_code(db, assistant, user_code, lang, go_to_page)
    
    if get_hint:
        handle_get_hint(assistant)
    
    if show_flowchart:
        handle_show_flowchart(assistant, go_to_page)
    
    if show_solution:
        handle_show_solution(db, assistant, lang, go_to_page)
    
    # Second row of actions
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Submit & Continue"):
            handle_submit_continue(db, assistant, user_code, lang, go_to_page)
    
    with col2:
        if st.button("Reset / Start New Problem"):
            reset_app()

def handle_analyze_code(db, assistant, user_code: str, lang: str, go_to_page: Callable) -> None:
    """
    Handle the "Analyze My Code" button action.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        user_code: The user's code attempt
        lang: Programming language
        go_to_page: Function to navigate to a different page
    """
    if not user_code or user_code.strip() == "":
        st.error("Please write some code before analyzing.")
    else:
        with st.spinner("Analyzing your code..."):
            # Generate feedback
            feedback = assistant.analyze_user_attempt(
                st.session_state.enhanced_prompt, 
                user_code
            )
            st.session_state.feedback = feedback
            
            # If user is logged in, analyze and store the attempt
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
                    score = assistant.score_user_attempt(user_code, solution, lang)
                    
                    # Check if successful
                    successful = score > 0.8
                    
                    # Store attempt in database
                    db.store_attempt(
                        st.session_state.user_id,
                        st.session_state.challenge_id,
                        user_code,
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
            
            # Show feedback here directly
            st.markdown("### Analysis Results")
            st.markdown(f"""
            <div class="feedback-card">
            {st.session_state.feedback}
            </div>
            """, unsafe_allow_html=True)
            
            # Add a button to move to feedback page for more options
            if st.button("Revise Solution"):
                go_to_page("feedback")