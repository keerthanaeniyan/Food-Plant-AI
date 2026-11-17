"""
FOOD PLANT AI — Executive Dashboard Page
All statistics derived from live SQLite database records.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import database


def show():
    st.markdown("""
        <div class="plant-header">
            <h1 class="plant-title">📊 Executive Dashboard</h1>
            <span class="plant-tag">LIVE DATA • SPICERAFT HYD</span>
        </div>
    """, unsafe_allow_html=True)

    # ── Filters ──────────────────────────────────────────────────────────────
    with st.expander("🔽 Date & Line Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("From Date", value=date.today() - timedelta(days=365))
        with col2:
            end_date = st.date_input("To Date", value=date.today())
        with col3:
            line_filter = st.multiselect("Production Lines", ["Line 1", "Line 2", "Line 3"],
                                         default=["Line 1", "Line 2", "Line 3"])

    # ── Fetch data ────────────────────────────────────────────────────────────
    all_batches = database.get_production_batches(
        start_date=str(start_date),
        end_date=str(end_date),
        limit=200000
    )

    if line_filter:
        all_batches = [b for b in all_batches if b.get("Production_Line") in line_filter]

    if not all_batches:
        st.info("📌 No production records found for the selected filters. Add batches in **Production Management** or generate the dataset in **Dataset Management**.")
        return

    df = pd.DataFrame(all_batches)
    df["Production_Date"] = pd.to_datetime(df["Production_Date"], errors="coerce")

    total         = len(df)
    total_pass    = (df["Actual_Quality_Result"] == "PASS").sum()
    total_fail    = (df["Actual_Quality_Result"] == "FAIL").sum()
    pass_rate     = total_pass / total * 100 if total > 0 else 0
    total_weight  = df["Standardized_Weight_Kg"].sum() / 1000  # tonnes

    suppliers     = database.get_all_suppliers()
    n_suppliers   = len(suppliers)

    # Best line
    line_pass_rates = (
        df.groupby("Production_Line")["Actual_Quality_Result"]
        .apply(lambda x: (x == "PASS").mean() * 100)
    )
    best_line = line_pass_rates.idxmax() if not line_pass_rates.empty else "—"

    # Most produced spice
    best_spice = df["Spice_Type"].value_counts().idxmax() if "Spice_Type" in df.columns else "—"

    # ── KPI Row 1 ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    _kpi(c1, "Total Batches", f"{total:,}", "All production runs")
    _kpi(c2, "PASS Batches", f"{total_pass:,}", f"{pass_rate:.1f}% pass rate", color="#047857")
    _kpi(c3, "FAIL Batches", f"{total_fail:,}", f"{100-pass_rate:.1f}% fail rate", color="#b91c1c")
    _kpi(c4, "Quality Pass %", f"{pass_rate:.1f}%", "Overall quality score")
    _kpi(c5, "Total Weight", f"{total_weight:,.1f} t", "Processed (tonnes)")

    st.markdown("<br>", unsafe_allow_html=True)

    c6, c7, c8 = st.columns(3)
    _kpi(c6, "Active Suppliers", str(n_suppliers), "Registered suppliers")
    _kpi(c7, "Best Performing Line", best_line, f"{line_pass_rates.max():.1f}% pass rate" if not line_pass_rates.empty else "")
    _kpi(c8, "Top Product", best_spice, "By batch count")

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # ── Charts Row 1 ──────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("📅 Monthly Production Trend")
        df["Month"] = df["Production_Date"].dt.to_period("M").astype(str)
        monthly = df.groupby(["Month", "Actual_Quality_Result"]).size().reset_index(name="Count")
        if not monthly.empty:
            fig = px.bar(monthly, x="Month", y="Count", color="Actual_Quality_Result",
                         color_discrete_map={"PASS": "#2563eb", "FAIL": "#dc2626"},
                         barmode="stack", template="plotly_white")
            fig.update_layout(height=360, xaxis_tickangle=-45, legend_title="Quality")
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("🌶️ Quality by Spice Type")
        if "Spice_Type" in df.columns:
            spice_q = df.groupby(["Spice_Type", "Actual_Quality_Result"]).size().reset_index(name="Count")
            fig2 = px.bar(spice_q, x="Spice_Type", y="Count", color="Actual_Quality_Result",
                          color_discrete_map={"PASS": "#2563eb", "FAIL": "#dc2626"},
                          barmode="group", template="plotly_white")
            fig2.update_layout(height=360)
            st.plotly_chart(fig2, use_container_width=True)

    # ── Charts Row 2 ──────────────────────────────────────────────────────────
    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("🏭 Production Line Performance")
        if not line_pass_rates.empty:
            fig3 = px.bar(
                x=line_pass_rates.values, y=line_pass_rates.index,
                orientation="h",
                color=line_pass_rates.values,
                color_continuous_scale=["#dc2626", "#f59e0b", "#2563eb"],
                range_color=[50, 100],
                labels={"x": "Pass Rate (%)", "y": "Production Line"},
                template="plotly_white"
            )
            fig3.update_layout(height=300, coloraxis_showscale=False)
            st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        st.subheader("🤝 Supplier Quality Analysis")
        sup_stats = (
            df.groupby("Supplier_Name")["Actual_Quality_Result"]
            .apply(lambda x: (x == "FAIL").mean() * 100)
            .reset_index()
        )
        sup_stats.columns = ["Supplier", "Fail_Rate_Pct"]
        sup_stats = sup_stats.sort_values("Fail_Rate_Pct", ascending=False).head(10)
        if not sup_stats.empty:
            fig4 = px.bar(sup_stats, x="Fail_Rate_Pct", y="Supplier", orientation="h",
                          color="Fail_Rate_Pct",
                          color_continuous_scale=["#2563eb", "#f59e0b", "#dc2626"],
                          labels={"Fail_Rate_Pct": "Fail Rate (%)"},
                          template="plotly_white")
            fig4.update_layout(height=300, coloraxis_showscale=False)
            st.plotly_chart(fig4, use_container_width=True)

    st.divider()
    st.subheader("📋 Recent Production Records")
    display_df = df.sort_values("Production_Date", ascending=False).head(20)[
        ["Batch_ID", "Production_Date", "Production_Line", "Supplier_Name",
         "Spice_Type", "Standardized_Weight_Kg", "Actual_Quality_Result"]
    ].copy()
    display_df["Production_Date"] = display_df["Production_Date"].dt.strftime("%Y-%m-%d")
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def _kpi(col, label, value, subtext="", color="#0f172a"):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value" style="color:{color}">{value}</div>
            <div class="kpi-subtext">{subtext}</div>
        </div>
        """, unsafe_allow_html=True)


show()
