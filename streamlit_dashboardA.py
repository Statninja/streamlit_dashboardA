import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
import pydeck as pdk

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
</style>
""", unsafe_allow_html=True)

# Generate enhanced sample data with geographic information
def generate_sample_data():
    np.random.seed(42)
    
    # Spanish regions and coordinates
    spanish_regions = {
        'Madrid': {'lat': 40.4168, 'lon': -3.7038, 'customers': 180},
        'Cataluña': {'lat': 41.3874, 'lon': 2.1686, 'customers': 160},
        'Andalucía': {'lat': 37.3891, 'lon': -5.9845, 'customers': 150},
        'Valencia': {'lat': 39.4699, 'lon': -0.3763, 'customers': 120},
        'País Vasco': {'lat': 43.2630, 'lon': -2.9350, 'customers': 90},
        'Galicia': {'lat': 42.5751, 'lon': -8.1339, 'customers': 80},
        'Castilla y León': {'lat': 41.8357, 'lon': -4.3976, 'customers': 85},
        'Aragón': {'lat': 41.6488, 'lon': -0.8891, 'customers': 70},
        'Canarias': {'lat': 28.2916, 'lon': -16.6291, 'customers': 65}
    }
    
    # European countries data
    european_countries = {
        'Spain': {'lat': 40.4637, 'lon': -3.7492, 'customers': 1000, 'conversion': 4.2},
        'France': {'lat': 46.6034, 'lon': 1.8883, 'customers': 850, 'conversion': 3.8},
        'Germany': {'lat': 51.1657, 'lon': 10.4515, 'customers': 920, 'conversion': 4.5},
        'Italy': {'lat': 41.8719, 'lon': 12.5674, 'customers': 780, 'conversion': 3.9},
        'UK': {'lat': 55.3781, 'lon': -3.4360, 'customers': 890, 'conversion': 4.1},
        'Portugal': {'lat': 39.3999, 'lon': -8.2245, 'customers': 450, 'conversion': 3.5}
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
            'latitude': spanish_regions[region]['lat'] + np.random.uniform(-0.5, 0.5),
            'longitude': spanish_regions[region]['lon'] + np.random.uniform(-0.5, 0.5),
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
    
    # Funnel data
    funnel_data = {
        'stage': ['Awareness', 'Interest', 'Consideration', 'Conversion', 'Loyalty'],
        'count': [10000, 6500, 3200, 1500, 800],
        'percentage': [100, 65, 32, 15, 8]
    }
    df_funnel = pd.DataFrame(funnel_data)
    
    return df_customers, df_campaigns, df_funnel, spanish_regions, european_countries

# Initialize session state for data
if 'data_loaded' not in st.session_state:
    st.session_state.df_customers, st.session_state.df_campaigns, st.session_state.df_funnel, st.session_state.spanish_regions, st.session_state.european_countries = generate_sample_data()
    st.session_state.data_loaded = True

df_customers = st.session_state.df_customers
df_campaigns = st.session_state.df_campaigns
df_funnel = st.session_state.df_funnel
spanish_regions = st.session_state.spanish_regions
european_countries = st.session_state.european_countries

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
        st.dataframe(df_customers[['customer_id', 'age', 'income_segment', 'region', 'total_balance', 'product_holdings']].head(10))
        
        st.markdown("#### 📈 Funnel Analysis")
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#1E3A8A')
        ax.set_facecolor('#1E3A8A')
        
        # Create funnel chart
        stages = df_funnel['stage']
        percentages = df_funnel['percentage']
        
        bars = ax.barh(stages, percentages, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
        ax.set_xlabel('Conversion Rate (%)', color='white', fontfamily='Helvetica')
        ax.set_ylabel('Funnel Stage', color='white', fontfamily='Helvetica')
        ax.tick_params(colors='white', labelsize=10)
        ax.grid(True, alpha=0.3, color='white')
        
        # Add value labels on bars
        for bar, percentage in zip(bars, percentages):
            ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                   f'{percentage}%', ha='left', va='center', color='white', fontfamily='Helvetica', fontweight='bold')
        
        plt.tight_layout()
        st.pyplot(fig)
    
    with col2:
        st.markdown("#### 📊 Customer Distribution by Income Segment")
        income_dist = df_customers['income_segment'].value_counts()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#1E3A8A')
        ax.set_facecolor('#1E3A8A')
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        wedges, texts, autotexts = ax.pie(income_dist.values, labels=income_dist.index, autopct='%1.1f%%',
                                         colors=colors, startangle=90)
        
        for text in texts:
            text.set_color('white')
            text.set_fontfamily('Helvetica')
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontfamily('Helvetica')
            autotext.set_fontweight('bold')
        
        st.pyplot(fig)
        
        st.markdown("#### 📈 Campaign Performance Overview")
        campaign_perf = df_campaigns.groupby('campaign_name')['conversion_rate'].mean().sort_values(ascending=False)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#1E3A8A')
        ax.set_facecolor('#1E3A8A')
        
        bars = ax.barh(range(len(campaign_perf)), campaign_perf.values * 100, 
                      color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
        ax.set_yticks(range(len(campaign_perf)))
        ax.set_yticklabels(campaign_perf.index, color='white', fontfamily='Helvetica')
        ax.set_xlabel('Conversion Rate (%)', color='white', fontfamily='Helvetica')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.3, color='white')
        
        plt.tight_layout()
        st.pyplot(fig)

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
                    st.markdown("**Balance Distribution**")
                    st.bar_chart(audience['total_balance'].value_counts(bins=10))
                
                with col2:
                    st.markdown("**Product Holdings**")
                    product_counts = audience['product_holdings'].value_counts().sort_index()
                    st.bar_chart(product_counts)
            
            with tab3:
                st.dataframe(audience[['customer_id', 'age', 'income_segment', 'region', 'total_balance', 'product_holdings']])
            
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
        conv_data = campaign_data.set_index('month')[['conversion_rate']]
        conv_data['conversion_rate'] = conv_data['conversion_rate'] * 100
        st.line_chart(conv_data)
    
    with col2:
        st.markdown("**Revenue Trend**")
        revenue_data = campaign_data.set_index('month')[['revenue_generated']]
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
        
        # Prepare data for Spain map
        spanish_data = []
        for region, info in spanish_regions.items():
            region_customers = df_customers[df_customers['region'] == region]
            spanish_data.append({
                'region': region,
                'lat': info['lat'],
                'lon': info['lon'],
                'customers': len(region_customers),
                'avg_balance': region_customers['total_balance'].mean(),
                'conversion_rate': np.random.uniform(2, 8)  # Simulated conversion rates
            })
        
        df_spain = pd.DataFrame(spanish_data)
        
        # Spain map
        layer = pdk.Layer(
            "ScatterplotLayer",
            df_spain,
            pickable=True,
            opacity=0.8,
            stroked=True,
            filled=True,
            radius_scale=100,
            radius_min_pixels=5,
            radius_max_pixels=50,
            line_width_min_pixels=1,
            get_position=["lon", "lat"],
            get_radius="customers",
            get_fill_color=[255, 107, 107, 180],
            get_line_color=[0, 0, 0],
        )
        
        view_state = pdk.ViewState(
            longitude=-3.7038,
            latitude=40.4168,
            zoom=5,
            pitch=0,
        )
        
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={
                "html": "<b>{region}</b><br>Customers: {customers}<br>Avg Balance: €{avg_balance:.0f}",
                "style": {"color": "white"}
            }
        )
        
        st.pydeck_chart(r)
        
        st.markdown("#### Spanish Regions Data")
        st.dataframe(df_spain[['region', 'customers', 'avg_balance', 'conversion_rate']])
    
    with col2:
        st.markdown("#### 🇪🇺 European Market Analysis")
        
        # Prepare data for Europe map
        europe_data = []
        for country, info in european_countries.items():
            europe_data.append({
                'country': country,
                'lat': info['lat'],
                'lon': info['lon'],
                'customers': info['customers'],
                'conversion_rate': info['conversion']
            })
        
        df_europe = pd.DataFrame(europe_data)
        
        # Europe map
        layer_europe = pdk.Layer(
            "ScatterplotLayer",
            df_europe,
            pickable=True,
            opacity=0.8,
            stroked=True,
            filled=True,
            radius_scale=200,
            radius_min_pixels=8,
            radius_max_pixels=80,
            line_width_min_pixels=1,
            get_position=["lon", "lat"],
            get_radius="customers",
            get_fill_color=[78, 205, 196, 180],
            get_line_color=[0, 0, 0],
        )
        
        view_state_europe = pdk.ViewState(
            longitude=10.0,
            latitude=50.0,
            zoom=3,
            pitch=0,
        )
        
        r_europe = pdk.Deck(
            layers=[layer_europe],
            initial_view_state=view_state_europe,
            tooltip={
                "html": "<b>{country}</b><br>Customers: {customers}<br>Conversion: {conversion_rate}%",
                "style": {"color": "white"}
            }
        )
        
        st.pydeck_chart(r_europe)
        
        st.markdown("#### European Markets Data")
        st.dataframe(df_europe[['country', 'customers', 'conversion_rate']])
        
        # Funnel chart for European markets
        st.markdown("#### 📊 European Conversion Funnel")
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#1E3A8A')
        ax.set_facecolor('#1E3A8A')
        
        countries = df_europe['country']
        conversions = df_europe['conversion_rate']
        
        bars = ax.bar(countries, conversions, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'])
        ax.set_ylabel('Conversion Rate (%)', color='white', fontfamily='Helvetica')
        ax.set_xlabel('Country', color='white', fontfamily='Helvetica')
        ax.tick_params(colors='white', rotation=45)
        ax.grid(True, alpha=0.3, color='white')
        
        for bar, conversion in zip(bars, conversions):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                   f'{conversion}%', ha='center', va='bottom', color='white', fontfamily='Helvetica')
        
        plt.tight_layout()
        st.pyplot(fig)

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
