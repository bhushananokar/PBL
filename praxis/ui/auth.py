# praxis/ui/auth.py
import streamlit as st
from typing import Tuple, Callable

def render_login_register(db, go_to_page: Callable[[str], None]) -> None:
    """
    Render the login and registration pages.
    
    Args:
        db: Database connection
        go_to_page: Function to navigate to a different page
    """
    st.title("Welcome to Code Learning Assistant")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        render_login_tab(db, go_to_page)
    
    with tab2:
        render_register_tab(db, go_to_page)
    
    # Introduction section for new users
    st.markdown("---")
    st.markdown("""
    ### Enhance Your Coding Skills with AI-Guided Learning
    
    **Features:**
    - 📊 Track your progress and skill development over time
    - 🎯 Get personalized challenge recommendations based on your skill gaps
    - 💡 Receive detailed feedback on your code with specific improvement suggestions
    - 📈 Visual skill analytics to identify strengths and weaknesses
    - 🧠 Customized learning paths that adapt to your progress
    
    Create an account to start tracking your progress and get personalized recommendations!
    """)

def render_login_tab(db, go_to_page: Callable[[str], None]) -> None:
    """
    Render the login tab.
    
    Args:
        db: Database connection
        go_to_page: Function to navigate to a different page
    """
    st.markdown("### Login to Your Account")
    login_username = st.text_input("Username", key="login_username")
    login_password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login", key="login_button"):
        if login_user(db, login_username, login_password):
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password")

def render_register_tab(db, go_to_page: Callable[[str], None]) -> None:
    """
    Render the registration tab.
    
    Args:
        db: Database connection
        go_to_page: Function to navigate to a different page
    """
    st.markdown("### Create an Account")
    reg_username = st.text_input("Username", key="reg_username")
    reg_email = st.text_input("Email (optional)", key="reg_email")
    reg_password = st.text_input("Password", type="password", key="reg_password")
    reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
    
    if st.button("Register", key="register_button"):
        if not reg_username or not reg_password:
            st.error("Username and password are required")
        elif reg_password != reg_confirm:
            st.error("Passwords do not match")
        else:
            if register_user(db, reg_username, reg_password, reg_email):
                st.success("Registration successful! You are now logged in.")
                st.rerun()
            else:
                st.error("Username or email already exists")

def login_user(db, username: str, password: str) -> bool:
    """
    Authenticate a user and store session information.
    
    Args:
        db: Database connection
        username: Username to authenticate
        password: Password to authenticate
    
    Returns:
        bool: True if login successful, False otherwise
    """
    if not db:
        st.error("Database not initialized")
        return False
    
    user_id = db.authenticate_user(username, password)
    if user_id:
        st.session_state.user_id = user_id
        st.session_state.username = username
        st.session_state.page = "dashboard"
        return True
    
    return False

def register_user(db, username: str, password: str, email: str = None) -> bool:
    """
    Create a new user and store session information.
    
    Args:
        db: Database connection
        username: New username
        password: New password
        email: Email for the user (optional)
    
    Returns:
        bool: True if registration successful, False otherwise
    """
    if not db:
        st.error("Database not initialized")
        return False
    
    user_id = db.create_user(username, password, email)
    if user_id:
        st.session_state.user_id = user_id
        st.session_state.username = username
        st.session_state.page = "dashboard"
        return True
    
    return False

def logout_user() -> None:
    """
    Log out the current user by clearing session state.
    """
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.page = "start"

def render_sidebar_auth(db) -> None:
    """
    Render the authentication section in the sidebar.
    
    Args:
        db: Database connection
    """
    if st.session_state.user_id:
        st.sidebar.markdown(f"### Welcome, {st.session_state.username}!")
        
        if st.sidebar.button("Logout"):
            logout_user()
            st.rerun()