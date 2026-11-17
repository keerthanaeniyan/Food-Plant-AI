"""
FOOD PLANT AI — Machine Monitoring Page
Historical parameter trend analysis and configurable alert system.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import database


def show():
    st.markdown("""
        <div class="plant-header">
            <h1 class="plant-title">⚙️ Machine Monitoring</h1>
            <span class="plant-tag">PARAMETER TRENDS</span>
        </div>
    """, unsafe_allow_html=True)

    st.info("""
    ⚠️ **Data Source Notice:** This module analyses **historical production records** stored in the database.
    It does **not** connect to live IoT sensors or real-time monitoring equipment.
    All operating limits shown are configurable demonstration defaults — they should be validated
    with certified factory engineers before operational use.
    """)

    # ── Configurable limits ───────────────────────────────────────────────────
    settings = database.get_all_settings()
    temp_min  = float(settings.get("TEMP_LIMIT_MIN",  "65"))
    temp_max  = float(settings.get("TEMP_LIMIT_MAX",  "85"))
    spd_min   = float(settings.get("SPEED_LIMIT_MIN", "1100"))
    spd_max   = float(settings.get("SPEED_LIMIT_MAX", "1450"))
    moist_max = float(settings.get("MOISTURE_LIMIT_MAX", "12"))
    time_max  = float(settings.get("PROD_TIME_MAX",   "55"))

    with st.expander("⚙️ Current Operating Limits (configure in Settings)", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Temp Min", f"{temp_min}°C")
            st.metric("Temp Max", f"{temp_max}°C")
        with col2:
            st.metric("Speed Min", f"{spd_min} RPM")
            st.metric("Speed Max", f"{spd_max} RPM")
        with col3:
            st.metric("Moisture Max", f"{moist_max}%")
        with col4:
            st.metric("Prod Time Max", f"{time_max} min")
        st.caption("Change limits on the **Settings** page → Operating Limits section.")

    # ── Filters ──────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        line_sel = st.selectbox("Production Line", ["All Lines", "Line 1", "Line 2", "Line 3"])
    with col2:
        days_back = st.number_input("Analysis Window (days)", min_value=7, max_value=1095, value=90)
    with col3:
        spice_sel = st.selectbox("Spice Type", ["All"] + ["Chilli Powder", "Turmeric Powder", "Coriander Powder", "Garam Masala"])

    cutoff = str(date.today() - timedelta(days=int(days_back)))
    batches = database.get_production_batches(
        production_line=None if line_sel == "All Lines" else line_sel,
        spice_type=None if spice_sel == "All" else spice_sel,
        start_date=cutoff,
        limit=50000
    )

    if not batches:
        st.info("No production records found for the selected filters.")
        return

    df = pd.DataFrame(batches)
    df["Production_Date"] = pd.to_datetime(df["Production_Date"], errors="coerce")

    # ── Alert summary ─────────────────────────────────────────────────────────
    st.subheader("🚨 Alert Summary")
    n_temp  = ((df["Machine_Temperature"] > temp_max) | (df["Machine_Temperature"] < temp_min)).sum()
    n_speed = ((df["Machine_Speed"] > spd_max) | (df["Machine_Speed"] < spd_min)).sum()
    n_moist = (df["Moisture_Level"] > moist_max).sum()
    n_time  = (df["Production_Time"] > time_max).sum()
    total   = len(df)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        color = "🔴" if n_temp > 0 else "🟢"
        st.metric(f"{color} Temp Out-of-Range", n_temp, f"{n_temp/total*100:.1f}% of batches")
    with c2:
        color = "🔴" if n_speed > 0 else "🟢"
        st.metric(f"{color} Speed Out-of-Range", n_speed, f"{n_speed/total*100:.1f}%")
    with c3:
        color = "🔴" if n_moist > 0 else "🟢"
        st.metric(f"{color} High Moisture", n_moist, f"{n_moist/total*100:.1f}%")
    with c4:
        color = "🔴" if n_time > 0 else "🟢"
        st.metric(f"{color} Long Cycle Time", n_time, f"{n_time/total*100:.1f}%")

    st.divider()

    # ── Parameter Trend Charts ────────────────────────────────────────────────
    st.subheader("📈 Parameter Trends")

    param_tabs = st.tabs(["🌡️ Temperature", "⚡ Speed", "💧 Moisture", "⏱️ Cycle Time"])

    with param_tabs[0]:
        _trend_chart(df, "Machine_Temperature", "Machine Temperature (°C)",
                     ymin=temp_min, ymax=temp_max, color="#f59e0b")

    with param_tabs[1]:
        _trend_chart(df, "Machine_Speed", "Machine Speed (RPM)",
                     ymin=spd_min, ymax=spd_max, color="#8b5cf6")

    with param_tabs[2]:
        _trend_chart(df, "Moisture_Level", "Moisture Level (%)",
                     ymin=None, ymax=moist_max, color="#3b82f6")

    with param_tabs[3]:
        _trend_chart(df, "Production_Time", "Production Cycle Time (min)",
                     ymin=None, ymax=time_max, color="#10b981")

    # ── Statistics Table ──────────────────────────────────────────────────────
    st.subheader("📊 Parameter Statistics")
    stats = df[["Production_Line", "Machine_Temperature", "Machine_Speed",
                "Moisture_Level", "Production_Time"]].groupby("Production_Line").agg(
        ["min", "max", "mean", "std"]
    ).round(2)
    st.dataframe(stats, use_container_width=True)


def _trend_chart(df, col, label, ymin=None, ymax=None, color="#2563eb"):
    if col not in df.columns:
        st.info(f"Column {col} not available.")
        return

    sample = df[["Production_Date", col, "Actual_Quality_Result"]].dropna().sample(
        min(2000, len(df)), random_state=42
    ).sort_values("Production_Date")

    fig = go.Figure()
    for result, marker_color in [("PASS", "#2563eb"), ("FAIL", "#dc2626")]:
        sub = sample[sample["Actual_Quality_Result"] == result]
        fig.add_trace(go.Scatter(
            x=sub["Production_Date"], y=sub[col],
            mode="markers", name=result,
            marker=dict(color=marker_color, size=4, opacity=0.6)
        ))

    if ymin is not None:
        fig.add_hline(y=ymin, line_dash="dash", line_color="#f59e0b",
                      annotation_text=f"Min Limit ({ymin})")
    if ymax is not None:
        fig.add_hline(y=ymax, line_dash="dash", line_color="#dc2626",
                      annotation_text=f"Max Limit ({ymax})")

    fig.update_layout(
        title=f"{label} Over Time (sample of {len(sample):,} batches)",
        xaxis_title="Date", yaxis_title=label,
        height=380, template="plotly_white",
        legend_title="Quality Result"
    )
    st.plotly_chart(fig, use_container_width=True)


show()
