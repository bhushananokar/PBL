# praxis/main.py
import os
import streamlit as st
import time
from typing import Callable

from config import APP_MODES
from database.db_manager import Database
from models.assistant import EducationalCodeAssistant
from ui.styles import apply_styles, show_logo, show_about, show_learning_approach
from ui.auth import render_login_register, render_sidebar_auth
from ui.dashboard import render_dashboard
from ui.challenge import render_challenge_page
from ui.feedback import render_feedback_page

def main():
    st.set_page_config(
        page_title="Praxis - AI Code Learning Assistant",
        page_icon="P",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    # Initialize session state
    initialize_session_state()
    
    # Apply custom CSS
    apply_styles()
    
    # Set page config
    
    
    # Initialize database connection
    db = Database()
    
    # Sidebar layout
    show_logo()
    
    # API Key input
    api_key = st.sidebar.text_input("Groq API Key", type="password")
    
    # User login/logout section in sidebar
    render_sidebar_auth(db)
    
    # Learning approach explanation
    show_learning_approach()
    
    # Navigation in sidebar for logged-in users
    if st.session_state.user_id:
        render_sidebar_navigation()
    
    # Mode selection
    app_mode = st.sidebar.selectbox(
        "Choose Mode",
        APP_MODES,
        key="app_mode_select",
        on_change=lambda: setattr(st.session_state, 'mode', st.session_state.app_mode_select)
    )
    
    # About section
    show_about()
    
    try:
        # Initialize the assistant if API key is provided
        if not api_key:
            st.warning("Please enter your Groq API key in the sidebar to continue.")
            st.markdown("""
            ### How to get a Groq API Key:
            1. Sign up at [groq.com](https://console.groq.com/signup)
            2. Navigate to API Keys in your account
            3. Create a new API key
            4. Paste it in the sidebar
            """)
            return
            
        # Initialize the assistant
        assistant = EducationalCodeAssistant(api_key=api_key, db=db)
        
        # Route to appropriate page based on session state
        route_to_page(db, assistant)
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.markdown(
            """
            #### Troubleshooting:
            - Make sure you've entered a valid Groq API key
            - Check your internet connection
            - Try a simpler code request
            - Verify that the Groq API service is available
            """
        )
    
    # Close database connection on app exit
    if db:
        db.close()

def initialize_session_state():
    """Initialize session state variables."""
    # Page navigation
    if "page" not in st.session_state:
        st.session_state.page = "start"
    
    # User authentication
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None
    
    # Challenge data
    if "problem_desc" not in st.session_state:
        st.session_state.problem_desc = ""
    if "enhanced_prompt" not in st.session_state:
        st.session_state.enhanced_prompt = ""
    if "challenge" not in st.session_state:
        st.session_state.challenge = ""
    if "user_code" not in st.session_state:
        st.session_state.user_code = ""
    if "feedback" not in st.session_state:
        st.session_state.feedback = ""
    if "flowchart" not in st.session_state:
        st.session_state.flowchart = ""
    if "solution" not in st.session_state:
        st.session_state.solution = ""
    if "mode" not in st.session_state:
        st.session_state.mode = "Learning Path"
    if "challenge_id" not in st.session_state:
        st.session_state.challenge_id = None
    if "attempt_number" not in st.session_state:
        st.session_state.attempt_number = 1
    if "start_time" not in st.session_state:
        st.session_state.start_time = None

def go_to_page(page_name: str) -> None:
    """Navigate to a specific page."""
    st.session_state.page = page_name

def reset_app() -> None:
    """Reset the app state for a new challenge."""
    # Clear all session state related to the problem
    st.session_state.problem_desc = ""
    st.session_state.enhanced_prompt = ""
    st.session_state.challenge = ""
    st.session_state.user_code = ""
    st.session_state.feedback = ""
    st.session_state.flowchart = ""
    st.session_state.solution = ""
    st.session_state.page = "dashboard" if st.session_state.user_id else "start"
    st.session_state.challenge_id = None
    st.session_state.attempt_number = 1
    st.session_state.start_time = None

def render_sidebar_navigation() -> None:
    """Render the navigation sidebar for logged-in users."""
    st.sidebar.markdown("### Navigation")
    
    if st.sidebar.button("Dashboard"):
        go_to_page("dashboard")
    
    if st.sidebar.button("My Skills Profile"):
        go_to_page("profile")
    
    if st.sidebar.button("Learning Paths"):
        go_to_page("paths")
    
    if st.sidebar.button("Challenge History"):
        go_to_page("history")
    
    if st.sidebar.button("Start New Challenge"):
        reset_app()
        go_to_page("start")

def route_to_page(db, assistant) -> None:
    """Route to the appropriate page based on the session state."""
    # Login/Registration pages
    if st.session_state.page == "start" and not st.session_state.user_id:
        from ui.auth import render_login_register
        render_login_register(db, go_to_page)
    
    # Dashboard for logged-in users
    elif st.session_state.page == "dashboard" and st.session_state.user_id:
        from ui.dashboard import render_dashboard
        render_dashboard(db, assistant, reset_app, go_to_page)
    
    # User profile page
    elif st.session_state.page == "profile" and st.session_state.user_id:
        from ui.profile import render_profile_page
        render_profile_page(db, assistant, go_to_page)
    
    # Learning paths page
    elif st.session_state.page == "paths" and st.session_state.user_id:
        from ui.paths import render_paths_page
        render_paths_page(db, assistant, go_to_page)
    
    # Challenge history page
    elif st.session_state.page == "history" and st.session_state.user_id:
        from ui.history import render_history_page
        render_history_page(db, assistant, go_to_page)
    
    # Challenge workflow pages
    elif st.session_state.mode == "Learning Path":
        if st.session_state.page == "challenge":
            from ui.challenge import render_challenge_page
            render_challenge_page(db, assistant, reset_app, go_to_page)
        elif st.session_state.page == "feedback":
            from ui.feedback import render_feedback_page
            render_feedback_page(db, assistant, reset_app, go_to_page)
        elif st.session_state.page == "flowchart":
            from ui.flowchart import render_flowchart_page
            render_flowchart_page(db, assistant, reset_app, go_to_page)
        elif st.session_state.page == "solution":
            from ui.solution import render_solution_page
            render_solution_page(db, assistant, reset_app, go_to_page)
        else:
            # Start page - Problem definition
            from ui.start import render_start_page
            render_start_page(db, assistant, go_to_page)
    
    # Code Review mode
    elif st.session_state.mode == "Code Review":  
        from ui.review import render_review_page
        render_review_page(db, assistant)
    
    # Analytics mode
    elif st.session_state.mode == "Analytics":
        if st.session_state.user_id:
            from ui.analytics import render_analytics_page
            render_analytics_page(db, assistant)
        else:
            st.warning("Please log in to access analytics features.")

if __name__ == "__main__":
    main()