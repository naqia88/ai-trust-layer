import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ===== IMPORTS ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ===== RESET ===== */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background: #f5f7fb;
    }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #eef2f6 !important;
        padding-top: 20px !important;
        box-shadow: none !important;
    }

    .sidebar-header {
        padding: 0 20px 20px 20px;
        border-bottom: 1px solid #f0f2f5;
        margin-bottom: 16px;
    }
    .sidebar-header .logo {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .sidebar-header .logo-icon {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #7c3aed, #6d28d9);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 700;
        font-size: 16px;
    }
    .sidebar-header .logo-text {
        font-size: 18px;
        font-weight: 700;
        color: #111827;
    }
    .sidebar-header .logo-text span {
        color: #7c3aed;
    }

    /* Navigation */
    .nav-section {
        padding: 0 12px;
    }
    .nav-section .nav-label {
        font-size: 11px;
        font-weight: 600;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        padding: 8px 12px 6px 12px;
    }
    .nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 9px 14px;
        border-radius: 10px;
        color: #6b7280;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.15s ease;
        cursor: pointer;
        margin: 1px 0;
    }
    .nav-item:hover {
        background: #f3f4f6;
        color: #111827;
    }
    .nav-item.active {
        background: #7c3aed;
        color: #ffffff;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
    }
    .nav-item .icon {
        font-size: 16px;
        width: 22px;
        text-align: center;
    }
    .nav-item .badge {
        margin-left: auto;
        background: #ef4444;
        color: #fff;
        font-size: 10px;
        padding: 1px 10px;
        border-radius: 20px;
        font-weight: 600;
    }
    .nav-item.active .badge {
        background: rgba(255,255,255,0.25);
    }

    /* ===== MAIN CONTENT ===== */
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 0 20px 0;
        border-bottom: 1px solid #f0f2f5;
        margin-bottom: 24px;
    }
    .main-header h1 {
        font-size: 24px;
        font-weight: 700;
        color: #111827;
        margin: 0;
        letter-spacing: -0.3px;
    }
    .main-header .header-right {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .main-header .search-box {
        background: #f3f4f6;
        border-radius: 10px;
        padding: 8px 16px;
        display: flex;
        align-items: center;
        gap: 8px;
        color: #9ca3af;
        font-size: 14px;
    }
    .main-header .avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: linear-gradient(135deg, #7c3aed, #6d28d9);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 14px;
    }

    /* ===== STAT CARDS ===== */
    .stat-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px 24px;
        border: 1px solid #f0f2f5;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        transition: all 0.2s ease;
        height: 100%;
    }
    .stat-card:hover {
        box-shadow: 0 8px 25px rgba(0,0,0,0.06);
        transform: translateY(-2px);
    }
    .stat-card .stat-label {
        font-size: 13px;
        font-weight: 500;
        color: #9ca3af;
        margin-bottom: 4px;
    }
    .stat-card .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: #111827;
        letter-spacing: -0.5px;
    }
    .stat-card .stat-change {
        font-size: 13px;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 20px;
        display: inline-block;
        margin-top: 4px;
    }
    .stat-card .stat-change.positive {
        color: #10b981;
        background: #ecfdf5;
    }
    .stat-card .stat-change.negative {
        color: #ef4444;
        background: #fef2f2;
    }
    .stat-card .stat-icon {
        float: right;
        font-size: 28px;
        opacity: 0.6;
    }

    /* ===== METRIC OVERRIDE ===== */
    [data-testid="metric-container"] {
        background: #ffffff !important;
        border: 1px solid #f0f2f5 !important;
        border-radius: 16px !important;
        padding: 20px 24px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="metric-container"]:hover {
        box-shadow: 0 8px 25px rgba(0,0,0,0.06) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="metric-container"] label {
        color: #9ca3af !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #111827 !important;
        font-size: 28px !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricDelta"] {
        color: #10b981 !important;
        font-size: 13px !important;
    }

    /* ===== CARDS ===== */
    .card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px 24px;
        border: 1px solid #f0f2f5;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        margin-bottom: 16px;
    }
    .card-title {
        font-size: 16px;
        font-weight: 600;
        color: #111827;
        margin-bottom: 12px;
    }
    .card-subtitle {
        font-size: 13px;
        color: #9ca3af;
        margin-bottom: 16px;
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        background: #ffffff;
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
        border: 1px solid #f0f2f5;
        margin-bottom: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #6b7280;
        font-weight: 500;
        font-size: 14px;
        padding: 8px 20px;
        transition: all 0.15s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #111827;
        background: #f3f4f6;
    }
    .stTabs [aria-selected="true"] {
        background: #7c3aed !important;
        color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(124, 58, 237, 0.25);
    }

    /* ===== BUTTONS ===== */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: all 0.15s !important;
        border: 1px solid #e5e7eb !important;
        background: #ffffff !important;
        color: #111827 !important;
        padding: 8px 20px !important;
        height: auto !important;
    }
    .stButton > button:hover {
        background: #f3f4f6 !important;
        border-color: #d1d5db !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    }

    /* ===== DIVIDER ===== */
    .divider {
        border: none;
        height: 1px;
        background: #f0f2f5;
        margin: 20px 0;
    }

    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {
        .main-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
        }
        .stat-card .stat-value {
            font-size: 22px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
        <div class="sidebar-header">
            <div class="logo">
                <div class="logo-icon">A</div>
                <div class="logo-text">Dash<span>Stack</span></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="nav-section">
            <div class="nav-label">Main</div>
            <div class="nav-item active">
                <span class="icon">📊</span> Dashboard
            </div>
            <div class="nav-item">
                <span class="icon">📈</span> Analytics
            </div>
            <div class="nav-item">
                <span class="icon">📄</span> Pages
            </div>
            <div class="nav-item">
                <span class="icon">📱</span> Applications
                <span class="badge">3</span>
            </div>
            <div class="nav-item">
                <span class="icon">🛍️</span> E-commerce
            </div>
        </div>
        <div style="height:16px;"></div>
        <div class="nav-section">
            <div class="nav-label">Analytics</div>
            <div class="nav-item">
                <span class="icon">👤</span> Profile
            </div>
            <div class="nav-item">
                <span class="icon">👥</span> Teams
            </div>
            <div class="nav-item">
                <span class="icon">📁</span> Projects
            </div>
        </div>
        <div style="height:16px;"></div>
        <div class="nav-section">
            <div class="nav-label">Settings</div>
            <div class="nav-item">
                <span class="icon">⚙️</span> Preferences
            </div>
            <div class="nav-item">
                <span class="icon">👤</span> Account
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Filters in sidebar
    st.markdown("### 🔍 Filters")
    date_range = st.selectbox(
        "Date Range",
        ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "This Month", "Last Month"]
    )
    category = st.selectbox(
        "Category",
        ["All", "Sales", "Marketing", "Development", "Design"]
    )

# ── MAIN CONTENT ─────────────────────────────────────────────────────────────

# Header
st.markdown("""
    <div class="main-header">
        <h1>Dashboard</h1>
        <div class="header-right">
            <div class="search-box">🔍 Search...</div>
            <div class="avatar">JD</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── STAT CARDS ROW 1 ────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Active Users",
        value="2,847",
        delta="12.5%",
        help="Active users in the last 24 hours"
    )

with col2:
    st.metric(
        label="Page Views",
        value="43.2K",
        delta="8.1%",
        help="Total page views"
    )

with col3:
    st.metric(
        label="Revenue",
        value="$735.2K",
        delta="23.4%",
        help="Total revenue this month"
    )

with col4:
    st.metric(
        label="Conversion Rate",
        value="3.42%",
        delta="-1.2%",
        help="Overall conversion rate"
    )

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── STAT CARDS ROW 2 ────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
        <div class="stat-card">
            <span class="stat-icon">👥</span>
            <div class="stat-label">Total Users</div>
            <div class="stat-value">2,847</div>
            <span class="stat-change positive">↑ 12.5%</span>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="stat-card">
            <span class="stat-icon">👁️</span>
            <div class="stat-label">Page Views</div>
            <div class="stat-value">43.2K</div>
            <span class="stat-change positive">↑ 8.1%</span>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="stat-card">
            <span class="stat-icon">💵</span>
            <div class="stat-label">Revenue</div>
            <div class="stat-value">$735.2K</div>
            <span class="stat-change positive">↑ 23.4%</span>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
        <div class="stat-card">
            <span class="stat-icon">📈</span>
            <div class="stat-label">Conversion</div>
            <div class="stat-value">3.42%</div>
            <span class="stat-change negative">↓ 1.2%</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── CHARTS SECTION ──────────────────────────────────────────────────────────

# Create sample data for charts
dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
data = {
    'Date': dates,
    'Sales': [random.randint(50, 200) for _ in range(30)],
    'Users': [random.randint(20, 100) for _ in range(30)],
    'Clicks': [random.randint(30, 150) for _ in range(30)]
}
df = pd.DataFrame(data)

# Row with two charts
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📊 Sales Overview</div>', unsafe_allow_html=True)
    
    fig = px.line(
        df,
        x='Date',
        y='Sales',
        line_shape='spline',
        color_discrete_sequence=['#7c3aed']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color='#6b7280'),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#f3f4f6'),
        margin=dict(l=0, r=0, t=0, b=0),
        height=300,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with chart_col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">👥 User Engagement</div>', unsafe_allow_html=True)
    
    fig2 = px.bar(
        df.tail(10),
        x='Date',
        y='Users',
        color_discrete_sequence=['#8b5cf6']
    )
    fig2.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color='#6b7280'),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#f3f4f6'),
        margin=dict(l=0, r=0, t=0, b=0),
        height=300,
        showlegend=False
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── PROFILE STATS SECTION ──────────────────────────────────────────────────

st.markdown("### 👤 Profile Overview")

profile_col1, profile_col2, profile_col3 = st.columns(3)

with profile_col1:
    st.markdown("""
        <div class="stat-card">
            <div class="stat-label">⭐ Average Likes</div>
            <div class="stat-value">635</div>
            <span class="stat-change positive">↑ 21.01%</span>
        </div>
    """, unsafe_allow_html=True)

with profile_col2:
    st.markdown("""
        <div class="stat-card">
            <div class="stat-label">💬 Comments Received</div>
            <div class="stat-value">123</div>
            <span class="stat-change positive">↑ 4.39%</span>
        </div>
    """, unsafe_allow_html=True)

with profile_col3:
    st.markdown("""
        <div class="stat-card">
            <div class="stat-label">📊 Avg. Engagement Rate</div>
            <div class="stat-value">23%</div>
            <span class="stat-change negative">↓ 7.9%</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── TABS FOR DETAILED VIEWS ────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["📈 Analytics", "👥 Team", "📊 Reports"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">📊 Revenue Breakdown</div>', unsafe_allow_html=True)
        
        # Pie chart
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Income', 'Outcome', 'Savings', 'Investments'],
            values=[45, 25, 20, 10],
            marker=dict(colors=['#7c3aed', '#8b5cf6', '#a78bfa', '#c4b5fd']),
            hole=0.5
        )])
        fig_pie.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', color='#6b7280'),
            margin=dict(l=0, r=0, t=0, b=0),
            height=300,
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=-0.2)
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">📈 Engagement Trends</div>', unsafe_allow_html=True)
        
        # Area chart
        fig_area = px.area(
            df.tail(15),
            x='Date',
            y=['Sales', 'Clicks'],
            color_discrete_sequence=['#7c3aed', '#8b5cf6']
        )
        fig_area.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', color='#6b7280'),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#f3f4f6'),
            margin=dict(l=0, r=0, t=0, b=0),
            height=300,
            legend=dict(orientation='h', yanchor='bottom', y=-0.2)
        )
        st.plotly_chart(fig_area, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">👥 Team Members</div>', unsafe_allow_html=True)
    
    team_data = {
        'Name': ['Alice Turner', 'Bob Smith', 'Carol White', 'David Brown', 'Emma Wilson'],
        'Role': ['Design Lead', 'Developer', 'Product Manager', 'Analyst', 'Marketing'],
        'Status': ['Online', 'Away', 'Online', 'Offline', 'Online']
    }
    team_df = pd.DataFrame(team_data)
    st.dataframe(
        team_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Status': st.column_config.SelectboxColumn(
                'Status',
                options=['Online', 'Away', 'Offline']
            )
        }
    )
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📊 Performance Metrics</div>', unsafe_allow_html=True)
    
    metric_data = {
        'Metric': ['Page Views', 'Click-through Rate', 'Bounce Rate', 'Avg Session', 'Conversions'],
        'Value': ['43.2K', '3.2%', '28.5%', '4m 32s', '1,284'],
        'Change': ['+8.1%', '+2.3%', '-5.4%', '+12%', '+18.7%'],
        'Status': ['✅', '✅', '⚠️', '✅', '✅']
    }
    metric_df = pd.DataFrame(metric_data)
    st.dataframe(
        metric_df,
        use_container_width=True,
        hide_index=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ──────────────────────────────────────────────────────────────────

st.markdown("""
    <div style="text-align:center;padding:20px 0;color:#9ca3af;font-size:13px;border-top:1px solid #f0f2f5;margin-top:20px;">
        Dashboard v2.0 · © 2024 DashStack
    </div>
""", unsafe_allow_html=True)
