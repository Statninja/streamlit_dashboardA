import streamlit as st
import pandas as pd
import numpy as np
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
st.sidebar.markdown("<h1 style='color: #000080;'>📊 Navigation</h1>", unsafe_allow_html=True)
section = st.sidebar.radio("", ["🏠 Dashboard Overview", "🎯 Audience Generation", "📈 Campaign Analytics", "🚀 Campaign Execution"])

# Main header
st.markdown("<h1 class='main-header'>🏦 Banking Campaign Analytics Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #A100FF; font-size: 1.2rem;'>Generación de Audiencias & Programación de Campañas</p>", unsafe_allow_html=True)

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
        st.bar_chart(income_dist)
        
        # Additional data table
        st.markdown("#### 👥 Customer Demographics")
        demo_summary = df_customers.groupby('income_segment').agg({
            'age': 'mean',
            'total_balance': 'mean',
            'product_holdings': 'mean'
        }).round(1)
        st.dataframe(demo_summary)
    
    with col2:
        st.markdown("#### 📈 Campaign Performance Overview")
        campaign_perf = df_campaigns.groupby('campaign_name')['conversion_rate'].mean().sort_values(ascending=False)
        
        # Display as metric cards
        for campaign, rate in campaign_perf.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{campaign}**")
            with col2:
                st.metric("Rate", f"{rate*100:.1f}%")
        
        st.markdown("#### 🌍 Regional Distribution")
        region_dist = df_customers['region'].value_counts()
        st.dataframe(region_dist)

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
        
        if st.button("🔍 Generate Audience", type="primary", use_container_width=True):
            # Apply filters
            filtered_audience = df_customers[
                (df_customers['total_balance'] >= min_balance) &
                (df_customers['age'] <= max_age) &
                (df_customers['income_segment'].isin(income_levels)) &
                (df_customers['region'].isin(regions)) &
                (df_customers['product_holdings'] >= min_products) &
                (df_customers['campaign_eligible'])
            ].copy()
            st.session_state.filtered_audience = filtered_audience
            st.success(f"✅ Audience generated: {len(filtered_audience)} customers")
    
    with col2:
        st.markdown("#### 📋 Generated Audience Summary")
        
        if 'filtered_audience' in st.session_state and len(st.session_state.filtered_audience) > 0:
            audience = st.session_state.filtered_audience
            
            # Audience metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Audience Size", f"{len(audience):,}")
            with col2:
                st.metric("Avg Balance", f"€{audience['total_balance'].mean():,.0f}")
            with col3:
                st.metric("Avg Products", f"{audience['product_holdings'].mean():.1f}")
            with col4:
                st.metric("Avg Age", f"{audience['age'].mean():.1f}")
            
            # Audience composition
            st.markdown("##### 📊 Audience Composition")
            
            tab1, tab2, tab3 = st.tabs(["Demographics", "Financial", "Raw Data"])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Income Distribution**")
                    income_counts = audience['income_segment'].value_counts()
                    st.bar_chart(income_counts)
                
                with col2:
                    st.markdown("**Regional Distribution**")
                    region_counts = audience['region'].value_counts()
                    st.bar_chart(region_counts)
            
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Balance Distribution**")
                    st.bar_chart(audience['total_balance'].value_counts(bins=10))
                
                with col2:
                    st.markdown("**Product Holdings**")
                    product_counts = audience['product_holdings'].value_counts().sort_index()
                    st.bar_chart(product_counts)
            
            with tab3:
                st.dataframe(audience[['customer_id', 'age', 'income_segment', 'region', 'total_balance', 'product_holdings']])
            
            # Export option
            st.markdown("##### 📤 Export Audience")
            if st.button("Download Audience as CSV", use_container_width=True):
                csv = audience.to_csv(index=False)
                st.download_button(
                    label="Download CSV File",
                    data=csv,
                    file_name=f"campaign_audience_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("👆 Configure your audience criteria and click 'Generate Audience' to see results")

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
    st.markdown("#### 📊 Monthly Performance Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Conversion Rate Trend**")
        # Create a simple line chart using st.line_chart
        conv_data = campaign_data.set_index('month')[['conversion_rate']]
        conv_data['conversion_rate'] = conv_data['conversion_rate'] * 100
        st.line_chart(conv_data)
    
    with col2:
        st.markdown("**Revenue Trend**")
        revenue_data = campaign_data.set_index('month')[['revenue_generated']]
        st.line_chart(revenue_data)
    
    # Campaign comparison
    st.markdown("#### 📈 Cross-Campaign Comparison")
    
    comparison_metric = st.selectbox(
        "Select Metric for Comparison:", 
        ["conversion_rate", "revenue_generated", "cost_per_acquisition", "actual_reach"]
    )
    
    # Aggregate data for comparison
    campaign_comparison = df_campaigns.groupby('campaign_name')[comparison_metric].mean().sort_values(ascending=False)
    st.bar_chart(campaign_comparison)
    
    # Detailed data table
    st.markdown("#### 📋 Detailed Campaign Data")
    st.dataframe(campaign_data)

elif section == "🚀 Campaign Execution":
    st.markdown("### 🚀 Campaign Programming & Execution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Campaign Setup")
        
        campaign_name = st.text_input("Campaign Name", "Q1_2024_CreditCard_Promo")
        
        st.markdown("**Execution Parameters:**")
        execution_date = st.date_input("Execution Date", datetime.now() + timedelta(days=7))
        channel = st.selectbox("Communication Channel", ["Email", "SMS", "Push Notification", "Direct Mail"])
        priority = st.select_slider("Campaign Priority", ["Low", "Medium", "High"], value="Medium")
        
        st.markdown("**Audience Selection:**")
        if 'filtered_audience' in st.session_state:
            audience_size = len(st.session_state.filtered_audience)
            st.success(f"✅ Pre-generated audience available: {audience_size} customers")
            use_existing = st.checkbox("Use pre-generated audience", value=True)
        else:
            st.warning("⚠️ No audience generated yet")
            use_existing = False
        
        message_template = st.text_area(
            "Campaign Message Template", 
            "Estimado cliente, tenemos una oferta exclusiva para usted...\n\nComo cliente preferente, puede acceder a [producto] con condiciones especiales.\n\n¡No pierda esta oportunidad!",
            height=100
        )
        
        if st.button("🚀 Schedule Campaign", type="primary", use_container_width=True):
            st.success(f"✅ Campaign '{campaign_name}' scheduled for {execution_date}")
            st.balloons()
            
            # Show next steps
            st.markdown("**Next Steps:**")
            st.write("1. ✅ Campaign scheduled in system")
            st.write("2. 📧 Communications team notified")
            st.write("3. 📊 Tracking codes generated")
            st.write("4. 🎯 Ready for execution")
    
    with col2:
        st.markdown("#### 📊 Execution Dashboard")
        
        # Mock execution metrics
        st.markdown("**Campaign Pipeline**")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Scheduled", "12", "+2")
        with col2:
            st.metric("Ready", "5", "0")
        with col3:
            st.metric("In Progress", "3", "-1")
        with col4:
            st.metric("Completed", "24", "+4")
        
        st.markdown("**Recent Campaign Executions**")
        
        # Campaign execution history
        execution_history = [
            {"Campaign": "Credit Card Q4", "Status": "✅ Completed", "Date": "2024-01-15", "Reach": "15,234", "Conv Rate": "4.2%"},
            {"Campaign": "Personal Loan Promo", "Status": "🔄 In Progress", "Date": "2024-01-14", "Reach": "8,567", "Conv Rate": "3.8%"},
            {"Campaign": "Mortgage Special", "Status": "✅ Completed", "Date": "2024-01-13", "Reach": "12,890", "Conv Rate": "2.1%"},
            {"Campaign": "Investment Fund", "Status": "⏸️ Paused", "Date": "2024-01-12", "Reach": "5,432", "Conv Rate": "5.6%"},
        ]
        
        for campaign in execution_history:
            with st.container():
                st.write(f"**{campaign['Campaign']}**")
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    st.write(campaign['Status'])
                with col2:
                    st.write(campaign['Date'])
                with col3:
                    st.write(f"Reach: {campaign['Reach']} | Conv: {campaign['Conv Rate']}")
                st.divider()

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #000080;'>"
    "Built with Streamlit for Accenture Banking Analytics | "
    "Generación de Audiencias & Programación de Campañas"
    "</p>", 
    unsafe_allow_html=True
)
