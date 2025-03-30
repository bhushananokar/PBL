# praxis/ui/styles.py
import streamlit as st

def apply_styles() -> None:
    """
    Apply custom CSS styles to the Streamlit app.
    """
    st.markdown("""
    <style>
    .main {
        background-color: #1e1e2e;
        color: #cdd6f4;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #313244;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        font-weight: 600;
        color: #cdd6f4;
    }
    .stTabs [aria-selected="true"] {
        background-color: #89b4fa !important;
        color: #1e1e2e !important;
    }
    .stMarkdown {
        padding: 10px;
    }
    h1, h2, h3 {
        color: #89b4fa;
    }
    .challenge-card {
        background-color: #313244;
        color: #cdd6f4;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #f9e2af;
        margin: 15px 0;
    }
    .feedback-card {
        background-color: #313244;
        color: #cdd6f4;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #89b4fa;
        margin: 15px 0;
    }
    .flowchart-card {
        background-color: #313244;
        color: #cdd6f4;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #a6e3a1;
        margin: 15px 0;
    }
    .solution-card {
        background-color: #313244;
        color: #cdd6f4;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #fab387;
        margin: 15px 0;
    }
    .analytics-card {
        background-color: #313244;
        color: #cdd6f4;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #cba6f7;
        margin: 15px 0;
    }
    .profile-card {
        background-color: #313244;
        color: #cdd6f4;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #f5c2e7;
        margin: 15px 0;
    }
    .step-badge {
        background-color: #f5c2e7;
        color: #1e1e2e;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 10px;
    }
    .skill-badge {
        background-color: #a6e3a1;
        color: #1e1e2e;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px 5px 5px 0;
    }
    .weak-badge {
        background-color: #f38ba8;
        color: #1e1e2e;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px 5px 5px 0;
    }
    .btn-primary {
        background-color: #cba6f7 !important;
        color: #1e1e2e !important;
        border: none !important;
        font-weight: bold !important;
    }
    .btn-secondary {
        background-color: #313244 !important;
        color: #cdd6f4 !important;
        border: 1px solid #cdd6f4 !important;
    }
    .stTextInput > div > div > input {
        background-color: #313244;
        color: #cdd6f4;
    }
    .stTextArea > div > div > textarea {
        background-color: #313244;
        color: #cdd6f4;
    }
    .st-bd {
        background-color: #313244;
    }
    .st-ex {
        color: #cdd6f4;
    }
    footer {
        visibility: hidden;
    }
    .metric-container {
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #313244;
        border-radius: 10px;
        padding: 15px;
        flex: 1;
        min-width: 200px;
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #89b4fa;
    }
    .metric-label {
        font-size: 14px;
        color: #cdd6f4;
        margin-top: 5px;
    }
    .recommendation-card {
        background-color: #313244;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 5px solid #f9e2af;
    }
    .path-card {
        background-color: #313244;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 5px solid #a6e3a1;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

def show_logo() -> None:
    """
    Display the Praxis logo.
    """
    st.sidebar.markdown("""
    <div style="
        font-family: 'Arial', sans-serif;
        font-weight: 900;
        font-size: 32px;
        letter-spacing: 3px;
        background: linear-gradient(90deg, #74c7ec, #cba6f7, #f38ba8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 10px 0;
        text-shadow: 0 0 5px rgba(203, 166, 247, 0.3);
        padding: 5px;
    ">
    PRAXIS
    </div>
    """, unsafe_allow_html=True)

def show_about() -> None:
    """
    Display the about section in the sidebar.
    """
    st.sidebar.markdown("### About")
    st.sidebar.info(
        """
        This app uses Groq's ultra-fast LLM API to help you learn coding concepts through guided practice.
        
        - Break down complex problems
        - Get personalized feedback
        - See visual solution approaches
        - Track your progress and skills
        - Get recommendations based on your strengths/weaknesses
        
        Built for effective learning through practice.
        """
    )

def show_learning_approach() -> None:
    """
    Display the learning approach explanation in the sidebar.
    """
    with st.sidebar.expander("Our Learning Approach", expanded=True):
        st.markdown("""
        **4-Step Learning Process:**
        1. **Challenge** - We'll break down the problem and encourage you to try it yourself first
        2. **Feedback** - Submit your attempt and get targeted feedback
        3. **Guidance** - If needed, receive a visual flowchart to guide your thinking
        4. **Solution** - Only after multiple attempts, view a complete solution with explanations
        
        This approach helps you develop problem-solving skills rather than just copying solutions.
        """)