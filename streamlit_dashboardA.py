import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io

# Set page configuration with royal blue theme
st.set_page_config(
    page_title="Banking Campaign Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for royal blue background and Helvetica font
st.markdown("""
<style>
    .main {
        background-color: #1E3A8A;
        color: white;
        font-family: 'Helvetica', Arial, sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #1E3A8A 0%, #3730A3 50%, #1E40AF 100%);
        font-family: 'Helvetica', Arial, sans-serif;
    }
    .main-header {
        font-size: 2.8rem;
        color: white;
        font-weight: bold;
        margin-bottom: 1rem;
        font-family: 'Helvetica', Arial, sans-serif;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .section-header {
        font-size: 1.8rem;
        color: white;
        font-weight: bold;
        margin-bottom: 1rem;
        font-family: 'Helvetica', Arial, sans-serif;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 1rem;
        color: white;
    }
    .stMetric {
        background: rgba(255, 255, 255, 0.15);
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    .sidebar .sidebar-content {
        background: rgba(30, 58, 138, 0.9);
        backdrop-filter: blur(10px);
    }
    div[data-testid="stSidebarNav"] {
        background: rgba(255, 255, 255, 0.1);
    }
    .map-container {
        background: rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .region-card {
        background: rgba(255, 255, 255, 0.15);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #FF6B6B;
    }
    .finance-chart-container {
        background: rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Generate enhanced sample data with geographic information
def generate_sample_data():
    np.random.seed(42)
    
    # Spanish regions data
    spanish_regions = {
        'Madrid': {'customers': 180, 'conversion': 4.8, 'revenue': 450000, 'aum': 45000000},
        'Cataluña': {'customers': 160, 'conversion': 4.2, 'revenue': 380000, 'aum': 38000000},
        'Andalucía': {'customers': 150, 'conversion': 3.9, 'revenue': 320000, 'aum': 32000000},
        'Valencia': {'customers': 120, 'conversion': 4.1, 'revenue': 280000, 'aum': 28000000},
        'País Vasco': {'customers': 90, 'conversion': 5.2, 'revenue': 220000, 'aum': 22000000},
        'Galicia': {'customers': 80, 'conversion': 3.8, 'revenue': 180000, 'aum': 18000000},
        'Castilla y León': {'customers': 85, 'conversion': 3.6, 'revenue': 190000, 'aum': 19000000},
        'Aragón': {'customers': 70, 'conversion': 4.0, 'revenue': 160000, 'aum': 16000000},
        'Canarias': {'customers': 65, 'conversion': 3.7, 'revenue': 150000, 'aum': 15000000}
    }
    
    # European countries data
    european_countries = {
        'Spain': {'customers': 1000, 'conversion': 4.2, 'revenue': 2450000, 'aum': 245000000},
        'France': {'customers': 850, 'conversion': 3.8, 'revenue': 1980000, 'aum': 198000000},
        'Germany': {'customers': 920, 'conversion': 4.5, 'revenue': 2150000, 'aum': 215000000},
        'Italy': {'customers': 780, 'conversion': 3.9, 'revenue': 1820000, 'aum': 182000000},
        'UK': {'customers': 890, 'conversion': 4.1, 'revenue': 2080000, 'aum': 208000000},
        'Portugal': {'customers': 450, 'conversion': 3.5, 'revenue': 1250000, 'aum': 125000000}
    }
    
    # Customer base data
    customers = []
    for i in range(1000):
        region = np.random.choice(list(spanish_regions.keys()))
        customers.append({
            'customer_id': f'CUST_{i:04d}',
            'age': np.random.randint(18, 70),
            'income_segment': np.random.choice(['Low', 'Medium', 'High'], p=[0.3, 0.5, 0.2]),
            'product_holdings': np.random.randint(1, 6),
            'last_transaction_days': np.random.randint(1, 90),
            'total_balance': np.random.normal(5000, 3000),
            'risk_profile': np.random.choice(['Low', 'Medium', 'High'], p=[0.6, 0.3, 0.1]),
            'region': region,
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
    
    # Financial performance data - FIXED: Use numeric months for charts
    financial_data = {
        'month': list(range(1, 13)),
        'revenue': np.random.randint(80000, 150000, 12),
        'profit': np.random.randint(20000, 60000, 12),
        'aum': np.random.randint(8000000, 12000000, 12),
        'new_clients': np.random.randint(80, 200, 12)
    }
    df_financial = pd.DataFrame(financial_data)
    
    return df_customers, df_campaigns, df_financial, spanish_regions, european_countries

# Initialize session state for data
if 'data_loaded' not in st.session_state:
    st.session_state.df_customers, st.session_state.df_campaigns, st.session_state.df_financial, st.session_state.spanish_regions, st.session_state.european_countries = generate_sample_data()
    st.session_state.data_loaded = True

df_customers = st.session_state.df_customers
df_campaigns = st.session_state.df_campaigns
df_financial = st.session_state.df_financial
spanish_regions = st.session_state.spanish_regions
european_countries = st.session_state.european_countries

# Create geographic visualization using Streamlit components (no HTML)
def display_geographic_data(regions_data, title):
    st.markdown(f"#### {title}")
    
    # Convert to DataFrame for better display
    geo_data = []
    for region, data in regions_data.items():
        geo_data.append({
            'Region': region,
            'Customers': data['customers'],
            'Conversion %': data['conversion'],
            'Revenue (€)': f"€{data['revenue']:,}",
            'AUM (€)': f"€{data['aum']:,}"
        })
    
    df_geo = pd.DataFrame(geo_data)
    st.dataframe(df_geo, use_container_width=True)
    
    # Display conversion rates as a simple bar chart
    st.markdown(f"**{title} - Conversion Rates**")
    conv_data = pd.DataFrame([{'Region': k, 'Conversion %': v['conversion']} for k, v in regions_data.items()])
    st.bar_chart(conv_data.set_index('Region'))

# Sidebar navigation
st.sidebar.markdown("<h1 style='color: white; font-family: Helvetica;'>📊 Navigation</h1>", unsafe_allow_html=True)
section = st.sidebar.radio("", 
    ["🏠 Dashboard Overview", "🎯 Audience Generation", "📈 Campaign Analytics", "🗺️ Geographic Analysis", "🚀 Campaign Execution"])

# Main header
st.markdown("<h1 class='main-header'>🏦 Banking Campaign Analytics Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: white; font-size: 1.2rem; font-family: Helvetica;'>Generación de Audiencias & Programación de Campañas con PySpark</p>", unsafe_allow_html=True)

if section == "🏠 Dashboard Overview":
    st.markdown("<h2 class='section-header'>📈 Executive Summary</h2>", unsafe_allow_html=True)
    
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
    
    # Charts and Data Table
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Customer Data Table")
        st.dataframe(df_customers[['customer_id', 'age', 'income_segment', 'region', 'total_balance', 'product_holdings']].head(8))
        
        st.markdown("#### 💰 Financial Performance")
        
        # Revenue trend - FIXED: Use numeric data
        st.markdown("**Monthly Revenue Trend**")
        revenue_data = df_financial[['month', 'revenue']].set_index('month')
        st.line_chart(revenue_data)
        
        # Profit trend
        st.markdown("**Monthly Profit Trend**")
        profit_data = df_financial[['month', 'profit']].set_index('month')
        st.line_chart(profit_data)
    
    with col2:
        st.markdown("#### 📊 Customer Distribution by Income Segment")
        income_dist = df_customers['income_segment'].value_counts()
        st.bar_chart(income_dist)
        
        st.markdown("#### 📈 Campaign Performance Overview")
        campaign_perf = df_campaigns.groupby('campaign_name')['conversion_rate'].mean().sort_values(ascending=False)
        
        # Display campaign performance as metrics
        for campaign, rate in campaign_perf.items():
            col_c1, col_c2 = st.columns([3, 1])
            with col_c1:
                st.write(f"**{campaign}**")
            with col_c2:
                st.metric("Rate", f"{rate*100:.1f}%")
        
        st.markdown("#### 📊 Assets Under Management")
        aum_data = df_financial[['month', 'aum']].set_index('month')
        st.area_chart(aum_data)

elif section == "🎯 Audience Generation":
    st.markdown("<h2 class='section-header'>🎯 Campaign Audience Generation</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### 🔧 Audience Criteria")
        
        campaign_type = st.selectbox(
            "Select Campaign Type:",
            ["Credit Card Premium", "Personal Loan", "Mortgage", "Investment Fund", "Insurance"]
        )
        
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
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Audience Size", f"{len(audience):,}")
            with col2:
                st.metric("Avg Balance", f"€{audience['total_balance'].mean():,.0f}")
            with col3:
                st.metric("Avg Products", f"{audience['product_holdings'].mean():.1f}")
            with col4:
                st.metric("Avg Age", f"{audience['age'].mean():.1f}")
            
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
                    st.markdown("**Balance Ranges**")
                    # Create simple balance ranges
                    balance_data = pd.cut(audience['total_balance'], 
                                        bins=[0, 2000, 4000, 6000, 8000, 20000], 
                                        labels=['0-2K', '2K-4K', '4K-6K', '6K-8K', '8K+'])
                    balance_counts = balance_data.value_counts()
                    st.bar_chart(balance_counts)
                
                with col2:
                    st.markdown("**Product Holdings**")
                    product_counts = audience['product_holdings'].value_counts().sort_index()
                    st.bar_chart(product_counts)
            
            with tab3:
                st.dataframe(audience[['customer_id', 'age', 'income_segment', 'region', 'total_balance', 'product_holdings']].head(10))
            
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
    st.markdown("<h2 class='section-header'>📈 Campaign Performance Analytics</h2>", unsafe_allow_html=True)
    
    selected_campaign = st.selectbox(
        "Select Campaign for Analysis:",
        df_campaigns['campaign_name'].unique()
    )
    
    campaign_data = df_campaigns[df_campaigns['campaign_name'] == selected_campaign]
    
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
    
    st.markdown("#### 📊 Monthly Performance Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Conversion Rate Trend**")
        conv_data = campaign_data[['month', 'conversion_rate']].set_index('month')
        conv_data['conversion_rate'] = conv_data['conversion_rate'] * 100
        st.line_chart(conv_data)
    
    with col2:
        st.markdown("**Revenue Trend**")
        revenue_data = campaign_data[['month', 'revenue_generated']].set_index('month')
        st.line_chart(revenue_data)
    
    st.markdown("#### 📈 Cross-Campaign Comparison")
    
    comparison_metric = st.selectbox(
        "Select Metric for Comparison:", 
        ["conversion_rate", "revenue_generated", "cost_per_acquisition", "actual_reach"]
    )
    
    campaign_comparison = df_campaigns.groupby('campaign_name')[comparison_metric].mean().sort_values(ascending=False)
    st.bar_chart(campaign_comparison)

elif section == "🗺️ Geographic Analysis":
    st.markdown("<h2 class='section-header'>🗺️ Geographic Analysis</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🇪🇸 Spain Regional Analysis")
        
        # Display Spain regions using fixed function
        display_geographic_data(spanish_regions, "Spanish Regions Performance")
        
        # Additional Spain metrics
        st.markdown("#### 📊 Spain Performance Summary")
        total_spain_customers = sum(region['customers'] for region in spanish_regions.values())
        avg_spain_conversion = np.mean([region['conversion'] for region in spanish_regions.values()])
        total_spain_revenue = sum(region['revenue'] for region in spanish_regions.values())
        total_spain_aum = sum(region['aum'] for region in spanish_regions.values())
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Customers", f"{total_spain_customers:,}")
        with col2:
            st.metric("Avg Conversion", f"{avg_spain_conversion:.1f}%")
        with col3:
            st.metric("Total Revenue", f"€{total_spain_revenue:,}")
        with col4:
            st.metric("Total AUM", f"€{total_spain_aum:,}")
    
    with col2:
        st.markdown("#### 🇪🇺 European Market Analysis")
        
        # Display European countries using fixed function
        display_geographic_data(european_countries, "European Markets Performance")
        
        # Additional Europe metrics
        st.markdown("#### 📊 Europe Performance Summary")
        total_europe_customers = sum(country['customers'] for country in european_countries.values())
        avg_europe_conversion = np.mean([country['conversion'] for country in european_countries.values()])
        total_europe_revenue = sum(country['revenue'] for country in european_countries.values())
        total_europe_aum = sum(country['aum'] for country in european_countries.values())
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Customers", f"{total_europe_customers:,}")
        with col2:
            st.metric("Avg Conversion", f"{avg_europe_conversion:.1f}%")
        with col3:
            st.metric("Total Revenue", f"€{total_europe_revenue:,}")
        with col4:
            st.metric("Total AUM", f"€{total_europe_aum:,}")

elif section == "🚀 Campaign Execution":
    st.markdown("<h2 class='section-header'>🚀 Campaign Programming & Execution</h2>", unsafe_allow_html=True)
    
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
            
            st.markdown("**Next Steps:**")
            st.write("1. ✅ Campaign scheduled in system")
            st.write("2. 📧 Communications team notified")
            st.write("3. 📊 Tracking codes generated")
            st.write("4. 🎯 Ready for execution")
    
    with col2:
        st.markdown("#### 📊 Execution Dashboard")
        
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

# PySpark Integration Section
st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color: white; font-family: Helvetica;'>⚡ PySpark Integration</h3>", unsafe_allow_html=True)

if st.sidebar.button("Simulate PySpark Processing"):
    with st.sidebar.expander("PySpark Results"):
        st.write("**Data Processing with PySpark:**")
        st.write("✅ Customer data loaded")
        st.write("✅ Audience segmentation completed")
        st.write("✅ Campaign analytics processed")
        st.write("✅ Geographic analysis generated")
        st.write(f"📊 Total records: {len(df_customers):,}")
        st.write(f"🎯 Eligible for campaigns: {len(df_customers[df_customers['campaign_eligible']]):,}")

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: white; font-family: Helvetica;'>"
    "Built with Streamlit & PySpark for Accenture Banking Analytics | "
    "Generación de Audiencias & Programación de Campañas"
    "</p>", 
    unsafe_allow_html=True
)
