# praxis/ui/solution.py
import streamlit as st
import re
from typing import Callable

from praxis.utils.visualization import render_mermaid

def render_solution_page(db, assistant, reset_app: Callable, go_to_page: Callable) -> None:
    """
    Render the solution page with detailed explanations and analysis.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        reset_app: Function to reset the app state
        go_to_page: Function to navigate to a different page
    """
    st.markdown("<div class='step-badge'>SOLUTION STEP</div>", unsafe_allow_html=True)
    
    # Show challenge in expander
    with st.expander("Show Challenge", expanded=False):
        st.markdown(f"""
        <div class="challenge-card">
        {st.session_state.challenge}
        </div>
        """, unsafe_allow_html=True)
    
    # Show flowchart in expander
    with st.expander("Show Solution Flowchart", expanded=False):
        render_mermaid(st.session_state.flowchart)
    
    # Show user's final attempt in expander
    with st.expander("Show Your Final Attempt", expanded=False):
        # Get programming language
        lang_match = re.search(r"Create code in (\w+)", st.session_state.problem_desc)
        lang = lang_match.group(1).lower() if lang_match else "python"
        
        st.code(st.session_state.user_code, language=lang)
    
    # Show solution
    st.markdown("### Complete Solution")
    st.markdown("""
    <div class="solution-card">
    <p>Here's a complete solution with detailed explanations:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get programming language
    lang_match = re.search(r"Create code in (\w+)", st.session_state.problem_desc)
    lang = lang_match.group(1).lower() if lang_match else "python"
    
    # Make sure we have a solution
    if not st.session_state.solution:
        # Check database first
        if st.session_state.user_id and st.session_state.challenge_id:
            cursor = db.conn.cursor()
            cursor.execute('SELECT solution FROM challenges WHERE challenge_id = ?', (st.session_state.challenge_id,))
            solution_result = cursor.fetchone()
            
            if solution_result and solution_result[0]:
                st.session_state.solution = solution_result[0]
            else:
                with st.spinner("Generating solution..."):
                    # Generate solution
                    solution = assistant.generate_code(st.session_state.enhanced_prompt)
                    st.session_state.solution = solution
                    
                    # Store solution in database
                    db.update_challenge_solution(st.session_state.challenge_id, solution)
        else:
            with st.spinner("Generating solution..."):
                solution = assistant.generate_code(st.session_state.enhanced_prompt)
                st.session_state.solution = solution
    
    st.code(st.session_state.solution, language=lang)
    
    # Add explanation if needed
    with st.expander("Solution Explanation", expanded=True):
        with st.spinner("Generating explanation..."):
            if "solution_explanation" not in st.session_state:
                system_prompt = """
                You are an expert programming educator. Provide a clear, concise explanation of the provided solution code.
                Focus on:
                1. The key algorithms and data structures used
                2. Why these were chosen for this problem
                3. How the different parts of the code work together
                4. Any tricks, optimizations, or clever approaches used
                5. Potential edge cases and how they're handled
                
                Keep your explanation educational and detailed, but avoid being overly verbose.
                """
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Problem: {st.session_state.enhanced_prompt}\n\nSolution Code:\n{st.session_state.solution}\n\nPlease explain this solution."}
                ]
                
                response = assistant._send_request(assistant.mixtral, messages, temperature=0.3, max_tokens=2000)
                
                if 'choices' in response and len(response['choices']) > 0:
                    explanation = response['choices'][0]['message']['content']
                    st.session_state.solution_explanation = explanation
                else:
                    st.session_state.solution_explanation = "Could not generate explanation."
            
            st.markdown(st.session_state.solution_explanation)
    
    # Analysis tabs
    st.markdown("### Solution Analysis")
    tab1, tab2, tab3 = st.tabs(["Complexity Analysis", "Learning Points", "Next Steps"])
    
    with tab1:
        st.markdown("### Code Complexity Analysis")
        with st.spinner("Analyzing complexity..."):
            if "complexity_analysis" not in st.session_state:
                try:
                    complexity = assistant.analyze_complexity(st.session_state.solution)
                    st.session_state.complexity_analysis = complexity
                except Exception as e:
                    st.session_state.complexity_analysis = {
                        "time_complexity": "Analysis failed",
                        "space_complexity": "Analysis failed",
                        "explanation": f"Could not analyze complexity: {str(e)}"
                    }
            
            complexity = st.session_state.complexity_analysis
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
    
    with tab2:
        st.markdown("### Key Learning Points")
        with st.spinner("Generating learning summary..."):
            if "learning_points" not in st.session_state:
                try:
                    system_prompt = """
                    You are an educational coding mentor. Based on the solution code provided:
                    1. Identify 3-5 key learning points from this exercise
                    2. Explain important concepts demonstrated in the solution
                    3. Highlight best practices or patterns used
                    4. Suggest what concepts to study next to build on this knowledge
                    """
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Problem: {st.session_state.enhanced_prompt}\n\nSolution Code:\n{st.session_state.solution}\n\nWhat are the key learning points from this exercise?"}
                    ]
                    
                    response = assistant._send_request(assistant.mixtral, messages, temperature=0.3, max_tokens=2000)
                    
                    if 'choices' in response and len(response['choices']) > 0:
                        learning_points = response['choices'][0]['message']['content']
                        st.session_state.learning_points = learning_points
                    else:
                        st.session_state.learning_points = "Could not generate learning points."
                except Exception as e:
                    st.session_state.learning_points = f"Unable to generate learning points: {str(e)}"
            
            st.markdown(f"""<div class="feedback-card">{st.session_state.learning_points}</div>""", unsafe_allow_html=True)
    
    with tab3:
        st.markdown("### Next Steps")
        with st.spinner("Generating next steps..."):
            if "next_steps" not in st.session_state:
                try:
                    system_prompt = """
                    You are an educational coding mentor. Based on this problem and solution:
                    1. Suggest 3-4 related problems that would build on what the student learned
                    2. For each problem, provide a short description and why it's valuable
                    3. Identify what concepts or techniques they should study next
                    4. Recommend specific resources (documentation, tutorials) they might find helpful
                    5. Suggest 1-2 ways to extend or optimize the current solution for practice
                    """
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Problem: {st.session_state.enhanced_prompt}\n\nSolution Code:\n{st.session_state.solution}\n\nWhat should I learn or practice next?"}
                    ]
                    
                    response = assistant._send_request(assistant.mixtral, messages, temperature=0.4, max_tokens=2000)
                    
                    if 'choices' in response and len(response['choices']) > 0:
                        next_steps = response['choices'][0]['message']['content']
                        st.session_state.next_steps = next_steps
                    else:
                        st.session_state.next_steps = "Could not generate next steps."
                except Exception as e:
                    st.session_state.next_steps = f"Unable to generate next steps: {str(e)}"
            
            st.markdown(f"""<div class="challenge-card">{st.session_state.next_steps}</div>""", unsafe_allow_html=True)
    
    # Compare your solution
    if st.session_state.user_code:
        with st.expander("Compare Your Solution", expanded=False):
            st.markdown("### Solution Comparison")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Your Solution")
                st.code(st.session_state.user_code, language=lang)
            
            with col2:
                st.markdown("#### Model Solution")
                st.code(st.session_state.solution, language=lang)
            
            # Generate comparison
            if "solution_comparison" not in st.session_state:
                with st.spinner("Comparing solutions..."):
                    system_prompt = """
                    You are an expert programming educator. Compare the user's solution with the model solution and highlight:
                    1. Key similarities and differences in approach
                    2. Strengths of the user's solution
                    3. Areas where the model solution might be more efficient or clear
                    4. Any creative approaches in the user's solution
                    
                    Be supportive and constructive. Focus on learning, not criticism.
                    """
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Problem: {st.session_state.enhanced_prompt}\n\nUser Solution:\n{st.session_state.user_code}\n\nModel Solution:\n{st.session_state.solution}\n\nPlease compare these solutions."}
                    ]
                    
                    response = assistant._send_request(assistant.mixtral, messages, temperature=0.3, max_tokens=2000)
                    
                    if 'choices' in response and len(response['choices']) > 0:
                        comparison = response['choices'][0]['message']['content']
                        st.session_state.solution_comparison = comparison
                    else:
                        st.session_state.solution_comparison = "Could not generate comparison."
            
            st.markdown(f"""<div class="feedback-card">{st.session_state.solution_comparison}</div>""", unsafe_allow_html=True)
    
    # If registered user, mark challenge as completed if high score
    if st.session_state.user_id and st.session_state.challenge_id:
        # Get best score
        cursor = db.conn.cursor()
        cursor.execute('''
            SELECT MAX(score) FROM attempts 
            WHERE user_id = ? AND challenge_id = ?
        ''', (st.session_state.user_id, st.session_state.challenge_id))
        
        result = cursor.fetchone()
        best_score = result[0] if result and result[0] is not None else 0
        
        if best_score > 0.8:
            # Mark as successful if high score
            cursor.execute('''
                UPDATE attempts 
                SET successful = 1 
                WHERE user_id = ? AND challenge_id = ? AND score = ?
            ''', (st.session_state.user_id, st.session_state.challenge_id, best_score))
            db.conn.commit()
            
            st.success(f"Challenge completed with score: {best_score * 100:.1f}%")
    
    # Navigation buttons
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Try Another Problem", type="primary"):
            reset_app()
    
    with col2:
        if st.button("Go Back to Your Code"):
            go_to_page("challenge")