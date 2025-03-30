# praxis/ui/profile.py
import streamlit as st
from typing import Callable

from utils.visualization import render_skill_chart, render_skill_progress

def render_profile_page(db, assistant, go_to_page: Callable) -> None:
    """
    Render the user's skills profile page.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
        go_to_page: Function to navigate to a different page
    """
    st.title("My Skills Profile")
    
    # Get comprehensive skill analysis
    skill_analysis = db.get_skill_analysis(st.session_state.user_id)
    
    if not skill_analysis or all(len(skills) == 0 for skills in skill_analysis.values()):
        st.info("Complete some challenges to build your skills profile!")
    else:
        # Strengths and weaknesses analysis
        with st.expander("Your Strengths and Weaknesses Analysis", expanded=True):
            strength_analysis = assistant.analyze_user_strengths_weaknesses(st.session_state.user_id)
            
            if strength_analysis:
                st.markdown(f"""
                <div class="analytics-card">
                {strength_analysis['analysis']}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("### Recommended Learning Focus")
                st.markdown(f"""
                <div class="recommendation-card">
                {strength_analysis['recommendations']}
                </div>
                """, unsafe_allow_html=True)
        
        # Skill categories
        for category, skills in skill_analysis.items():
            if skills:
                # Skip categories with no skills
                if len(skills) == 0:
                    continue
                
                # Format category name
                category_display = category.replace('_', ' ').title()
                
                with st.expander(f"{category_display} Skills ({len(skills)})", expanded=category in ["algorithm", "data_structure", "concept"]):
                    # Sort by proficiency
                    sorted_skills = sorted(skills, key=lambda x: x['proficiency'], reverse=True)
                    
                    # Create columns for each skill
                    cols = st.columns(3)
                    
                    for i, skill in enumerate(sorted_skills):
                        col = cols[i % 3]
                        
                        with col:
                            proficiency = skill['proficiency'] * 100
                            color = "#a6e3a1" if proficiency > 60 else "#f9e2af" if proficiency > 30 else "#f38ba8"
                            
                            st.markdown(f"""
                            <div style="background-color: #313244; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                            <h4>{skill['name']}</h4>
                            <div style="background-color: #1e1e2e; height: 10px; border-radius: 5px; margin: 10px 0;">
                                <div style="background-color: {color}; width: {proficiency}%; height: 10px; border-radius: 5px;"></div>
                            </div>
                            <p>Proficiency: {proficiency:.1f}% | Practice Count: {skill['practice_count']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # View progress for this skill
                            if skill['practice_count'] > 0 and st.button(f"View Progress", key=f"view_{skill['skill_id']}"):
                                fig = render_skill_progress(st.session_state.user_id, skill['skill_id'], db)
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
    
    # Generate personalized learning plan
    st.markdown("### Generate Personalized Learning Plan")
    languages = ["Python", "JavaScript", "Java", "C++", "C#", "Go", "Ruby", "PHP", "TypeScript", "Rust", "Swift", "Kotlin"]
    selected_lang = st.selectbox("Select Language", languages)
    
    if st.button("Create Learning Path", type="primary"):
        with st.spinner("Generating personalized learning path..."):
            path_id = assistant.generate_personalized_learning_path(st.session_state.user_id, selected_lang)
            
            if path_id:
                st.success("Learning path created! View it in the Learning Paths section.")
                st.session_state.path_id = path_id
                go_to_page("paths")
            else:
                st.error("Could not create learning path. Try again later.")