# praxis/ui/history.py
import streamlit as st
from typing import Callable

def render_history_page(db, assistant, go_to_page: Callable) -> None:
    """
    Render the challenge history page.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        go_to_page: Function to navigate to a different page
    """
    st.title("Challenge History")
    
    # Get all attempted challenges
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT c.challenge_id, c.title, c.description, 
               MAX(a.score) as best_score, 
               COUNT(a.attempt_id) as attempts,
               MAX(a.successful) as completed,
               MAX(a.created_at) as last_attempt
        FROM attempts a
        JOIN challenges c ON a.challenge_id = c.challenge_id
        WHERE a.user_id = ?
        GROUP BY c.challenge_id
        ORDER BY last_attempt DESC
    """, (st.session_state.user_id,))
    
    history = cursor.fetchall()
    
    if not history:
        st.info("You haven't attempted any challenges yet!")
    else:
        # Summary stats
        total_challenges = len(history)
        completed_challenges = sum(1 for _, _, _, _, _, completed, _ in history if completed)
        avg_score = sum(score for _, _, _, score, _, _, _ in history if score is not None) / total_challenges if total_challenges > 0 else 0
        
        st.markdown("### Your Challenge Stats")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
            <div class="metric-value">{total_challenges}</div>
            <div class="metric-label">Total Challenges</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
            <div class="metric-value">{completed_challenges}</div>
            <div class="metric-label">Completed Challenges</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
            <div class="metric-value">{avg_score*100:.1f}%</div>
            <div class="metric-label">Average Score</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Challenge history
        st.markdown("### Challenge History")
        
        # Use tabs to organize by status
        tab1, tab2, tab3 = st.tabs(["All Challenges", "Completed", "In Progress"])
        
        with tab1:
            for challenge in history:
                challenge_id, title, description, best_score, attempts, completed, last_attempt = challenge
                
                status = "✅ Completed" if completed else "⏳ In Progress"
                score_display = f"{best_score * 100:.1f}%" if best_score is not None else "N/A"
                
                st.markdown(f"""
                <div class="challenge-card">
                <h4>{title}</h4>
                <p>Best Score: {score_display} | Attempts: {attempts} | Status: {status} | Last attempt: {last_attempt}</p>
                <p>{description[:100]}...</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("Resume", key=f"resume_{challenge_id}"):
                        resume_challenge(db, assistant, challenge_id, description, go_to_page)
        
        with tab2:
            completed_challenges = [c for c in history if c[5]]  # Check completed flag
            
            if not completed_challenges:
                st.info("You haven't completed any challenges yet!")
            else:
                for challenge in completed_challenges:
                    challenge_id, title, description, best_score, attempts, _, last_attempt = challenge
                    
                    score_display = f"{best_score * 100:.1f}%" if best_score is not None else "N/A"
                    
                    st.markdown(f"""
                    <div class="challenge-card">
                    <h4>{title} ✅</h4>
                    <p>Score: {score_display} | Attempts: {attempts} | Completed: {last_attempt}</p>
                    <p>{description[:100]}...</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        with tab3:
            in_progress = [c for c in history if not c[5]]  # Check not completed
            
            if not in_progress:
                st.info("No challenges in progress!")
            else:
                for challenge in in_progress:
                    challenge_id, title, description, best_score, attempts, _, last_attempt = challenge
                    
                    score_display = f"{best_score * 100:.1f}%" if best_score is not None else "N/A"
                    
                    st.markdown(f"""
                    <div class="challenge-card">
                    <h4>{title} ⏳</h4>
                    <p>Current Score: {score_display} | Attempts: {attempts} | Last attempt: {last_attempt}</p>
                    <p>{description[:100]}...</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Continue", key=f"continue_{challenge_id}"):
                        resume_challenge(db, assistant, challenge_id, description, go_to_page)
                        
def resume_challenge(db, assistant, challenge_id: str, description: str, go_to_page: Callable) -> None:
    """
    Resume a previously started challenge.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        challenge_id: ID of the challenge to resume
        description: Description of the challenge
        go_to_page: Function to navigate to a different page
    """
    st.session_state.challenge_id = challenge_id
    st.session_state.problem_desc = description
    
    # Retrieve challenge data
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT enhanced_prompt 
        FROM challenges 
        WHERE challenge_id = ?
    """, (challenge_id,))
    result = cursor.fetchone()
    
    if result:
        enhanced_prompt = result[0]
        st.session_state.enhanced_prompt = enhanced_prompt
        
        # Get the last attempt
        cursor.execute("""
            SELECT code, attempt_number 
            FROM attempts 
            WHERE user_id = ? AND challenge_id = ? 
            ORDER BY created_at DESC LIMIT 1
        """, (st.session_state.user_id, challenge_id))
        attempt_result = cursor.fetchone()
        
        if attempt_result:
            code, attempt_number = attempt_result
            st.session_state.user_code = code
            st.session_state.attempt_number = attempt_number + 1
        else:
            st.session_state.attempt_number = 1
            st.session_state.user_code = ""
        
        # Generate challenge text if needed
        if not st.session_state.challenge:
            st.session_state.challenge = assistant.generate_learning_challenge(enhanced_prompt)
        
        # Set starting point
        st.session_state.start_time = None  # Will be set in challenge page
        go_to_page("challenge")