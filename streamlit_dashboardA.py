import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io

# Set page configuration with premium banking theme
st.set_page_config(
    page_title="Accenture Banking Analytics",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium CSS for ultra-sharp banking interface
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #0A0F2D 0%, #1A1F3C 50%, #0A0F2D 100%);
        color: #FFFFFF;
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #0A0F2D 0%, #1A1F3C 50%, #0A0F2D 100%);
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }
    .main-header {
        font-size: 3.2rem;
        color: #FFFFFF;
        font-weight: 800;
        margin-bottom: 0.5rem;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        text-shadow: 0px 4px 8px rgba(0,0,0,0.5);
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #FFFFFF 0%, #D4AF37 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .section-header {
        font-size: 2.1rem;
        color: #D4AF37;
        font-weight: 700;
        margin-bottom: 1.5rem;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        border-bottom: 3px solid #D4AF37;
        padding-bottom: 0.5rem;
        letter-spacing: -0.3px;
    }
    .subsection-header {
        font-size: 1.6rem;
        color: #FFFFFF;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        letter-spacing: -0.2px;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        padding: 1.8rem;
        border-radius: 12px;
        border: 1px solid rgba(212, 175, 55, 0.3);
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .stMetric {
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(212, 175, 55, 0.2);
        backdrop-filter: blur(10px);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #0A0F2D 0%, #1A1F3C 100%);
        border-right: 1px solid rgba(212, 175, 55, 0.3);
    }
    div[data-testid="stSidebarNav"] {
        background: rgba(255, 255, 255, 0.05);
    }
    .funnel-container {
        background: rgba(255, 255, 255, 0.05);
        padding: 25px;
        border-radius: 12px;
        margin: 15px 0;
        border: 1px solid rgba(212, 175, 55, 0.2);
        backdrop-filter: blur(10px);
    }
    .funnel-stage {
        background: linear-gradient(90deg, #D4AF37, #FFD700);
        margin: 12px 0;
        padding: 18px;
        border-radius: 8px;
        text-align: center;
        color: #0A0F2D;
        font-weight: 700;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 1.1rem;
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
        transition: transform 0.2s ease;
    }
    .funnel-stage:hover {
        transform: translateX(5px);
    }
    .map-container {
        background: rgba(255, 255, 255, 0.05);
        padding: 25px;
        border-radius: 12px;
        margin: 15px 0;
        border: 1px solid rgba(212, 175, 55, 0.2);
        backdrop-filter: blur(10px);
    }
    .region-card {
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        padding: 18px;
        border-radius: 10px;
        margin: 12px 0;
        border-left: 4px solid #D4AF37;
        border: 1px solid rgba(212, 175, 55, 0.2);
    }
    .stButton button {
        background: linear-gradient(90deg, #D4AF37 0%, #FFD700 100%);
        color: #0A0F2D;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4);
    }
    .stSelectbox, .stMultiselect, .stSlider, .stTextInput, .stTextArea, .stDateInput {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 8px;
        color: white;
    }
    .stDataFrame {
        border: 1px solid rgba(212, 175, 55, 0.2);
        border-radius: 8px;
    }
    /* Fix chart labels */
    .stChart {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Generate premium banking data
def generate_sample_data():
    np.random.seed(42)
    
    # Spanish regions data - premium banking focus
    spanish_regions = {
        'Madrid': {'customers': 2450, 'conversion': 6.8, 'revenue': 1250000, 'aum': 450000000},
        'Cataluña': {'customers': 1980, 'conversion': 5.9, 'revenue': 980000, 'aum': 320000000},
        'Andalucía': {'customers': 1650, 'conversion': 4.7, 'revenue': 720000, 'aum': 280000000},
        'Valencia': {'customers': 1320, 'conversion': 5.2, 'revenue': 580000, 'aum': 195000000},
        'País Vasco': {'customers': 980, 'conversion': 7.1, 'revenue': 420000, 'aum': 180000000},
        'Galicia': {'customers': 870, 'conversion': 4.3, 'revenue': 380000, 'aum': 150000000},
        'Castilla y León': {'customers': 920, 'conversion': 4.1, 'revenue': 390000, 'aum': 165000000},
        'Aragón': {'customers': 750, 'conversion': 4.8, 'revenue': 320000, 'aum': 120000000},
        'Canarias': {'customers': 680, 'conversion': 4.5, 'revenue': 290000, 'aum': 95000000}
    }
    
    # European markets data
    european_countries = {
        'Spain': {'customers': 10000, 'conversion': 5.2, 'revenue': 5230000, 'aum': 1850000000},
        'France': {'customers': 12500, 'conversion': 4.8, 'revenue': 4980000, 'aum': 2200000000},
        'Germany': {'customers': 14200, 'conversion': 5.6, 'revenue': 6150000, 'aum': 2850000000},
        'Italy': {'customers': 9800, 'conversion': 4.3, 'revenue': 3820000, 'aum': 1650000000},
        'UK': {'customers': 15800, 'conversion': 5.1, 'revenue': 5980000, 'aum': 3150000000},
        'Switzerland': {'customers': 5200, 'conversion': 8.2, 'revenue': 2850000, 'aum': 1850000000}
    }
    
    # Premium customer base data
    customers = []
    for i in range(5000):
        region = np.random.choice(list(spanish_regions.keys()))
        income_tier = np.random.choice(['Mass Affluent', 'High Net Worth', 'Private Banking'], 
                                      p=[0.6, 0.3, 0.1])
        customers.append({
            'customer_id': f'PB_{i:05d}',
            'age': np.random.randint(25, 75),
            'income_tier': income_tier,
            'product_holdings': np.random.randint(2, 8),
            'total_balance': np.random.lognormal(10, 1.2) * 10000,
            'investment_portfolio': np.random.lognormal(11, 1.5) * 10000,
            'credit_score': np.random.randint(650, 850),
            'region': region,
            'campaign_eligible': np.random.choice([True, False], p=[0.8, 0.2]),
            'last_contact_days': np.random.randint(1, 120)
        })
    
    df_customers = pd.DataFrame(customers)
    
    # Premium campaign performance data
    campaigns = [
        'Wealth Management', 'Private Banking', 'Premium Credit Cards', 
        'Investment Advisory', 'Family Office', 'ESG Investing'
    ]
    campaign_data = []
    
    for campaign in campaigns:
        for month in range(1, 13):
            base_conversion = np.random.uniform(0.08, 0.25)  # Higher conversion for premium
            campaign_data.append({
                'campaign_name': campaign,
                'month': month,
                'target_audience': np.random.randint(800, 3000),
                'actual_reach': np.random.randint(700, 2900),
                'conversion_rate': base_conversion,
                'revenue_generated': np.random.uniform(150000, 800000),
                'aum_generated': np.random.uniform(5000000, 25000000),
                'cost_per_acquisition': np.random.uniform(200, 800)
            })
    
    df_campaigns = pd.DataFrame(campaign_data)
    
    # Premium funnel data
    funnel_data = {
        'stage': ['Market Reach', 'Lead Generation', 'Qualified Leads', 'Client Onboarding', 'Assets Under Management'],
        'count': [50000, 18500, 8200, 3500, 2800],
        'percentage': [100, 37, 16.4, 7, 5.6],
        'value_eur': [0, 0, 18500000, 125000000, 1850000000]
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

# Create premium funnel chart
def create_premium_funnel(funnel_data):
    html_funnel = """
    <div class="funnel-container">
        <h4 style="color: #D4AF37; text-align: center; font-family: 'Helvetica Neue'; font-weight: 700; font-size: 1.4rem; margin-bottom: 1.5rem;">CLIENT ACQUISITION FUNNEL</h4>
    """
    
    colors = ['#D4AF37', '#FFD700', '#FFEC8B', '#FFF8DC', '#FFFFFF']
    
    for i, (_, row) in enumerate(funnel_data.iterrows()):
        width = max(30, row['percentage'] * 1.5)  # Minimum width for visibility
        html_funnel += f"""
        <div class="funnel-stage" style="background: linear-gradient(90deg, {colors[i]}, {colors[(i+1)%len(colors)]}); width: {width}%; margin: 0 auto 8px auto;">
            <div style="font-size: 1.1rem; font-weight: 700;">{row['stage']}</div>
            <div style="font-size: 1rem; margin-top: 4px;">
                {row['count']:,} Clients | {row['percentage']}% Conversion
            </div>
            <div style="font-size: 0.9rem; margin-top: 2px; opacity: 0.9;">
                €{row['value_eur']:,.0f} AUM
            </div>
        </div>
        """
    
    html_funnel += "</div>"
    return html_funnel

# Create premium geographic visualization
def create_premium_geographic_view(regions_data, title):
    html_content = f"""
    <div class="map-container">
        <h4 style="color: #D4AF37; text-align: center; font-family: 'Helvetica Neue'; font-weight: 700; margin-bottom: 1.5rem;">{title}</h4>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
    """
    
    for region, data in regions_data.items():
        html_content += f"""
        <div class="region-card">
            <h5 style="color: #D4AF37; margin: 0 0 8px 0; font-family: 'Helvetica Neue'; font-weight: 700; font-size: 1.1rem;">{region}</h5>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.9rem;">
                <div style="color: #FFFFFF;">Clients:</div>
                <div style="color: #D4AF37; text-align: right; font-weight: 600;">{data['customers']:,}</div>
                <div style="color: #FFFFFF;">Conversion:</div>
                <div style="color: #D4AF37; text-align: right; font-weight: 600;">{data['conversion']}%</div>
                <div style="color: #FFFFFF;">Revenue:</div>
                <div style="color: #D4AF37; text-align: right; font-weight: 600;">€{data['revenue']:,}</div>
                <div style="color: #FFFFFF;">AUM:</div>
                <div style="color: #D4AF37; text-align: right; font-weight: 600;">€{data['aum']:,}</div>
            </div>
        </div>
        """
    
    html_content += "</div></div>"
    return html_content

# Premium sidebar navigation
st.sidebar.markdown("<h1 style='color: #D4AF37; font-family: \"Helvetica Neue\"; font-weight: 800; font-size: 1.6rem; margin-bottom: 2rem;'>ACCENTURE WEALTH ANALYTICS</h1>", unsafe_allow_html=True)
section = st.sidebar.radio("", 
    ["🏦 EXECUTIVE DASHBOARD", "🎯 CLIENT ACQUISITION", "📈 PERFORMANCE ANALYTICS", "🗺️ MARKET INTELLIGENCE", "🚀 CAMPAIGN EXECUTION"])

# Main header
st.markdown("<h1 class='main-header'>PRIVATE BANKING ANALYTICS PLATFORM</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #D4AF37; font-size: 1.3rem; font-family: \"Helvetica Neue\"; font-weight: 600; text-align: center; letter-spacing: 0.5px;'>WEALTH MANAGEMENT & CLIENT ACQUISITION INTELLIGENCE</p>", unsafe_allow_html=True)

if section == "🏦 EXECUTIVE DASHBOARD":
    st.markdown("<h2 class='section-header'>EXECUTIVE OVERVIEW</h2>", unsafe_allow_html=True)
    
    # Premium KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_aum = sum(region['aum'] for region in spanish_regions.values())
        st.metric(
            label="TOTAL ASSETS UNDER MANAGEMENT", 
            value=f"€{total_aum:,.0f}",
            delta="+8.7% YoY"
        )
    
    with col2:
        avg_conversion = df_campaigns['conversion_rate'].mean() * 100
        st.metric(
            label="AVG CONVERSION RATE", 
            value=f"{avg_conversion:.1f}%",
            delta="+2.3%"
        )
    
    with col3:
        premium_clients = len(df_customers[df_customers['income_tier'] != 'Mass Affluent'])
        st.metric(
            label="PREMIUM CLIENTS", 
            value=f"{premium_clients:,}",
            delta=f"{premium_clients/len(df_customers)*100:.1f}% of portfolio"
        )
    
    with col4:
        total_revenue = df_campaigns['revenue_generated'].sum()
        st.metric(
            label="ANNUAL REVENUE", 
            value=f"€{total_revenue:,.0f}",
            delta="+15.2%"
        )
    
    # Premium Charts and Data
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3 class='subsection-header'>CLIENT ACQUISITION FUNNEL</h3>", unsafe_allow_html=True)
        st.markdown(create_premium_funnel(df_funnel), unsafe_allow_html=True)
        
        st.markdown("<h3 class='subsection-header'>PORTFOLIO COMPOSITION</h3>", unsafe_allow_html=True)
        portfolio_data = df_customers['income_tier'].value_counts()
        st.bar_chart(portfolio_data)
    
    with col2:
        st.markdown("<h3 class='subsection-header'>CLIENT PORTFOLIO OVERVIEW</h3>", unsafe_allow_html=True)
        # Premium client data display
        premium_display = df_customers[['customer_id', 'income_tier', 'total_balance', 'investment_portfolio', 'credit_score']].head(8)
        st.dataframe(premium_display.style.format({
            'total_balance': '€{:,.0f}',
            'investment_portfolio': '€{:,.0f}'
        }), use_container_width=True)
        
        st.markdown("<h3 class='subsection-header'>ASSET CLASS DISTRIBUTION</h3>", unsafe_allow_html=True)
        asset_classes = ['Equities', 'Fixed Income', 'Alternatives', 'Cash', 'Real Estate']
        allocation = [45, 30, 15, 5, 5]
        asset_data = pd.DataFrame({'Asset Class': asset_classes, 'Allocation %': allocation})
        st.bar_chart(asset_data.set_index('Asset Class'))

elif section == "🎯 CLIENT ACQUISITION":
    st.markdown("<h2 class='section-header'>PRECISION CLIENT ACQUISITION</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("<h3 class='subsection-header'>TARGETING CRITERIA</h3>", unsafe_allow_html=True)
        
        campaign_type = st.selectbox(
            "WEALTH SEGMENT:",
            ["Private Banking", "High Net Worth", "Mass Affluent", "Family Office", "Institutional"]
        )
        
        st.markdown("**CLIENT FILTERS:**")
        min_balance = st.slider("MINIMUM ASSETS (€)", 50000, 5000000, 250000, step=50000)
        min_credit = st.slider("MINIMUM CREDIT SCORE", 650, 850, 720)
        income_tiers = st.multiselect(
            "WEALTH TIERS:",
            ["Mass Affluent", "High Net Worth", "Private Banking"],
            default=["High Net Worth", "Private Banking"]
        )
        
        regions = st.multiselect(
            "TARGET REGIONS:",
            df_customers['region'].unique(),
            default=df_customers['region'].unique()
        )
        
        min_products = st.slider("MINIMUM PRODUCT HOLDINGS", 2, 8, 3)
        
        if st.button("🎯 GENERATE TARGET AUDIENCE", type="primary", use_container_width=True):
            filtered_audience = df_customers[
                (df_customers['total_balance'] >= min_balance) &
                (df_customers['credit_score'] >= min_credit) &
                (df_customers['income_tier'].isin(income_tiers)) &
                (df_customers['region'].isin(regions)) &
                (df_customers['product_holdings'] >= min_products) &
                (df_customers['campaign_eligible'])
            ].copy()
            st.session_state.filtered_audience = filtered_audience
            st.success(f"✅ TARGET AUDIENCE IDENTIFIED: {len(filtered_audience):,} PREMIUM CLIENTS")
    
    with col2:
        st.markdown("<h3 class='subsection-header'>AUDIENCE INTELLIGENCE</h3>", unsafe_allow_html=True)
        
        if 'filtered_audience' in st.session_state and len(st.session_state.filtered_audience) > 0:
            audience = st.session_state.filtered_audience
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("TARGET SIZE", f"{len(audience):,}")
            with col2:
                st.metric("AVG ASSETS", f"€{audience['total_balance'].mean():,.0f}")
            with col3:
                st.metric("AVG PORTFOLIO", f"€{audience['investment_portfolio'].mean():,.0f}")
            with col4:
                st.metric("AVG CREDIT", f"{audience['credit_score'].mean():.0f}")
            
            st.markdown("<h4 style='color: #D4AF37; margin: 1.5rem 0 1rem 0;'>CLIENT SEGMENT ANALYSIS</h4>", unsafe_allow_html=True)
            
            tab1, tab2, tab3 = st.tabs(["WEALTH DISTRIBUTION", "REGIONAL ANALYSIS", "CLIENT DATA"])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**WEALTH TIER DISTRIBUTION**")
                    wealth_counts = audience['income_tier'].value_counts()
                    st.bar_chart(wealth_counts)
                
                with col2:
                    st.markdown("**ASSET DISTRIBUTION**")
                    # Use proper binning for better visualization
                    balance_bins = pd.cut(audience['total_balance'], bins=8)
                    st.bar_chart(balance_bins.value_counts().sort_index())
            
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**REGIONAL DISTRIBUTION**")
                    region_counts = audience['region'].value_counts()
                    st.bar_chart(region_counts)
                
                with col2:
                    st.markdown("**PRODUCT HOLDINGS**")
                    product_counts = audience['product_holdings'].value_counts().sort_index()
                    st.bar_chart(product_counts)
            
            with tab3:
                st.dataframe(audience[['customer_id', 'income_tier', 'region', 'total_balance', 'investment_portfolio', 'credit_score']])
            
            st.markdown("<h4 style='color: #D4AF37; margin: 1.5rem 0 1rem 0;'>AUDIENCE EXPORT</h4>", unsafe_allow_html=True)
            if st.button("📊 EXPORT CLIENT LIST", use_container_width=True):
                csv = audience.to_csv(index=False)
                st.download_button(
                    label="DOWNLOAD PREMIUM CLIENT DATA",
                    data=csv,
                    file_name=f"premium_audience_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

elif section == "📈 PERFORMANCE ANALYTICS":
    st.markdown("<h2 class='section-header'>PERFORMANCE INTELLIGENCE</h2>", unsafe_allow_html=True)
    
    selected_campaign = st.selectbox(
        "SELECT WEALTH PROGRAM:",
        df_campaigns['campaign_name'].unique()
    )
    
    campaign_data = df_campaigns[df_campaigns['campaign_name'] == selected_campaign]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_revenue = campaign_data['revenue_generated'].sum()
        st.metric("TOTAL REVENUE", f"€{total_revenue:,.0f}")
    
    with col2:
        avg_conversion = campaign_data['conversion_rate'].mean() * 100
        st.metric("CONVERSION RATE", f"{avg_conversion:.1f}%")
    
    with col3:
        total_aum = campaign_data['aum_generated'].sum()
        st.metric("AUM GENERATED", f"€{total_aum:,.0f}")
    
    with col4:
        avg_cpa = campaign_data['cost_per_acquisition'].mean()
        st.metric("COST PER CLIENT", f"€{avg_cpa:.0f}")
    
    st.markdown("<h3 class='subsection-header'>PERFORMANCE TRENDS</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**CONVERSION RATE TREND**")
        conv_data = campaign_data.set_index('month')[['conversion_rate']]
        conv_data['conversion_rate'] = conv_data['conversion_rate'] * 100
        st.line_chart(conv_data)
    
    with col2:
        st.markdown("**REVENUE GENERATION**")
        revenue_data = campaign_data.set_index('month')[['revenue_generated']]
        st.line_chart(revenue_data)
    
    st.markdown("<h3 class='subsection-header'>PROGRAM COMPARISON</h3>", unsafe_allow_html=True)
    
    comparison_metric = st.selectbox(
        "PERFORMANCE METRIC:", 
        ["conversion_rate", "revenue_generated", "aum_generated", "cost_per_acquisition"]
    )
    
    campaign_comparison = df_campaigns.groupby('campaign_name')[comparison_metric].mean().sort_values(ascending=False)
    st.bar_chart(campaign_comparison)

elif section == "🗺️ MARKET INTELLIGENCE":
    st.markdown("<h2 class='section-header'>MARKET INTELLIGENCE</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3 class='subsection-header'>SPANISH MARKET OVERVIEW</h3>", unsafe_allow_html=True)
        
        st.markdown(create_premium_geographic_view(spanish_regions, "SPANISH REGIONAL PERFORMANCE"), unsafe_allow_html=True)
        
        st.markdown("<h3 class='subsection-header'>REGIONAL PERFORMANCE</h3>", unsafe_allow_html=True)
        region_performance = pd.DataFrame([
            {'Region': region, 'Conversion %': data['conversion'], 'AUM (M)': data['aum']/1000000} 
            for region, data in spanish_regions.items()
        ])
        st.bar_chart(region_performance.set_index('Region')['Conversion %'])
    
    with col2:
        st.markdown("<h3 class='subsection-header'>EUROPEAN MARKETS</h3>", unsafe_allow_html=True)
        
        st.markdown(create_premium_geographic_view(european_countries, "EUROPEAN MARKET PRESENCE"), unsafe_allow_html=True)
        
        st.markdown("<h3 class='subsection-header'>MARKET COMPARISON</h3>", unsafe_allow_html=True)
        country_performance = pd.DataFrame([
            {'Country': country, 'AUM (B)': data['aum']/1000000000, 'Clients': data['customers']} 
            for country, data in european_countries.items()
        ])
        st.bar_chart(country_performance.set_index('Country')['AUM (B)'])

elif section == "🚀 CAMPAIGN EXECUTION":
    st.markdown("<h2 class='section-header'>CAMPAIGN EXECUTION PLATFORM</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3 class='subsection-header'>CAMPAIGN ORCHESTRATION</h3>", unsafe_allow_html=True)
        
        campaign_name = st.text_input("CAMPAIGN NAME", "Q1_2024_Private_Wealth_Acquisition")
        
        st.markdown("**EXECUTION PARAMETERS:**")
        execution_date = st.date_input("LAUNCH DATE", datetime.now() + timedelta(days=7))
        channel = st.selectbox("PRIMARY CHANNEL", ["Private Banking", "Wealth Advisor", "Digital Platform", "Family Office"])
        priority = st.select_slider("PRIORITY LEVEL", ["Standard", "High", "VIP"], value="High")
        
        st.markdown("**AUDIENCE STRATEGY:**")
        if 'filtered_audience' in st.session_state:
            audience_size = len(st.session_state.filtered_audience)
            st.success(f"✅ PRE-QUALIFIED AUDIENCE: {audience_size:,} PREMIUM CLIENTS")
            use_existing = st.checkbox("USE PRE-QUALIFIED AUDIENCE", value=True)
        else:
            st.warning("⚠️ NO AUDIENCE GENERATED - CONFIGURE IN CLIENT ACQUISITION")
            use_existing = False
        
        message_template = st.text_area(
            "CLIENT COMMUNICATION", 
            "Dear Valued Client,\n\nAs part of our exclusive Private Banking services, we would like to present a bespoke wealth management opportunity tailored to your portfolio requirements.\n\nOur dedicated wealth advisors are prepared to discuss how our [PROGRAM] can enhance your financial strategy and achieve your long-term objectives.\n\nWe look forward to the opportunity to serve you.\n\nSincerely,\nAccenture Private Banking",
            height=120
        )
        
        if st.button("🚀 DEPLOY CAMPAIGN", type="primary", use_container_width=True):
            st.success(f"✅ CAMPAIGN '{campaign_name}' SCHEDULED FOR {execution_date}")
            st.balloons()
            
            st.markdown("<h4 style='color: #D4AF37; margin: 1.5rem 0 1rem 0;'>NEXT PHASES</h4>", unsafe_allow_html=True)
            st.write("1. ✅ **CAMPAIGN SCHEDULED** - System deployment complete")
            st.write("2. 📧 **ADVISOR NOTIFICATION** - Wealth team briefed")
            st.write("3. 📊 **TRACKING ACTIVE** - Performance monitoring live")
            st.write("4. 🎯 **CLIENT OUTREACH** - Advisor communications initiated")
    
    with col2:
        st.markdown("<h3 class='subsection-header'>EXECUTION DASHBOARD</h3>", unsafe_allow_html=True)
        
        st.markdown("**CAMPAIGN PIPELINE**")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("SCHEDULED", "18", "+3")
        with col2:
            st.metric("ACTIVE", "7", "0")
        with col3:
            st.metric("IN PROGRESS", "5", "-1")
        with col4:
            st.metric("COMPLETED", "42", "+6")
        
        st.markdown("**RECENT EXECUTIONS**")
        
        execution_history = [
            {"Program": "Private Wealth Q4", "Status": "✅ COMPLETED", "Date": "2024-01-15", "AUM": "€185M", "Conv Rate": "6.8%"},
            {"Program": "Family Office", "Status": "🔄 ACTIVE", "Date": "2024-01-14", "AUM": "€92M", "Conv Rate": "8.2%"},
            {"Program": "ESG Investing", "Status": "✅ COMPLETED", "Date": "2024-01-13", "AUM": "€128M", "Conv Rate": "5.9%"},
            {"Program": "Wealth Transfer", "Status": "⏸️ PAUSED", "Date": "2024-01-12", "AUM": "€65M", "Conv Rate": "7.1%"},
        ]
        
        for campaign in execution_history:
            with st.container():
                st.write(f"**{campaign['Program']}**")
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    st.write(campaign['Status'])
                with col2:
                    st.write(campaign['Date'])
                with col3:
                    st.write(f"AUM: {campaign['AUM']} | Rate: {campaign['Conv Rate']}")
                st.divider()

# Premium PySpark Integration
st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color: #D4AF37; font-family: \"Helvetica Neue\"; font-weight: 700;'>⚡ PySpark DATA ENGINE</h3>", unsafe_allow_html=True)

if st.sidebar.button("ANALYZE CLIENT DATA"):
    with st.sidebar.expander("DATA PROCESSING RESULTS"):
        st.write("**PySpark Processing Complete:**")
        st.write("✅ **CLIENT DATA** - 5,000 premium records analyzed")
        st.write("✅ **WEALTH SEGMENTS** - Segmentation models applied")
        st.write("✅ **PERFORMANCE ANALYTICS** - Campaign ROI calculated")
        st.write("✅ **GEOGRAPHIC INTELLIGENCE** - Regional patterns identified")
        st.write(f"📊 **TOTAL AUM ANALYZED**: €{sum(region['aum'] for region in spanish_regions.values()):,.0f}")
        st.write(f"🎯 **PREMIUM CLIENTS**: {len(df_customers[df_customers['income_tier'] != 'Mass Affluent']):,}")

# Premium Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #D4AF37; font-family: \"Helvetica Neue\"; font-weight: 600; font-size: 1.1rem;'>"
    "ACCENTURE PRIVATE BANKING ANALYTICS | BUILT WITH PySpark & STREAMLIT | "
    "WEALTH MANAGEMENT INTELLIGENCE PLATFORM"
    "</p>", 
    unsafe_allow_html=True
)
