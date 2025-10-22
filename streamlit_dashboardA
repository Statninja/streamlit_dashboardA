import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

# Set page configuration
st.set_page_config(
    page_title="Banking Campaign Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Accenture colors
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #000080;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .accenture-blue {
        color: #000080;
    }
    .accenture-violet {
        color: #A100FF;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #000080;
        margin-bottom: 1rem;
    }
    .sidebar .sidebar-content {
        background-color: #000080;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Generate sample banking data
def generate_sample_data():
    np.random.seed(42)
    
    # Customer base data
    customers = []
    for i in range(1000):
        customers.append({
            'customer_id': f'CUST_{i:04d}',
            'age': np.random.randint(18, 70),
            'income_segment': np.random.choice(['Low', 'Medium', 'High'], p=[0.3, 0.5, 0.2]),
            'product_holdings': np.random.randint(1, 6),
            'last_transaction_days': np.random.randint(1, 90),
            'total_balance': np.random.normal(5000, 3000),
            'risk_profile': np.random.choice(['Low', 'Medium', 'High'], p=[0.6, 0.3, 0.1]),
            'region': np.random.choice(['North', 'South', 'East', 'West', 'Central']),
            'campaign_eligible': np.random.choice([True, False], p=[0.7, 0.3])
        })
    
    df_customers = pd.DataFrame(customers)
    df_customers['total_balance'] = df_customers['total_balance'].clip(lower=0)
    
    # Campaign performance data
    campaigns = ['Credit Card Premium', 'Personal Loan', 'Mortgage', 'Investment Fund', 'Insurance']
    campaign_data = []
    
    for campaign in campaigns:
        for month in range(1, 13):
            campaign_data.append({
                'campaign_name': campaign,
                'month': month,
                'target_audience': np.random.randint(500, 2000),
                'actual_reach': np.random.randint(400, 1900),
                'conversion_rate': np.random.uniform(0.02, 0.15),
                'revenue_generated': np.random.uniform(5000, 50000),
                'cost_per_acquisition': np.random.uniform(50, 200)
            })
    
    df_campaigns = pd.DataFrame(campaign_data)
    
    return df_customers, df_campaigns

# Initialize session state for data
if 'df_customers' not in st.session_state:
    st.session_state.df_customers, st.session_state.df_campaigns = generate_sample_data()

df_customers = st.session_state.df_customers
df_campaigns = st.session_state.df_campaigns

# Sidebar navigation
st.sidebar.markdown("<h1 style='color: white;'>📊 Navigation</h1>", unsafe_allow_html=True)
section = st.sidebar.radio("", ["🏠 Dashboard Overview", "🎯 Audience Generation", "📈 Campaign Analytics", "🚀 Campaign Execution"])

# Main header
st.markdown("<h1 class='main-header'>🏦 Banking Campaign Analytics Dashboard</h1>", unsafe_allow_html=True)

if section == "🏠 Dashboard Overview":
    st.markdown("### 📈 Executive Summary")
    
    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_customers = len(df_customers)
        eligible_customers = len(df_customers[df_customers['campaign_eligible']])
        st.metric(
            label="Total Customers", 
            value=f"{total_customers:,}",
            delta=f"{eligible_customers} eligible"
        )
    
    with col2:
        avg_balance = df_customers['total_balance'].mean()
        st.metric(
            label="Average Balance", 
            value=f"€{avg_balance:,.0f}",
            delta="+5.2%"
        )
    
    with col3:
        total_revenue = df_campaigns['revenue_generated'].sum()
        st.metric(
            label="Total Revenue", 
            value=f"€{total_revenue:,.0f}",
            delta="+12.3%"
        )
    
    with col4:
        avg_conversion = df_campaigns['conversion_rate'].mean() * 100
        st.metric(
            label="Avg Conversion Rate", 
            value=f"{avg_conversion:.1f}%",
            delta="+2.1%"
        )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Customer Distribution by Income Segment")
        income_dist = df_customers['income_segment'].value_counts()
        fig_income = px.pie(
            values=income_dist.values,
            names=income_dist.index,
            color=income_dist.index,
            color_discrete_map={'Low':'#000080', 'Medium':'#A100FF', 'High':'#4169E1'}
        )
        st.plotly_chart(fig_income, use_container_width=True)
    
    with col2:
        st.markdown("#### 📈 Campaign Performance Overview")
        campaign_perf = df_campaigns.groupby('campaign_name')['conversion_rate'].mean().sort_values(ascending=False)
        fig_campaign = px.bar(
            x=campaign_perf.values * 100,
            y=campaign_perf.index,
            orientation='h',
            color=campaign_perf.values,
            color_continuous_scale=['#000080', '#A100FF']
        )
        fig_campaign.update_layout(xaxis_title="Conversion Rate (%)", yaxis_title="Campaign")
        st.plotly_chart(fig_campaign, use_container_width=True)

elif section == "🎯 Audience Generation":
    st.markdown("### 🎯 Campaign Audience Generation")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### 🔧 Audience Criteria")
        
        # Campaign type selection
        campaign_type = st.selectbox(
            "Select Campaign Type:",
            ["Credit Card Premium", "Personal Loan", "Mortgage", "Investment Fund", "Insurance"]
        )
        
        # Audience filters
        st.markdown("**Audience Filters:**")
        min_balance = st.slider("Minimum Balance (€)", 0, 10000, 1000, step=500)
        max_age = st.slider("Maximum Age", 18, 70, 65)
        income_levels = st.multiselect(
            "Income Segments:",
            ["Low", "Medium", "High"],
            default=["Medium", "High"]
        )
        
        regions = st.multiselect(
            "Regions:",
            df_customers['region'].unique(),
            default=df_customers['region'].unique()
        )
        
        min_products = st.slider("Minimum Products Held", 1, 5, 1)
        
        if st.button("🔍 Generate Audience", type="primary"):
            # Apply filters
            filtered_audience = df_customers[
                (df_customers['total_balance'] >= min_balance) &
                (df_customers['age'] <= max_age) &
                (df_customers['income_segment'].isin(income_levels)) &
                (df_customers['region'].isin(regions)) &
                (df_customers['product_holdings'] >= min_products) &
                (df_customers['campaign_eligible'])
            ]
            st.session_state.filtered_audience = filtered_audience
    
    with col2:
        st.markdown("#### 📋 Generated Audience Summary")
        
        if 'filtered_audience' in st.session_state:
            audience = st.session_state.filtered_audience
            
            # Audience metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Audience Size", f"{len(audience):,}")
            with col2:
                st.metric("Avg Balance", f"€{audience['total_balance'].mean():,.0f}")
            with col3:
                st.metric("Avg Products", f"{audience['product_holdings'].mean():.1f}")
            
            # Audience composition charts
            tab1, tab2 = st.tabs(["📊 Demographics", "📈 Financial Profile"])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    age_fig = px.histogram(audience, x='age', nbins=20, 
                                         color_discrete_sequence=['#000080'])
                    st.plotly_chart(age_fig, use_container_width=True)
                
                with col2:
                    region_fig = px.bar(audience['region'].value_counts(), 
                                      color_discrete_sequence=['#A100FF'])
                    st.plotly_chart(region_fig, use_container_width=True)
            
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    balance_fig = px.box(audience, y='total_balance', 
                                       color_discrete_sequence=['#000080'])
                    st.plotly_chart(balance_fig, use_container_width=True)
                
                with col2:
                    income_fig = px.pie(audience, names='income_segment',
                                      color_discrete_map={'Low':'#000080', 'Medium':'#A100FF', 'High':'#4169E1'})
                    st.plotly_chart(income_fig, use_container_width=True)
            
            # Export option
            if st.button("📤 Export Audience List"):
                csv = audience.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"campaign_audience_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

elif section == "📈 Campaign Analytics":
    st.markdown("### 📈 Campaign Performance Analytics")
    
    # Campaign selection
    selected_campaign = st.selectbox(
        "Select Campaign for Analysis:",
        df_campaigns['campaign_name'].unique()
    )
    
    campaign_data = df_campaigns[df_campaigns['campaign_name'] == selected_campaign]
    
    # Campaign KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_revenue = campaign_data['revenue_generated'].sum()
        st.metric("Total Revenue", f"€{total_revenue:,.0f}")
    
    with col2:
        avg_conversion = campaign_data['conversion_rate'].mean() * 100
        st.metric("Avg Conversion", f"{avg_conversion:.1f}%")
    
    with col3:
        total_reach = campaign_data['actual_reach'].sum()
        st.metric("Total Reach", f"{total_reach:,}")
    
    with col4:
        avg_cpa = campaign_data['cost_per_acquisition'].mean()
        st.metric("Avg CPA", f"€{avg_cpa:.0f}")
    
    # Performance charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Monthly Conversion Rate")
        fig_conv = px.line(campaign_data, x='month', y='conversion_rate',
                         color_discrete_sequence=['#A100FF'])
        fig_conv.update_layout(yaxis_tickformat=".1%")
        st.plotly_chart(fig_conv, use_container_width=True)
    
    with col2:
        st.markdown("#### 💰 Revenue Trend")
        fig_rev = px.area(campaign_data, x='month', y='revenue_generated',
                        color_discrete_sequence=['#000080'])
        st.plotly_chart(fig_rev, use_container_width=True)
    
    # Comparative analysis
    st.markdown("#### 📈 Campaign Comparison")
    comparison_metric = st.selectbox("Comparison Metric:", 
                                   ["conversion_rate", "revenue_generated", "cost_per_acquisition"])
    
    fig_compare = px.box(df_campaigns, x='campaign_name', y=comparison_metric,
                       color='campaign_name',
                       color_discrete_sequence=['#000080', '#A100FF', '#4169E1', '#8A2BE2', '#4B0082'])
    st.plotly_chart(fig_compare, use_container_width=True)

elif section == "🚀 Campaign Execution":
    st.markdown("### 🚀 Campaign Programming & Execution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Campaign Setup")
        
        campaign_name = st.text_input("Campaign Name", "New_Campaign_2024")
        
        st.markdown("**Execution Parameters:**")
        execution_date = st.date_input("Execution Date", datetime.now() + timedelta(days=7))
        channel = st.selectbox("Communication Channel", ["Email", "SMS", "Push Notification", "Direct Mail"])
        
        st.markdown("**Audience Selection:**")
        if 'filtered_audience' in st.session_state:
            audience_size = len(st.session_state.filtered_audience)
            st.info(f"📊 Selected Audience: {audience_size} customers")
        else:
            st.warning("⚠️ No audience generated yet. Please generate an audience first.")
        
        message_template = st.text_area("Campaign Message", "Dear customer, we have a special offer for you...")
        
        if st.button("🚀 Schedule Campaign", type="primary"):
            st.success(f"✅ Campaign '{campaign_name}' scheduled for {execution_date}")
            st.balloons()
    
    with col2:
        st.markdown("#### 📊 Execution Dashboard")
        
        # Mock execution metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Scheduled Campaigns", "12", "+2")
            st.metric("Ready for Execution", "5", "0")
        with col2:
            st.metric("In Progress", "3", "-1")
            st.metric("Completed Today", "4", "+1")
        
        st.markdown("**Recent Campaigns:**")
        
        # Mock campaign execution log
        execution_log = [
            {"campaign": "Credit Card Q4", "status": "✅ Completed", "date": "2024-01-15", "reach": "15,234"},
            {"campaign": "Personal Loan Promo", "status": "🔄 In Progress", "date": "2024-01-14", "reach": "8,567"},
            {"campaign": "Mortgage Special", "status": "✅ Completed", "date": "2024-01-13", "reach": "12,890"},
            {"campaign": "Investment Fund", "status": "⏸️ Paused", "date": "2024-01-12", "reach": "5,432"},
        ]
        
        for log in execution_log:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{log['campaign']}**")
                with col2:
                    st.write(log['status'])
                with col3:
                    st.write(log['date'])
                st.write(f"Reach: {log['reach']} customers")
                st.divider()

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #000080;'>Built with Streamlit for Accenture Banking Analytics Team</p>", 
            unsafe_allow_html=True)
