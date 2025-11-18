"""
Chart generation helpers using Plotly
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from config import COLORS, CHART_THEME, CHART_HEIGHT


def create_status_pie_chart(df: pd.DataFrame):
    """Create pie chart for application status distribution"""
    fig = px.pie(
        df, 
        values='count', 
        names='status',
        title='Application Status Distribution',
        color='status',
        color_discrete_map={
            'submitted': COLORS['success'],
            'failed': COLORS['danger'],
            'pending': COLORS['warning'],
            'in_progress': COLORS['info']
        },
        hole=0.4
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        height=CHART_HEIGHT,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    return fig


def create_timeline_chart(df: pd.DataFrame):
    """Create timeline chart for applications over time"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['count'],
        mode='lines+markers',
        name='Total Applications',
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor=f'rgba(99, 102, 241, 0.2)'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['submitted'],
        mode='lines+markers',
        name='Successful',
        line=dict(color=COLORS['success'], width=2),
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['failed'],
        mode='lines+markers',
        name='Failed',
        line=dict(color=COLORS['danger'], width=2),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title='Applications Over Time',
        xaxis_title='Date',
        yaxis_title='Number of Applications',
        height=CHART_HEIGHT,
        hovermode='x unified',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    
    return fig


def create_company_bar_chart(df: pd.DataFrame):
    """Create horizontal bar chart for top companies"""
    fig = px.bar(
        df,
        y='company',
        x='job_count',
        orientation='h',
        title='Top Companies by Job Count',
        color='application_rate',
        color_continuous_scale='Viridis',
        text='job_count'
    )
    
    fig.update_traces(
        texttemplate='%{text}',
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Jobs: %{x}<br>Application Rate: %{marker.color:.1f}%<extra></extra>'
    )
    
    fig.update_layout(
        height=max(400, len(df) * 30),
        yaxis={'categoryorder':'total ascending'},
        xaxis_title='Number of Jobs',
        yaxis_title='',
        showlegend=False
    )
    
    return fig


def create_location_treemap(df: pd.DataFrame):
    """Create treemap for job locations"""
    fig = px.treemap(
        df,
        path=['location'],
        values='count',
        title='Jobs by Location',
        color='count',
        color_continuous_scale='Blues'
    )
    
    fig.update_traces(
        texttemplate='<b>%{label}</b><br>%{value} jobs',
        hovertemplate='<b>%{label}</b><br>Jobs: %{value}<extra></extra>'
    )
    
    fig.update_layout(height=CHART_HEIGHT)
    
    return fig


def create_success_rate_chart(df: pd.DataFrame):
    """Create bar chart for success rate by company"""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df['company'],
        x=df['success_rate'],
        orientation='h',
        marker=dict(
            color=df['success_rate'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Success %")
        ),
        text=df['success_rate'].apply(lambda x: f'{x:.1f}%'),
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Success Rate: %{x:.1f}%<br>Total Apps: %{customdata}<extra></extra>',
        customdata=df['total_applications']
    ))
    
    fig.update_layout(
        title='Success Rate by Company',
        xaxis_title='Success Rate (%)',
        yaxis_title='',
        height=max(400, len(df) * 25),
        yaxis={'categoryorder':'total ascending'}
    )
    
    return fig


def create_gauge_chart(value, title, max_value=100):
    """Create gauge chart for metrics"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 24}},
        delta={'reference': max_value * 0.7},
        gauge={
            'axis': {'range': [None, max_value], 'tickwidth': 1},
            'bar': {'color': COLORS['primary']},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, max_value * 0.5], 'color': COLORS['danger']},
                {'range': [max_value * 0.5, max_value * 0.75], 'color': COLORS['warning']},
                {'range': [max_value * 0.75, max_value], 'color': COLORS['success']}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.9
            }
        }
    ))
    
    fig.update_layout(height=300)
    
    return fig


def create_funnel_chart(data: dict):
    """Create funnel chart for application process"""
    fig = go.Figure(go.Funnel(
        y=list(data.keys()),
        x=list(data.values()),
        textposition="inside",
        textinfo="value+percent initial",
        marker=dict(
            color=[COLORS['primary'], COLORS['info'], COLORS['warning'], COLORS['success']]
        ),
        connector={"line": {"color": "royalblue", "dash": "dot", "width": 3}}
    ))
    
    fig.update_layout(
        title='Application Funnel',
        height=CHART_HEIGHT
    )
    
    return fig


def create_heatmap(df: pd.DataFrame):
    """Create heatmap for application activity"""
    fig = px.density_heatmap(
        df,
        x='hour',
        y='day',
        z='count',
        title='Application Activity Heatmap',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        height=CHART_HEIGHT,
        xaxis_title='Hour of Day',
        yaxis_title='Day of Week'
    )
    
    return fig
