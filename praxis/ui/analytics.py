# praxis/ui/analytics.py
import streamlit as st
import plotly.graph_objects as go
from typing import Callable

def render_analytics_page(db, assistant) -> None:
    """
    Render the analytics page with learning statistics and visualizations.
    
    Args:
        db: Database connection
        assistant: The LLM assistant
    """
    st.title("Learning Analytics")
    
    # Main analytics tabs
    tabs = st.tabs(["Skills Analysis", "Progress Tracking", "Recommendations", "Learning Patterns"])
    
    # Skills Analysis tab
    with tabs[0]:
        st.markdown("### Your Skills Profile")
        
        # Get skill categories
        skill_analysis = db.get_skill_analysis(st.session_state.user_id)
        
        if not skill_analysis or all(len(skills) == 0 for skills in skill_analysis.values()):
            st.info("Complete some challenges to build your skills profile!")
        else:
            # Create radar chart of skills
            top_skills = []
            for category, skills in skill_analysis.items():
                # Get top skills from each category
                if skills:
                    sorted_skills = sorted(skills, key=lambda x: x['proficiency'], reverse=True)
                    top_skills.extend(sorted_skills[:3])
            
            # Sort by proficiency and take top 10
            top_skills = sorted(top_skills, key=lambda x: x['proficiency'], reverse=True)[:10]
            
            if top_skills:
                # Create radar chart data
                skill_names = [skill['name'] for skill in top_skills]
                proficiencies = [skill['proficiency'] for skill in top_skills]
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatterpolar(
                    r=proficiencies,
                    theta=skill_names,
                    fill='toself',
                    name='Proficiency',
                    line_color='#89b4fa',
                    fillcolor='rgba(137, 180, 250, 0.3)'
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 1]
                        )
                    ),
                    title="Your Top Skills",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#cdd6f4')
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Skill breakdown by category
            st.markdown("### Skill Breakdown by Category")
            
            for category, skills in skill_analysis.items():
                if skills:
                    category_display = category.replace('_', ' ').title()
                    
                    with st.expander(f"{category_display} Skills ({len(skills)})", expanded=category in ["algorithm", "data_structure"]):
                        # Create bar chart
                        sorted_skills = sorted(skills, key=lambda x: x['proficiency'], reverse=True)
                        
                        skill_names = [skill['name'] for skill in sorted_skills]
                        proficiencies = [skill['proficiency'] * 100 for skill in sorted_skills]
                        practice_counts = [skill['practice_count'] for skill in sorted_skills]
                        
                        # Color gradient based on proficiency
                        colors = []
                        for prof in proficiencies:
                            if prof > 70:
                                colors.append('#a6e3a1')  # Green
                            elif prof > 40:
                                colors.append('#f9e2af')  # Yellow
                            else:
                                colors.append('#f38ba8')  # Red
                        
                        fig = go.Figure()
                        
                        # Add proficiency bars
                        fig.add_trace(go.Bar(
                            x=skill_names,
                            y=proficiencies,
                            name='Proficiency (%)',
                            marker_color=colors
                        ))
                        
                        # Add practice count line
                        fig.add_trace(go.Scatter(
                            x=skill_names,
                            y=practice_counts,
                            mode='lines+markers',
                            name='Practice Count',
                            yaxis='y2',
                            line=dict(color='#cba6f7', width=2),
                            marker=dict(size=8)
                        ))
                        
                        fig.update_layout(
                            title=f"{category_display} Skills",
                            xaxis=dict(title='Skills'),
                            yaxis=dict(
                                title='Proficiency (%)',
                                range=[0, 100],
                                ticksuffix='%'
                            ),
                            yaxis2=dict(
                                title='Practice Count',
                                overlaying='y',
                                side='right',
                                rangemode='nonnegative'
                            ),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#cdd6f4'),
                            barmode='group',
                            legend=dict(
                                orientation='h',
                                yanchor='bottom',
                                y=1.02,
                                xanchor='right',
                                x=1
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
    
    # Progress Tracking tab
    with tabs[1]:
        st.markdown("### Your Learning Progress")
        
        # Get progress data
        progress_data = db.get_user_progress(st.session_state.user_id)
        
        if progress_data['total_attempts'] == 0:
            st.info("Complete some challenges to see your progress!")
        else:
            # Progress metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                <div class="metric-value">{progress_data['total_attempts']}</div>
                <div class="metric-label">Total Attempts</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                success_rate = 0 if progress_data['total_attempts'] == 0 else (progress_data['successful_attempts'] / progress_data['total_attempts']) * 100
                st.markdown(f"""
                <div class="metric-card">
                <div class="metric-value">{success_rate:.1f}%</div>
                <div class="metric-label">Success Rate</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                <div class="metric-value">{progress_data['challenges_attempted']}</div>
                <div class="metric-label">Challenges Attempted</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                avg_score = progress_data['average_score'] * 100
                st.markdown(f"""
                <div class="metric-card">
                <div class="metric-value">{avg_score:.1f}%</div>
                <div class="metric-label">Average Score</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Get data for the progress chart
            cursor = db.conn.cursor()
            cursor.execute('''
                SELECT date(created_at) as date, AVG(score) as avg_score, COUNT(*) as attempts
                FROM attempts
                WHERE user_id = ?
                GROUP BY date(created_at)
                ORDER BY date ASC
                LIMIT 30
            ''', (st.session_state.user_id,))
            
            data = cursor.fetchall()
            
            if data:
                dates = [row[0] for row in data]
                scores = [row[1] for row in data]
                attempts = [row[2] for row in data]
                
                # Progress over time chart
                st.markdown("### Progress Over Time")
                
                fig = go.Figure()
                
                # Add score line
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=scores,
                    mode='lines+markers',
                    name='Average Score',
                    line=dict(color='#89b4fa', width=3),
                    marker=dict(size=8)
                ))
                
                # Add attempts bars
                fig.add_trace(go.Bar(
                    x=dates,
                    y=attempts,
                    name='Attempts',
                    marker_color='#fab387',
                    opacity=0.7,
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    title='Progress Over Time',
                    xaxis=dict(title='Date'),
                    yaxis=dict(
                        title=dict(
                            text='Average Score',
                            font=dict(color='#89b4fa')
                        ),
                        range=[0, 1],
                        tickfont=dict(color='#89b4fa')
                    ),
                    yaxis2=dict(
                        title=dict(
                            text='Number of Attempts',
                            font=dict(color='#fab387')
                        ),
                        tickfont=dict(color='#fab387'),
                        anchor='x',
                        overlaying='y',
                        side='right'
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#cdd6f4'),
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='right',
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Attempts distribution
            cursor.execute("""
                SELECT c.title, COUNT(a.attempt_id) as attempt_count, MAX(a.score) * 100 as max_score
                FROM attempts a
                JOIN challenges c ON a.challenge_id = c.challenge_id
                WHERE a.user_id = ?
                GROUP BY c.challenge_id
                ORDER BY attempt_count DESC
                LIMIT 10
            """, (st.session_state.user_id,))
            
            attempts_data = cursor.fetchall()
            
            if attempts_data:
                st.markdown("### Challenge Attempts Distribution")
                
                titles = [row[0][:20] + "..." if len(row[0]) > 20 else row[0] for row in attempts_data]
                attempt_counts = [row[1] for row in attempts_data]
                max_scores = [row[2] for row in attempts_data]
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=titles,
                    y=attempt_counts,
                    name='Attempts',
                    marker_color='#fab387'
                ))
                
                fig.add_trace(go.Scatter(
                    x=titles,
                    y=max_scores,
                    mode='lines+markers',
                    name='Max Score (%)',
                    yaxis='y2',
                    marker=dict(size=10, color='#a6e3a1'),
                    line=dict(width=2, color='#a6e3a1')
                ))
                
                fig.update_layout(
                    title="Challenge Attempts vs. Scores",
                    xaxis=dict(title=dict(text='Challenges')),
                    yaxis=dict(
                        title=dict(text='Number of Attempts'),
                        rangemode='nonnegative'
                    ),
                    yaxis2=dict(
                        title=dict(text='Max Score (%)'),
                        overlaying='y',
                        side='right',
                        range=[0, 100],
                        ticksuffix='%'
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#cdd6f4'),
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='right',
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Time spent distribution
            cursor.execute("""
                SELECT c.title, AVG(a.time_spent) / 60 as avg_minutes, COUNT(a.attempt_id) as attempts
                FROM attempts a
                JOIN challenges c ON a.challenge_id = c.challenge_id
                WHERE a.user_id = ? AND a.time_spent > 0
                GROUP BY c.challenge_id
                ORDER BY avg_minutes DESC
                LIMIT 10
            """, (st.session_state.user_id,))
            
            time_data = cursor.fetchall()
            
            if time_data:
                st.markdown("### Time Spent on Challenges")
                
                titles = [row[0][:20] + "..." if len(row[0]) > 20 else row[0] for row in time_data]
                avg_times = [round(row[1], 2) for row in time_data]
                attempts = [row[2] for row in time_data]
                
                fig = go.Figure()
                
                # Average time bars
                fig.add_trace(go.Bar(
                    x=titles,
                    y=avg_times,
                    name='Avg. Time (min)',
                    marker_color='#f5c2e7'
                ))
                
                fig.update_layout(
                    title="Average Time Spent per Challenge",
                    xaxis=dict(title=dict(text='Challenges')),
                    yaxis=dict(
                        title=dict(text='Time (minutes)'),
                        rangemode='nonnegative'
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#cdd6f4')
                )
                
                fig.add_trace(go.Scatter(
                    x=titles,
                    y=attempts,
                    mode='lines+markers',
                    name='Number of Attempts',
                    yaxis='y2',
                    marker=dict(size=8, color='#89b4fa'),
                    line=dict(width=2, color='#89b4fa')
                ))
                
                fig.update_layout(
                    yaxis2=dict(
                        title=dict(text='Attempts'),
                        overlaying='y',
                        side='right',
                        rangemode='nonnegative'
                    ),
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='right',
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations tab
    with tabs[2]:
        st.markdown("### Personalized Recommendations")
        
        # Get weak skills for recommendations
        weak_skills = db.get_user_weakest_skills(st.session_state.user_id, limit=5)
        
        if not weak_skills:
            st.info("Complete some challenges to get personalized recommendations!")
        else:
            with st.spinner("Generating personalized recommendations..."):
                # Generate analysis if not already in session state
                if "strength_analysis" not in st.session_state:
                    strength_analysis = assistant.analyze_user_strengths_weaknesses(st.session_state.user_id)
                    st.session_state.strength_analysis = strength_analysis
                else:
                    strength_analysis = st.session_state.strength_analysis
                
                if strength_analysis:
                    st.markdown("### Skills Analysis")
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
            
            # Recommended challenges
            st.markdown("### Recommended Challenges")
            
            # Generate new recommendations button
            if st.button("Find New Challenges For You"):
                with st.spinner("Finding challenges..."):
                    recommended = db.get_recommended_challenges(st.session_state.user_id, limit=5)
                    
                    if recommended:
                        for challenge in recommended:
                            challenge_id, title, description, difficulty, language, skills = challenge
                            
                            difficulty_stars = "⭐" * difficulty
                            
                            st.markdown(f"""
                            <div class="recommendation-card">
                            <h4>{title}</h4>
                            <p>Difficulty: {difficulty_stars} | Language: {language}</p>
                            <p>{description[:100]}...</p>
                            <p>Skills: {skills}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No more challenges available that match your needs. Try creating a custom challenge!")
            
            # Custom challenge for weak skills
            st.markdown("### Generate Custom Challenge")
            
            # Display weak skills
            st.markdown("#### Your areas for improvement:")
            for _, name, _, prof in weak_skills:
                st.markdown(f"""
                <div class="weak-badge">{name}: {prof:.2f}</div>
                """, unsafe_allow_html=True)
            
            # Language selection
            languages = ["Python", "JavaScript", "Java", "C++", "C#", "Go", "Ruby", "PHP", "TypeScript", "Rust", "Swift", "Kotlin"]
            selected_lang = st.selectbox("Challenge Language", languages)
            
            difficulty = st.slider("Difficulty Level", 1, 5, 3)
            
            if st.button("Generate Custom Challenge", type="primary"):
                with st.spinner("Creating personalized challenge..."):
                    weak_skill_names = [name for _, name, _, _ in weak_skills[:3]]
                    
                    system_prompt = f"""
                    You are a programming challenge creator. Create a coding challenge that targets these skills:
                    {', '.join(weak_skill_names)}
                    
                    The challenge should:
                    1. Be clear and specific
                    2. Have difficulty level: {difficulty}/5
                    3. Combine multiple skills in a practical scenario
                    4. Include input/output examples
                    5. Be relatively self-contained (not requiring external libraries)
                    
                    Format: Create a function that...
                    """
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Create a {selected_lang} coding challenge that develops skills in {', '.join(weak_skill_names)}"}
                    ]
                    
                    response = assistant._send_request(assistant.llama3_70b, messages, temperature=0.4, max_tokens=1000)
                    
                    if 'choices' in response and len(response['choices']) > 0:
                        problem_desc = f"Create code in {selected_lang} that: {response['choices'][0]['message']['content']}"
                        
                        # Display generated challenge
                        st.markdown("### Generated Challenge")
                        st.markdown(f"""
                        <div class="challenge-card">
                        <h4>Custom Challenge for {', '.join(weak_skill_names)}</h4>
                        <p>Difficulty: {"⭐" * difficulty} | Language: {selected_lang}</p>
                        <p>{problem_desc}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Option to start the challenge
                        if st.button("Start This Challenge"):
                            enhanced_prompt = assistant.enhance_prompt(problem_desc)
                            challenge = assistant.generate_learning_challenge(enhanced_prompt)
                            
                            # Save to database
                            challenge_id = db.store_challenge(problem_desc, enhanced_prompt, selected_lang, difficulty)
                            
                            # Map skills
                            skill_relevance = {skill: 0.9 for skill in weak_skill_names}
                            db.map_challenge_skills(challenge_id, skill_relevance)
                            
                            # Store in session
                            st.session_state.problem_desc = problem_desc
                            st.session_state.enhanced_prompt = enhanced_prompt
                            st.session_state.challenge = challenge
                            st.session_state.challenge_id = challenge_id
                            st.session_state.attempt_number = 1
                            st.session_state.start_time = None  # Will be set in challenge page
                            
                            # Redirect to challenge page
                            st.session_state.page = "challenge"
                            st.rerun()
    
    # Learning Patterns tab
    with tabs[3]:
        st.markdown("### Your Learning Patterns")
        
        # Get timing data
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT 
                strftime('%H', created_at) as hour, 
                COUNT(*) as attempts
            FROM attempts
            WHERE user_id = ?
            GROUP BY hour
            ORDER BY hour
        """, (st.session_state.user_id,))
        
        time_data = cursor.fetchall()
        
        if not time_data:
            st.info("Complete more challenges to see your learning patterns!")
        else:
            # Active hours chart
            hours = [f"{int(row[0]):02d}:00" for row in time_data]
            counts = [row[1] for row in time_data]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=hours,
                y=counts,
                marker_color='#cba6f7'
            ))
            
            fig.update_layout(
                title="Your Most Active Hours",
                xaxis=dict(title=dict(text='Hour of Day')),
                yaxis=dict(title=dict(text='Number of Attempts')),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cdd6f4')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Day of week data
            cursor.execute("""
                SELECT 
                    CASE cast(strftime('%w', created_at) as integer)
                        WHEN 0 THEN 'Sunday'
                        WHEN 1 THEN 'Monday'
                        WHEN 2 THEN 'Tuesday'
                        WHEN 3 THEN 'Wednesday'
                        WHEN 4 THEN 'Thursday'
                        WHEN 5 THEN 'Friday'
                        WHEN 6 THEN 'Saturday'
                    END as day_of_week,
                    COUNT(*) as attempts
                FROM attempts
                WHERE user_id = ?
                GROUP BY day_of_week
                ORDER BY cast(strftime('%w', created_at) as integer)
            """, (st.session_state.user_id,))
            
            day_data = cursor.fetchall()
            
            if day_data:
                days = [row[0] for row in day_data]
                day_counts = [row[1] for row in day_data]
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=days,
                    y=day_counts,
                    marker_color='#f9e2af'
                ))
                
                fig.update_layout(
                    title="Coding Activity by Day of Week",
                    xaxis=dict(title=dict(text='Day')),
                    yaxis=dict(title=dict(text='Number of Attempts')),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#cdd6f4')
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Challenge completion time analysis
            cursor.execute("""
                SELECT 
                    c.difficulty,
                    AVG(a.time_spent) / 60 as avg_minutes
                FROM attempts a
                JOIN challenges c ON a.challenge_id = c.challenge_id
                WHERE a.user_id = ? AND a.time_spent > 0
                GROUP BY c.difficulty
                ORDER BY c.difficulty
            """, (st.session_state.user_id,))
            
            difficulty_data = cursor.fetchall()
            
            if difficulty_data:
                difficulties = [f"Level {row[0]}" for row in difficulty_data]
                avg_times = [round(row[1], 2) for row in difficulty_data]
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=difficulties,
                    y=avg_times,
                    marker_color='#89b4fa'
                ))
                
                fig.update_layout(
                    title="Average Time by Difficulty Level",
                    xaxis=dict(title=dict(text='Difficulty')),
                    yaxis=dict(title=dict(text='Average Time (minutes)')),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#cdd6f4')
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Learning insights
            st.markdown("### Learning Insights")
            
            with st.spinner("Generating insights..."):
                # Get additional stats
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT strftime('%Y-%m-%d', created_at)) as active_days,
                        AVG(score) * 100 as avg_score,
                        (SELECT COUNT(*) FROM challenges c JOIN attempts a ON c.challenge_id = a.challenge_id WHERE a.user_id = ? AND a.successful = 1) as challenges_completed
                    FROM attempts
                    WHERE user_id = ?
                """, (st.session_state.user_id, st.session_state.user_id))
                
                stats = cursor.fetchone()
                
                if stats:
                    active_days, avg_score, completed = stats
                    
                    system_prompt = """
                    You are a learning analytics expert. Based on the user's learning data, provide personalized insights about:
                    1. Their learning patterns and habits
                    2. Suggestions for optimizing their study time based on active hours
                    3. Tips for improving their progress based on completion rates
                    4. Observations about their skill development journey
                    
                    Keep your insights encouraging, specific to their data, and actionable.
                    """
                    
                    # Format data for the prompt
                    active_hours_str = ", ".join([f"{h}: {c} attempts" for h, c in zip(hours[:3], sorted(counts, reverse=True)[:3])])
                    active_days_str = f"{active_days} days"
                    completion_rate = f"{avg_score:.1f}%"
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"""
                        My learning stats:
                        - Most active hours: {active_hours_str}
                        - Active days: {active_days_str}
                        - Average score: {completion_rate}
                        - Challenges completed: {completed}
                        
                        Please provide personalized learning insights.
                        """}
                    ]
                    
                    response = assistant._send_request(assistant.mixtral, messages, temperature=0.4, max_tokens=2000)
                    
                    if 'choices' in response and len(response['choices']) > 0:
                        insights = response['choices'][0]['message']['content']
                        
                        st.markdown(f"""
                        <div class="analytics-card">
                        {insights}
                        </div>
                        """, unsafe_allow_html=True)