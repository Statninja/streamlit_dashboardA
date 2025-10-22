import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Configure the page
st.set_page_config(
    page_title="Banking KPI Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #7f8c8d;
        margin-bottom: 2rem;
    }
    .kpi-card {
        background-color: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
        border-left: 4px solid #3498db;
    }
    .kpi-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    .kpi-change {
        display: inline-flex;
        align-items: center;
        font-size: 0.9rem;
        font-weight: 500;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        margin-bottom: 0.5rem;
    }
    .kpi-change.positive {
        background-color: rgba(39, 174, 96, 0.1);
        color: #27ae60;
    }
    .kpi-change.negative {
        background-color: rgba(231, 76, 60, 0.1);
        color: #e74c3c;
    }
    .kpi-target {
        font-size: 0.9rem;
        color: #7f8c8d;
    }
    .performance-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    .performance-excellent { background-color: #27ae60; }
    .performance-good { background-color: #3498db; }
    .performance-average { background-color: #f39c12; }
    .performance-poor { background-color: #e74c3c; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🏦 Banking Performance Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Key Performance Indicators & Financial Metrics</div>', unsafe_allow_html=True)

# Generate sample data
@st.cache_data
def generate_kpi_data():
    dates = pd.date_range(start=datetime.now() - timedelta(days=90), end=datetime.now(), freq='D')
    
    data = {
        'Date': dates,
        'Awareness': np.random.normal(10000, 500, len(dates)).cumsum() + 100000,
        'Customer Deposits': np.random.normal(5000, 300, len(dates)).cumsum() + 500000,
        'Loan Applications': np.random.normal(200, 50, len(dates)).cumsum() + 5000,
        'Digital Engagement': np.random.normal(100, 20, len(dates)).cumsum() + 3000,
        'Net Interest Margin': np.random.normal(0.1, 0.05, len(dates)) + 2.5,
        'Operating Efficiency': np.random.normal(0.05, 0.02, len(dates)) + 0.6
    }
    
    df = pd.DataFrame(data)
    df['Awareness'] = df['Awareness'].apply(lambda x: max(x, 100000))
    df['Customer Deposits'] = df['Customer Deposits'].apply(lambda x: max(x, 500000))
    df['Loan Applications'] = df['Loan Applications'].apply(lambda x: max(x, 5000))
    df['Digital Engagement'] = df['Digital Engagement'].apply(lambda x: max(x, 3000))
    
    return df

df = generate_kpi_data()

# Calculate current values and changes
current_date = df['Date'].max()
month_ago = current_date - timedelta(days=30)

current_values = {}
previous_values = {}
changes = {}

for col in df.columns[1:]:
    current_values[col] = df[df['Date'] == current_date][col].values[0]
    previous_values[col] = df[df['Date'] == month_ago][col].values[0]
    changes[col] = ((current_values[col] - previous_values[col]) / previous_values[col]) * 100

# Define KPI targets and performance levels
kpi_targets = {
    'Awareness': 120000,
    'Customer Deposits': 600000,
    'Loan Applications': 8000,
    'Digital Engagement': 5000,
    'Net Interest Margin': 3.0,
    'Operating Efficiency': 0.55
}

performance_levels = {}
for kpi in current_values:
    achievement = (current_values[kpi] / kpi_targets[kpi]) * 100
    if achievement >= 100:
        performance_levels[kpi] = 'Excellent'
    elif achievement >= 90:
        performance_levels[kpi] = 'Good'
    elif achievement >= 80:
        performance_levels[kpi] = 'Average'
    else:
        performance_levels[kpi] = 'Poor'

# Create KPI cards in columns
col1, col2, col3 = st.columns(3)

with col1:
    # Awareness KPI
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Awareness</div>
        <div class="kpi-value">{current_values['Awareness']:,.0f}</div>
        <div class="kpi-change {'positive' if changes['Awareness'] > 0 else 'negative'}">
            <span class="performance-indicator performance-{performance_levels['Awareness'].lower()}"></span>
            {changes['Awareness']:+.1f}% vs previous period
        </div>
        <div class="kpi-target">Target: {kpi_targets['Awareness']:,.0f} | Performance: {performance_levels['Awareness']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create trend chart for Awareness
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['Awareness'],
        mode='lines',
        line=dict(color='#3498db', width=3),
        name='Awareness'
    ))
    fig.update_layout(
        height=150,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Customer Deposits KPI
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Customer Deposits</div>
        <div class="kpi-value">${current_values['Customer Deposits']:,.0f}</div>
        <div class="kpi-change {'positive' if changes['Customer Deposits'] > 0 else 'negative'}">
            <span class="performance-indicator performance-{performance_levels['Customer Deposits'].lower()}"></span>
            {changes['Customer Deposits']:+.1f}% vs previous period
        </div>
        <div class="kpi-target">Target: ${kpi_targets['Customer Deposits']:,.0f} | Performance: {performance_levels['Customer Deposits']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create trend chart for Customer Deposits
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['Customer Deposits'],
        mode='lines',
        line=dict(color='#9b59b6', width=3),
        name='Customer Deposits'
    ))
    fig.update_layout(
        height=150,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Loan Applications KPI
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Loan Applications</div>
        <div class="kpi-value">{current_values['Loan Applications']:,.0f}</div>
        <div class="kpi-change {'positive' if changes['Loan Applications'] > 0 else 'negative'}">
            <span class="performance-indicator performance-{performance_levels['Loan Applications'].lower()}"></span>
            {changes['Loan Applications']:+.1f}% vs previous period
        </div>
        <div class="kpi-target">Target: {kpi_targets['Loan Applications']:,.0f} | Performance: {performance_levels['Loan Applications']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create trend chart for Loan Applications
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['Loan Applications'],
        mode='lines',
        line=dict(color='#e74c3c', width=3),
        name='Loan Applications'
    ))
    fig.update_layout(
        height=150,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Digital Engagement KPI
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Digital Engagement</div>
        <div class="kpi-value">{current_values['Digital Engagement']:,.0f}</div>
        <div class="kpi-change {'positive' if changes['Digital Engagement'] > 0 else 'negative'}">
            <span class="performance-indicator performance-{performance_levels['Digital Engagement'].lower()}"></span>
            {changes['Digital Engagement']:+.1f}% vs previous period
        </div>
        <div class="kpi-target">Target: {kpi_targets['Digital Engagement']:,.0f} | Performance: {performance_levels['Digital Engagement']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create trend chart for Digital Engagement
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['Digital Engagement'],
        mode='lines',
        line=dict(color='#f39c12', width=3),
        name='Digital Engagement'
    ))
    fig.update_layout(
        height=150,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

with col3:
    # Net Interest Margin KPI
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Net Interest Margin</div>
        <div class="kpi-value">{current_values['Net Interest Margin']:.2f}%</div>
        <div class="kpi-change {'positive' if changes['Net Interest Margin'] > 0 else 'negative'}">
            <span class="performance-indicator performance-{performance_levels['Net Interest Margin'].lower()}"></span>
            {changes['Net Interest Margin']:+.1f}% vs previous period
        </div>
        <div class="kpi-target">Target: {kpi_targets['Net Interest Margin']:.1f}% | Performance: {performance_levels['Net Interest Margin']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create trend chart for Net Interest Margin
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['Net Interest Margin'],
        mode='lines',
        line=dict(color='#1abc9c', width=3),
        name='Net Interest Margin'
    ))
    fig.update_layout(
        height=150,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Operating Efficiency KPI
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Operating Efficiency</div>
        <div class="kpi-value">{current_values['Operating Efficiency']:.2f}</div>
        <div class="kpi-change {'positive' if changes['Operating Efficiency'] < 0 else 'negative'}">
            <span class="performance-indicator performance-{performance_levels['Operating Efficiency'].lower()}"></span>
            {changes['Operating Efficiency']:+.1f}% vs previous period
        </div>
        <div class="kpi-target">Target: {kpi_targets['Operating Efficiency']:.2f} | Performance: {performance_levels['Operating Efficiency']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create trend chart for Operating Efficiency
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['Operating Efficiency'],
        mode='lines',
        line=dict(color='#34495e', width=3),
        name='Operating Efficiency'
    ))
    fig.update_layout(
        height=150,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# Detailed trend analysis section
st.markdown("---")
st.subheader("Detailed Trend Analysis")

# Select KPI for detailed view
selected_kpi = st.selectbox(
    "Select KPI for detailed analysis:",
    list(current_values.keys())
)

# Create detailed chart
fig = px.line(
    df, 
    x='Date', 
    y=selected_kpi,
    title=f'{selected_kpi} - 90-Day Trend'
)
fig.update_layout(
    height=400,
    xaxis_title="Date",
    yaxis_title=selected_kpi,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
)
st.plotly_chart(fig, use_container_width=True)

# Performance summary
st.markdown("---")
st.subheader("Performance Summary")

summary_col1, summary_col2, summary_col3 = st.columns(3)

with summary_col1:
    excellent_count = sum(1 for level in performance_levels.values() if level == 'Excellent')
    good_count = sum(1 for level in performance_levels.values() if level == 'Good')
    
    st.metric("KPIs Exceeding Target", excellent_count)
    st.metric("KPIs Meeting Target", good_count)

with summary_col2:
    average_count = sum(1 for level in performance_levels.values() if level == 'Average')
    poor_count = sum(1 for level in performance_levels.values() if level == 'Poor')
    
    st.metric("KPIs Near Target", average_count)
    st.metric("KPIs Below Target", poor_count)

with summary_col3:
    overall_performance = (excellent_count + good_count * 0.8) / len(performance_levels) * 100
    st.metric("Overall Performance Score", f"{overall_performance:.1f}%")
    
    # Performance indicator
    if overall_performance >= 90:
        performance_status = "Excellent"
    elif overall_performance >= 80:
        performance_status = "Good"
    elif overall_performance >= 70:
        performance_status = "Average"
    else:
        performance_status = "Needs Improvement"
    
    st.metric("Performance Status", performance_status)

# Add sidebar with filters
with st.sidebar:
    st.header("Dashboard Filters")
    
    st.subheader("Date Range")
    start_date = st.date_input(
        "Start Date",
        value=datetime.now() - timedelta(days=90)
    )
    end_date = st.date_input(
        "End Date",
        value=datetime.now()
    )
    
    st.subheader("Performance Thresholds")
    excellent_threshold = st.slider("Excellent Performance (%)", 90, 100, 95)
    good_threshold = st.slider("Good Performance (%)", 80, 95, 85)
    
    st.subheader("About")
    st.info(
        "This dashboard displays key banking performance indicators "
        "with trend analysis over the last 90 days. Each KPI card shows "
        "the current value, percentage change from previous period, "
        "and performance against target."
    )
