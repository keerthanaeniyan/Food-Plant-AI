"""
FOOD PLANT AI — ROI Calculator Page
Interactive financial impact calculator for AI quality management.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from roi_calculator import calculate_roi


def show():
    st.markdown("""
        <div class="plant-header">
            <h1 class="plant-title">💰 ROI Calculator</h1>
            <span class="plant-tag">BUSINESS IMPACT ANALYSIS</span>
        </div>
    """, unsafe_allow_html=True)

    st.info("""
    📌 **Financial Assumptions Notice:** All inputs below are configurable estimates.
    Actual financial impact depends on real production data, lab costs, market prices, and operational factors.
    These calculations are provided as a **business case tool**, not guaranteed business outcomes.
    """)

    # ── Inputs ───────────────────────────────────────────────────────────────
    with st.expander("📋 Business Parameters (click to adjust)", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            monthly_batches = st.number_input("Monthly Production Batches", min_value=10, max_value=10000, value=500, step=10)
            failure_rate    = st.number_input("Current Quality Failure Rate (%)", min_value=1.0, max_value=80.0, value=25.0, step=0.5)
            loss_per_batch  = st.number_input("Average Financial Loss per Failed Batch (₹)", min_value=1000, max_value=500000, value=15000, step=1000)
        with col2:
            preventable_pct  = st.number_input("Expected Preventable Failures with AI (%)", min_value=10.0, max_value=90.0, value=65.0, step=5.0)
            initial_cost     = st.number_input("Initial AI Development Cost (₹)", min_value=50000, max_value=10000000, value=500000, step=25000)
            annual_maint     = st.number_input("Annual Maintenance Cost (₹)", min_value=10000, max_value=2000000, value=120000, step=10000)

    # ── Calculate ─────────────────────────────────────────────────────────────
    result = calculate_roi(
        monthly_batches=int(monthly_batches),
        failure_rate_pct=float(failure_rate),
        loss_per_batch_inr=float(loss_per_batch),
        preventable_pct=float(preventable_pct),
        initial_cost_inr=float(initial_cost),
        annual_maintenance_inr=float(annual_maint)
    )

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📊 Projected Financial Impact")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Monthly Savings</div>
            <div class="kpi-value" style="color:#047857">₹{result['monthly_savings_inr']:,.0f}</div>
            <div class="kpi-subtext">From AI-prevented failures</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Annual Savings</div>
            <div class="kpi-value" style="color:#047857">₹{result['annual_savings_inr']:,.0f}</div>
            <div class="kpi-subtext">12-month projection</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Net Annual Benefit</div>
            <div class="kpi-value" style="color:#1d4ed8">₹{result['net_annual_benefit_inr']:,.0f}</div>
            <div class="kpi-subtext">After operating costs</div></div>""", unsafe_allow_html=True)
    with c4:
        roi_color = "#047857" if result["roi_percentage"] > 0 else "#b91c1c"
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">ROI</div>
            <div class="kpi-value" style="color:{roi_color}">{result['roi_percentage']:+.1f}%</div>
            <div class="kpi-subtext">Return on investment</div></div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Payback Period</div>
            <div class="kpi-value">{result['payback_months']:.1f} mo</div>
            <div class="kpi-subtext">Months to break even</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        monthly_loss = result["monthly_financial_loss_inr"]
        monthly_save = result["monthly_savings_inr"]
        monthly_remain = monthly_loss - monthly_save
        fig = go.Figure(data=[
            go.Bar(name="Monthly Loss (Without AI)", x=["Monthly Impact"], y=[monthly_loss], marker_color="#dc2626"),
            go.Bar(name="AI-Prevented Loss (Savings)", x=["Monthly Impact"], y=[monthly_save], marker_color="#2563eb"),
            go.Bar(name="Remaining Loss (With AI)", x=["Monthly Impact"], y=[monthly_remain], marker_color="#f59e0b"),
        ])
        fig.update_layout(title="Monthly Financial Impact Breakdown", barmode="group",
                          template="plotly_white", height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        cost_labels = ["Development Cost", "Annual Maintenance", "Remaining Annual Loss"]
        cost_values = [
            result["initial_cost_inr"],
            result["annual_operating_cost_inr"],
            max(0, monthly_remain * 12)
        ]
        fig2 = px.pie(names=cost_labels, values=cost_values,
                      color_discrete_sequence=["#dc2626", "#f59e0b", "#6b7280"],
                      title="Cost Distribution (Year 1)")
        st.plotly_chart(fig2, use_container_width=True)

    # ── 3-Year Projection ─────────────────────────────────────────────────────
    st.subheader("📈 3-Year Cumulative Net Benefit Projection")
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=["Start", "Year 1", "Year 2", "Year 3"],
        y=[0, result["year1_net_inr"], result["year2_net_inr"], result["year3_net_inr"]],
        mode="lines+markers",
        line=dict(color="#2563eb", width=3),
        marker=dict(size=10),
        name="Cumulative Net Benefit"
    ))
    fig3.add_hline(y=0, line_dash="dash", line_color="#dc2626", annotation_text="Break-Even")
    fig3.update_layout(
        yaxis_title="Cumulative Net Benefit (₹)",
        template="plotly_white", height=350
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Summary Table ────────────────────────────────────────────────────────
    st.subheader("📋 Detailed Calculation Summary")
    rows = [
        ("Monthly Production Batches", f"{result['monthly_batches']:,}"),
        ("Monthly Failed Batches", f"{result['monthly_failed_batches']:.0f}"),
        ("Monthly Financial Loss (without AI)", f"₹{result['monthly_financial_loss_inr']:,.0f}"),
        ("Monthly Savings (with AI)", f"₹{result['monthly_savings_inr']:,.0f}"),
        ("Annual Gross Savings", f"₹{result['annual_savings_inr']:,.0f}"),
        ("Annual Operating Cost (Maintenance)", f"₹{result['annual_operating_cost_inr']:,.0f}"),
        ("Net Annual Benefit", f"₹{result['net_annual_benefit_inr']:,.0f}"),
        ("Initial Development Investment", f"₹{result['initial_cost_inr']:,.0f}"),
        ("ROI (%)", f"{result['roi_percentage']:+.1f}%"),
        ("Break-Even Period", f"{result['payback_months']:.1f} months"),
    ]
    import pandas as pd
    summary_df = pd.DataFrame(rows, columns=["Metric", "Value"])
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.caption("""
    **Formula:** ROI = (Net Annual Benefit − 0) / (Initial Cost + Annual Maintenance) × 100  
    **Assumptions:** Figures are illustrative estimates. Actual results depend on model deployment quality,
    factory-specific conditions, and confirmed failure-cost data from operations.
    """)


show()
