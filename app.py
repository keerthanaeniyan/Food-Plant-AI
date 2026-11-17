"""
FOOD PLANT AI - Smart Spice Production, Quality Prediction and Manufacturing Intelligence System
Main Application Entrypoint.
"""

import streamlit as st
import database

# 1. Page Configuration
st.set_page_config(
    page_title="FOOD PLANT AI - Smart Manufacturing Intelligence",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Database Initialization
database.init_db()

# 3. Custom Industrial Styling (Dark Navy Blue & Crisp White Industrial Theme)
st.markdown("""
<style>
    /* Main Font & Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Top Bar Header */
    .plant-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-bottom: 2px solid #3b82f6;
        padding: 1.25rem 1.75rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
    }
    
    .plant-title {
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        color: #f8fafc;
        margin: 0;
    }
    
    .plant-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        background: rgba(59, 130, 246, 0.2);
        color: #93c5fd;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        border: 1px solid rgba(59, 130, 246, 0.4);
    }
    
    /* Modern Industrial KPI Cards */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
    }
    .kpi-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 0.25rem;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
        line-height: 1.2;
    }
    .kpi-subtext {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 0.25rem;
    }
    
    /* Status Badges */
    .badge-pass {
        background-color: #ecfdf5;
        color: #047857;
        font-weight: 600;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        border: 1px solid #a7f3d0;
        display: inline-block;
        font-size: 0.85rem;
    }
    .badge-fail {
        background-color: #fef2f2;
        color: #b91c1c;
        font-weight: 600;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        border: 1px solid #fecaca;
        display: inline-block;
        font-size: 0.85rem;
    }
    .badge-risk-low {
        background-color: #f0fdf4;
        color: #15803d;
        font-weight: 600;
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        border: 1px solid #bbf7d0;
    }
    .badge-risk-med {
        background-color: #fffbeb;
        color: #b45309;
        font-weight: 600;
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        border: 1px solid #fde68a;
    }
    .badge-risk-high {
        background-color: #fef2f2;
        color: #b91c1c;
        font-weight: 600;
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        border: 1px solid #fecaca;
    }
    
    /* Clean Industrial Tables */
    .stDataFrame {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# 4. Streamlit Navigation Setup (Section 4 Requirements)
dashboard_page = st.Page("pages/dashboard.py", title="Executive Dashboard", icon="📊")
production_page = st.Page("pages/production.py", title="Production Management", icon="🏭")
suppliers_page = st.Page("pages/suppliers.py", title="Supplier Management", icon="🤝")
raw_materials_page = st.Page("pages/raw_materials.py", title="Raw Material Management", icon="📦")
dataset_page = st.Page("pages/dataset.py", title="Dataset Management", icon="📁")
prediction_page = st.Page("pages/prediction.py", title="AI Quality Prediction", icon="🤖")
history_page = st.Page("pages/history.py", title="Prediction History", icon="📜")
monitoring_page = st.Page("pages/machine_monitoring.py", title="Machine Monitoring", icon="⚙️")
performance_page = st.Page("pages/model_performance.py", title="Model Performance", icon="📈")
roi_page = st.Page("pages/roi.py", title="ROI Calculator", icon="💰")
responsible_ai_page = st.Page("pages/responsible_ai.py", title="Responsible AI", icon="🛡️")
settings_page = st.Page("pages/settings.py", title="Settings", icon="⚙️")

pg = st.navigation({
    "Executive & Plant Operations": [dashboard_page, production_page, suppliers_page, raw_materials_page, dataset_page],
    "Industrial AI & Quality": [prediction_page, history_page, monitoring_page, performance_page],
    "Enterprise & Compliance": [roi_page, responsible_ai_page, settings_page]
})

# Sidebar Industrial Branding
with st.sidebar:
    st.markdown("""
        <div style="padding: 0.75rem 0; border-bottom: 1px solid #334155; margin-bottom: 1rem;">
            <div style="font-size: 1.15rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.01em;">
                🏭 FOOD PLANT AI
            </div>
            <div style="font-size: 0.75rem; color: #94a3b8;">
                Hyderabad Facility • Lines 1, 2, 3
            </div>
        </div>
    """, unsafe_allow_html=True)

pg.run()
