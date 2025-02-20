import os
import re
import json
import time
import streamlit as st
import requests
from streamlit_ace import st_ace
import streamlit.components.v1 as components

class CodeAssistant:
    def __init__(self, api_key=None):
        """Initialize the Code Assistant with Groq API key."""
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key is required. Set GROQ_API_KEY environment variable or provide it as an argument.")
        
        # Set up API endpoint
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Model configurations
        self.llama3_70b = "llama3-70b-8192"
        self.mixtral = "mixtral-8x7b-32768"
        
    def _send_request(self, model, messages, temperature=0.2, max_tokens=4000):
        """Send a request to the Groq API."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def enhance_prompt(self, user_prompt):
        """Use Groq to enhance and structure the user prompt for better code generation."""
        system_prompt = """
        You are an expert programming assistant. Your task is to:
        1. Analyze the user's coding request
        2. Structure and enhance it for optimal code generation
        3. Include specific requirements, edge cases, and expected functionality
        4. Format the output as a clear, detailed coding task
        5. Include code comments where helpful
        
        DO NOT generate any code yourself. Focus only on improving the prompt.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Enhance this coding prompt for better code generation: {user_prompt}"}
        ]
        
        response = self._send_request(self.mixtral, messages, temperature=0.3)
        
        if 'choices' in response and len(response['choices']) > 0:
            return response['choices'][0]['message']['content']
        else:
            raise Exception("Failed to get a valid response from Groq API")
    
    def generate_code(self, enhanced_prompt):
        """Use Groq to generate code based on the enhanced prompt."""
        system_prompt = """
        You are an expert code generator. Given a programming problem:
        1. Write clean, efficient, and well-documented code
        2. Include helpful comments explaining key components
        3. Handle edge cases and potential errors
        4. Follow best practices for the relevant language/framework
        5. ONLY return the code and essential documentation - no explanations or conversation
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": enhanced_prompt}
        ]
        
        response = self._send_request(self.llama3_70b, messages, temperature=0.2, max_tokens=8000)
        
        if 'choices' in response and len(response['choices']) > 0:
            # Clean up code - extract from markdown if needed
            return self._extract_code(response['choices'][0]['message']['content'])
        else:
            raise Exception("Failed to get a valid response from Groq API")
    
    def _extract_code(self, text):
        """Extract code from markdown code blocks if present."""
        # Look for triple backtick code blocks
        code_pattern = r'```(?:\w+)?\n([\s\S]*?)\n```'
        code_matches = re.findall(code_pattern, text)
        
        if code_matches:
            # Join multiple code blocks with newlines
            return '\n\n'.join(code_matches)
        else:
            # Return the original text if no code blocks found
            return text
    
    def analyze_complexity(self, code):
        """Use Groq to analyze time and space complexity of the code."""
        system_prompt = """
        You are an algorithm analysis expert. Analyze the provided code and:
        1. Determine its time complexity (Big O notation)
        2. Determine its space complexity (Big O notation)
        3. Explain the reasoning behind your analysis
        4. Consider best, average, and worst-case scenarios where applicable
        5. Format your response as JSON with keys: time_complexity, space_complexity, explanation
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze the time and space complexity of this code:\n\n{code}"}
        ]
        
        response = self._send_request(self.llama3_70b, messages, temperature=0.1, max_tokens=4000)
        
        if 'choices' in response and len(response['choices']) > 0:
            result = response['choices'][0]['message']['content']
            try:
                # Try to extract JSON from the response
                json_pattern = r'\{[\s\S]*\}'
                json_match = re.search(json_pattern, result)
                if json_match:
                    json_str = json_match.group(0)
                    complexity_analysis = json.loads(json_str)
                else:
                    # If no JSON found, extract complexity using patterns
                    complexity_analysis = {
                        "time_complexity": self._extract_complexity(result, "time"),
                        "space_complexity": self._extract_complexity(result, "space"),
                        "explanation": result
                    }
                return complexity_analysis
            except Exception as e:
                return {
                    "time_complexity": "Analysis failed",
                    "space_complexity": "Analysis failed",
                    "explanation": f"Could not parse complexity analysis: {str(e)}\n\nRaw response: {result}"
                }
        else:
            raise Exception("Failed to get a valid response from Groq API")
    
    def _extract_complexity(self, text, complexity_type):
        """Helper method to extract complexity from text."""
        patterns = [
            rf"{complexity_type}.*complexity.*O\([^)]+\)",
            rf"{complexity_type}.*O\([^)]+\)",
            r"O\([^)]+\)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return "Undefined"
    
    def generate_visualization(self, code):
        """Generate Mermaid diagram visualizing the code structure."""
        system_prompt = """
        You are a code visualization expert. Create a Mermaid diagram that visualizes the structure and flow of the provided code:
        1. For object-oriented code: show classes, methods, and relationships
        2. For procedural code: show the control flow and function calls
        3. For data processing: show the data flow
        4. Keep the diagram clear and focused on key components
        5. Provide ONLY the Mermaid code without any explanation or markdown formatting
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a Mermaid diagram visualizing this code:\n\n{code}"}
        ]
        
        response = self._send_request(self.llama3_70b, messages, temperature=0.2, max_tokens=4000)
        
        if 'choices' in response and len(response['choices']) > 0:
            result = response['choices'][0]['message']['content']
            # Extract Mermaid code from the response
            mermaid_pattern = r'```mermaid\n([\s\S]*?)\n```'
            mermaid_match = re.search(mermaid_pattern, result)
            if mermaid_match:
                return mermaid_match.group(1)
            else:
                # Strip any other markdown formatting if present
                clean_pattern = r'```\n([\s\S]*?)\n```'
                clean_match = re.search(clean_pattern, result)
                if clean_match:
                    return clean_match.group(1)
                else:
                    return result
        else:
            raise Exception("Failed to get a valid response from Groq API")
    
    def review_code(self, code):
        """Use Groq to review code quality and suggest improvements."""
        system_prompt = """
        You are an expert code reviewer. Analyze the provided code and:
        1. Rate it on a scale of 1-10 for: readability, efficiency, robustness, and maintainability
        2. Identify specific strengths in the implementation
        3. Highlight areas for improvement with concrete suggestions
        4. Suggest optimizations for performance or resource usage
        5. Check for potential bugs, edge cases, or security issues
        6. Format as JSON with keys: overall_rating, strengths, improvements, optimizations, potential_issues
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Review this code and suggest improvements:\n\n{code}"}
        ]
        
        response = self._send_request(self.llama3_70b, messages, temperature=0.3, max_tokens=6000)
        
        if 'choices' in response and len(response['choices']) > 0:
            result = response['choices'][0]['message']['content']
            try:
                # Try to extract JSON from the response
                json_pattern = r'\{[\s\S]*\}'
                json_match = re.search(json_pattern, result)
                if json_match:
                    json_str = json_match.group(0)
                    review = json.loads(json_str)
                else:
                    # If no JSON structure found, return the text response
                    review = {
                        "overall_rating": "N/A",
                        "review": result
                    }
                return review
            except Exception as e:
                return {
                    "overall_rating": "Review failed",
                    "review": f"Could not parse review: {str(e)}\n\nRaw response: {result}"
                }
        else:
            raise Exception("Failed to get a valid response from Groq API")

    def rate_user_code(self, code):
        """Rate user-provided code and suggest improvements."""
        return self.review_code(code)

# Streamlit app
def render_mermaid(mermaid_code):
    """Render mermaid diagram in Streamlit."""
    html = f"""
    <div class="mermaid">
    {mermaid_code}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
    """
    components.html(html, height=400)

def main():
    st.set_page_config(
        page_title="Groq Coding Assistant",
        page_icon="🧑‍💻",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Add custom CSS
    st.markdown("""
    <style>
    .main {
        background-color: #f5f7fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #e6f0ff;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4b88ff !important;
        color: white !important;
    }
    .stMarkdown {
        padding: 10px;
    }
    h1, h2, h3 {
        color: #1e3d59;
    }
    .highlight {
        background-color: #4a3928;
        color: #f5e9d9;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #ffa41b;
        margin: 10px 0;
    }
    .code-output {
        background-color: #213552;
        color: #e6edf7;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #4b88ff;
        margin: 10px 0;
    }
    .review-card {
        background-color: #1d3246;
        color: #d9e6f2;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        border: 1px solid #345a7d;
    }
    .rating-box {
        background-color: #1e5631;
        color: white;
        padding: 5px 15px;
        border-radius: 15px;
        display: inline-block;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🧠 Groq Coding Assistant")
    st.sidebar.image("https://assets-global.website-files.com/64f6ea097da2395a3add0d15/65150b4f4a2cc2b5c2bb98d2_groq-logo.svg", width=200)
    
    # API Key input
    api_key = st.sidebar.text_input("Groq API Key", type="password")
    
    # Model selection
    model_info = st.sidebar.expander("Model Information", expanded=False)
    with model_info:
        st.markdown("""
        **Models Used:**
        - **LLaMA 3 70B**: Used for code generation, complexity analysis, and visualization
        - **Mixtral 8x7B**: Used for prompt enhancement and simpler tasks
        
        These models provide state-of-the-art capabilities with significantly faster inference than other LLMs.
        """)
    
    # Mode selection
    app_mode = st.sidebar.selectbox(
        "Choose Mode",
        ["Generate Code", "Review My Code"]
    )
    
    # Optional settings
    st.sidebar.markdown("### Output Options")
    analyze_complexity = st.sidebar.checkbox("Analyze Complexity", value=True)
    generate_visualization = st.sidebar.checkbox("Generate Visualization", value=True)
    review_code = st.sidebar.checkbox("Review Code Quality", value=True)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        """
        This app uses Groq's ultra-fast LLM API to help you with coding tasks.
        - Generate high-quality code from descriptions
        - Analyze code complexity
        - Visualize code structure
        - Get expert code reviews
        
        Built with Streamlit and Groq API
        """
    )
    
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
            
        assistant = CodeAssistant(api_key=api_key)
        
        if app_mode == "Generate Code":
            st.title("✨ AI Code Generator")
            st.markdown(
                """
                <div class="highlight">
                Describe what code you need, and the AI will generate it for you.
                Be as specific as possible for better results.
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            user_prompt = st.text_area(
                "Describe the code you need:",
                height=150,
                placeholder="E.g., Write a Python function that finds the longest palindromic substring in a given string.",
                key="user_prompt"
            )
            
            programming_language = st.selectbox(
                "Primary Programming Language",
                ["Python", "JavaScript", "Java", "C++", "C#", "Go", "Ruby", "PHP", "TypeScript", "Rust", "Swift", "Kotlin"]
            )
            
            if st.button("✨ Generate Code", key="generate_button", type="primary"):
                if not user_prompt:
                    st.error("Please enter a description of the code you need.")
                else:
                    with st.spinner("🧠 Enhancing your prompt..."):
                        enhanced_prompt = f"Create code in {programming_language} that: {user_prompt}"
                        enhanced_prompt = assistant.enhance_prompt(enhanced_prompt)
                    
                    st.markdown("### 🔍 Enhanced Prompt")
                    st.markdown(f"""<div class="highlight">{enhanced_prompt}</div>""", unsafe_allow_html=True)
                    
                    with st.spinner("💻 Generating code..."):
                        generated_code = assistant.generate_code(enhanced_prompt)
                    
                    tabs = st.tabs(["Generated Code", "Editor", "Complexity Analysis", "Visualization", "Code Review"])
                    
                    with tabs[0]:
                        st.markdown("### 📝 Generated Code")
                        st.code(generated_code, language=programming_language.lower())
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("⬇️ Download Code", key="download_code"):
                                file_ext = {
                                    "Python": "py", "JavaScript": "js", "Java": "java",
                                    "C++": "cpp", "C#": "cs", "Go": "go", "Ruby": "rb",
                                    "PHP": "php", "TypeScript": "ts", "Rust": "rs",
                                    "Swift": "swift", "Kotlin": "kt"
                                }.get(programming_language, "txt")
                                
                                st.download_button(
                                    label="Click to Download",
                                    data=generated_code,
                                    file_name=f"generated_code.{file_ext}",
                                    mime="text/plain",
                                )
                    
                    with tabs[1]:
                        st.markdown("### 🖊️ Code Editor")
                        st.markdown("You can edit the generated code here:")
                        edited_code = st_ace(
                            value=generated_code,
                            language=programming_language.lower(),
                            theme="monokai",
                            font_size=14,
                            key="editor"
                        )
                    
                    if analyze_complexity:
                        with tabs[2]:
                            st.markdown("### ⏱️ Complexity Analysis")
                            with st.spinner("Analyzing complexity..."):
                                complexity = assistant.analyze_complexity(generated_code)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"""
                                #### Time Complexity
                                <div class="rating-box">{complexity['time_complexity']}</div>
                                """, unsafe_allow_html=True)
                            
                            with col2:
                                st.markdown(f"""
                                #### Space Complexity
                                <div class="rating-box">{complexity['space_complexity']}</div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown("#### Explanation")
                            st.markdown(f"""<div class="code-output">{complexity['explanation']}</div>""", unsafe_allow_html=True)
                    
                    if generate_visualization:
                        with tabs[3]:
                            st.markdown("### 📊 Code Visualization")
                            with st.spinner("Generating visualization..."):
                                mermaid_code = assistant.generate_visualization(generated_code)
                            
                            st.markdown("#### Code Structure Diagram")
                            render_mermaid(mermaid_code)
                            
                            with st.expander("View Mermaid Code"):
                                st.code(mermaid_code, language="mermaid")
                    
                    if review_code:
                        with tabs[4]:
                            st.markdown("### 🔍 Code Review")
                            with st.spinner("Reviewing code..."):
                                code_review = assistant.review_code(generated_code)
                            
                            if 'overall_rating' in code_review and code_review['overall_rating'] != "N/A" and code_review['overall_rating'] != "Review failed":
                                # Try to convert to numeric if possible
                                try:
                                    rating = float(code_review['overall_rating'])
                                    st.markdown(f"""
                                    #### Overall Rating: <div class="rating-box">{rating}/10</div>
                                    """, unsafe_allow_html=True)
                                except:
                                    st.markdown(f"""
                                    #### Overall Rating: <div class="rating-box">{code_review['overall_rating']}</div>
                                    """, unsafe_allow_html=True)
                            
                            if 'strengths' in code_review and isinstance(code_review['strengths'], list):
                                st.markdown("#### ✅ Strengths")
                                for strength in code_review['strengths']:
                                    st.markdown(f"- {strength}")
                            
                            if 'improvements' in code_review and isinstance(code_review['improvements'], list):
                                st.markdown("#### 🔧 Improvements")
                                for improvement in code_review['improvements']:
                                    st.markdown(f"- {improvement}")
                            
                            if 'optimizations' in code_review and isinstance(code_review['optimizations'], list):
                                st.markdown("#### ⚡ Optimizations")
                                for optimization in code_review['optimizations']:
                                    st.markdown(f"- {optimization}")
                            
                            if 'potential_issues' in code_review and isinstance(code_review['potential_issues'], list):
                                st.markdown("#### ⚠️ Potential Issues")
                                for issue in code_review['potential_issues']:
                                    st.markdown(f"- {issue}")
                            
                            if 'review' in code_review and not isinstance(code_review.get('strengths'), list):
                                st.markdown("#### Detailed Review")
                                st.markdown(f"""<div class="review-card">{code_review['review']}</div>""", unsafe_allow_html=True)
        
        else:  # Review My Code mode
            st.title("🔍 AI Code Reviewer")
            st.markdown(
                """
                <div class="highlight">
                Paste your code below for an expert AI review.
                Get insights on quality, performance, and potential improvements.
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
            
            if st.button("🔍 Review Code", key="review_button", type="primary"):
                if not user_code:
                    st.error("Please enter your code for review.")
                else:
                    tabs = st.tabs(["Code Review", "Complexity Analysis", "Visualization"])
                    
                    with tabs[0]:
                        st.markdown("### 🔍 Code Review")
                        with st.spinner("Analyzing your code..."):
                            code_review = assistant.rate_user_code(user_code)
                        
                        if 'overall_rating' in code_review and code_review['overall_rating'] != "N/A" and code_review['overall_rating'] != "Review failed":
                            # Try to convert to numeric if possible
                            try:
                                rating = float(code_review['overall_rating'])
                                st.markdown(f"""
                                #### Overall Rating: <div class="rating-box">{rating}/10</div>
                                """, unsafe_allow_html=True)
                            except:
                                st.markdown(f"""
                                #### Overall Rating: <div class="rating-box">{code_review['overall_rating']}</div>
                                """, unsafe_allow_html=True)
                        
                        if 'strengths' in code_review and isinstance(code_review['strengths'], list):
                            st.markdown("#### ✅ Strengths")
                            for strength in code_review['strengths']:
                                st.markdown(f"- {strength}")
                        
                        if 'improvements' in code_review and isinstance(code_review['improvements'], list):
                            st.markdown("#### 🔧 Improvements")
                            for improvement in code_review['improvements']:
                                st.markdown(f"- {improvement}")
                        
                        if 'optimizations' in code_review and isinstance(code_review['optimizations'], list):
                            st.markdown("#### ⚡ Optimizations")
                            for optimization in code_review['optimizations']:
                                st.markdown(f"- {optimization}")
                        
                        if 'potential_issues' in code_review and isinstance(code_review['potential_issues'], list):
                            st.markdown("#### ⚠️ Potential Issues")
                            for issue in code_review['potential_issues']:
                                st.markdown(f"- {issue}")
                        
                        if 'review' in code_review and not isinstance(code_review.get('strengths'), list):
                            st.markdown("#### Detailed Review")
                            st.markdown(f"""<div class="review-card">{code_review['review']}</div>""", unsafe_allow_html=True)
                    
                    with tabs[1]:
                        st.markdown("### ⏱️ Complexity Analysis")
                        with st.spinner("Analyzing complexity..."):
                            complexity = assistant.analyze_complexity(user_code)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"""
                            #### Time Complexity
                            <div class="rating-box">{complexity['time_complexity']}</div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f"""
                            #### Space Complexity
                            <div class="rating-box">{complexity['space_complexity']}</div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("#### Explanation")
                        st.markdown(f"""<div class="code-output">{complexity['explanation']}</div>""", unsafe_allow_html=True)
                    
                    with tabs[2]:
                        st.markdown("### 📊 Code Visualization")
                        with st.spinner("Generating visualization..."):
                            mermaid_code = assistant.generate_visualization(user_code)
                        
                        st.markdown("#### Code Structure Diagram")
                        render_mermaid(mermaid_code)
                        
                        with st.expander("View Mermaid Code"):
                            st.code(mermaid_code, language="mermaid")
    
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

if __name__ == "__main__":
    main()