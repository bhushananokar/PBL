# praxis/utils/visualization.py
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from typing import List, Tuple, Optional, Dict, Any

def render_mermaid(mermaid_code: str, height: int = 400) -> None:
    """Render mermaid diagram in Streamlit."""
    html = f"""
    <div class="mermaid">
    {mermaid_code}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
    </script>
    """
    components.html(html, height=height)

def render_skill_chart(skills_data: List[Tuple], title: str) -> Optional[go.Figure]:
    """Render a radar chart for skills visualization."""
    if not skills_data:
        return None
    
    categories = [skill[1] for skill in skills_data]  # Skill names
    values = [skill[3] for skill in skills_data]  # Proficiency values
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
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
        title=title,
        margin=dict(t=50, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(
            color='#cdd6f4'
        )
    )
    
    return fig

def render_progress_chart(user_id: str, db) -> Optional[go.Figure]:
    """Render a chart showing user progress over time."""
    if not db:
        return None
    
    # Get recent attempts
    cursor = db.conn.cursor()
    cursor.execute('''
        SELECT date(created_at) as date, AVG(score) as avg_score, COUNT(*) as attempts
        FROM attempts
        WHERE user_id = ?
        GROUP BY date(created_at)
        ORDER BY date ASC
        LIMIT 30
    ''', (user_id,))
    
    data = cursor.fetchall()
    
    if not data:
        return None
    
    dates = [row[0] for row in data]
    scores = [row[1] for row in data]
    attempts = [row[2] for row in data]
    
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
    
    return fig

def render_skill_progress(user_id: str, skill_id: int, db) -> Optional[go.Figure]:
    """Render a chart showing progress in a specific skill over time."""
    if not db:
        return None
    
    # Get skill name
    cursor = db.conn.cursor()
    cursor.execute('SELECT name FROM skills WHERE skill_id = ?', (skill_id,))
    result = cursor.fetchone()
    if not result:
        return None
        
    skill_name = result[0]
    
    # Get progress data
    progress_data = db.get_skill_progress_over_time(user_id, skill_id)
    
    if not progress_data:
        return None
    
    dates = [row[0] for row in progress_data]
    weighted_scores = [row[1] * row[2] for row in progress_data]  # score * relevance
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=weighted_scores,
        mode='lines+markers',
        name='Skill Progress',
        line=dict(color='#a6e3a1', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=f'Progress in {skill_name}',
        xaxis=dict(title=dict(text='Date')),
        yaxis=dict(title=dict(text='Weighted Score')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#cdd6f4')
    )
    
    return fig