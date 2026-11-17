"""
FOOD PLANT AI — Dataset Management Page
Upload, download, preview, and inspect production datasets.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import database

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RAW_PATH     = os.path.join(DATA_DIR, "raw_production_data.csv")
CLEANED_PATH = os.path.join(DATA_DIR, "cleaned_production_data.csv")

REQUIRED_COLS = [
    "Batch_ID", "Production_Date", "Production_Line", "Supplier_Name",
    "Spice_Type", "Raw_Material_Weight", "Weight_Unit", "Moisture_Level",
    "Machine_Temperature", "Machine_Speed", "Production_Time",
    "Raw_Material_Quality", "Final_Product_Weight", "Quality_Result"
]


def show():
    st.markdown("""
        <div class="plant-header">
            <h1 class="plant-title">📁 Dataset Management</h1>
            <span class="plant-tag">DATA OPERATIONS</span>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dataset Overview",
        "⬆️ Upload CSV",
        "⬇️ Download CSV",
        "🧹 Data Quality"
    ])

    with tab1:
        _overview()
    with tab2:
        _upload()
    with tab3:
        _download()
    with tab4:
        _quality()


def _load_df(path):
    if not os.path.exists(path):
        return None
    try:
        return pd.read_csv(path, comment="#", low_memory=False, nrows=5000)
    except Exception:
        return None


def _overview():
    st.subheader("📊 Dataset Overview")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Raw Dataset**")
        if os.path.exists(RAW_PATH):
            size_mb = os.path.getsize(RAW_PATH) / 1024 / 1024
            # Count rows without loading everything
            with open(RAW_PATH, "r") as f:
                n_rows = sum(1 for _ in f) - 2  # subtract header + comment
            st.metric("Raw Records", f"{n_rows:,}")
            st.caption(f"File size: {size_mb:.1f} MB")
        else:
            st.info("raw_production_data.csv not found. Run `python src/data_generator.py`")

    with col2:
        st.markdown("**Cleaned Dataset**")
        if os.path.exists(CLEANED_PATH):
            size_mb = os.path.getsize(CLEANED_PATH) / 1024 / 1024
            with open(CLEANED_PATH, "r") as f:
                n_rows = sum(1 for _ in f) - 1
            st.metric("Cleaned Records", f"{n_rows:,}")
            st.caption(f"File size: {size_mb:.1f} MB")
        else:
            st.info("cleaned_production_data.csv not found. Run `python src/preprocessing.py`")

    st.divider()

    df = _load_df(CLEANED_PATH) or _load_df(RAW_PATH)
    if df is None:
        st.info("No dataset files found.")
        return

    st.subheader("Preview (first 20 rows)")
    st.dataframe(df.head(20), use_container_width=True, hide_index=True)

    st.subheader("Column Information")
    col_info = pd.DataFrame({
        "Column": df.columns,
        "Data Type": [str(df[c].dtype) for c in df.columns],
        "Non-Null Count": [df[c].notna().sum() for c in df.columns],
        "Missing Count": [df[c].isna().sum() for c in df.columns],
        "Missing %": [f"{df[c].isna().mean()*100:.1f}%" for c in df.columns],
        "Unique Values": [df[c].nunique() for c in df.columns],
    })
    st.dataframe(col_info, use_container_width=True, hide_index=True)


def _upload():
    st.subheader("⬆️ Upload Production CSV")
    st.info("Required columns: " + ", ".join(REQUIRED_COLS))

    uploaded = st.file_uploader("Choose a CSV file", type=["csv"])
    if uploaded is None:
        return

    try:
        df = pd.read_csv(uploaded, comment="#", low_memory=False)
    except Exception as e:
        st.error(f"❌ Failed to parse CSV: {e}")
        return

    missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing_cols:
        st.error(f"❌ Validation failed — missing columns: {missing_cols}")
        return

    st.success(f"✅ File validated — {len(df):,} rows, {len(df.columns)} columns")
    st.dataframe(df.head(10), use_container_width=True, hide_index=True)

    if os.path.exists(CLEANED_PATH):
        overwrite = st.checkbox("⚠️ Cleaned dataset exists. I confirm I want to import and merge this data.")
    else:
        overwrite = True

    if st.button("📥 Import to Database", type="primary", disabled=not overwrite):
        suppliers = database.get_all_suppliers()
        sup_map = {s["Supplier_Name"]: s["Supplier_ID"] for s in suppliers}

        progress = st.progress(0)
        imported = 0
        errors   = 0
        total    = len(df)

        for i, row in df.iterrows():
            try:
                database.add_production_batch(
                    batch_id=str(row.get("Batch_ID", f"IMP-{i}")),
                    prod_date=str(row.get("Production_Date", "2024-01-01")),
                    prod_line=str(row.get("Production_Line", "Line 1")),
                    supplier_id=sup_map.get(str(row.get("Supplier_Name", "")), None),
                    supplier_name=str(row.get("Supplier_Name", "Unknown")),
                    spice_type=str(row.get("Spice_Type", "Chilli Powder")),
                    raw_weight=float(row.get("Raw_Material_Weight", 500)),
                    weight_unit=str(row.get("Weight_Unit", "kg")),
                    moisture=float(row.get("Moisture_Level", 8.5)),
                    temperature=float(row.get("Machine_Temperature", 75)),
                    speed=float(row.get("Machine_Speed", 1250)),
                    prod_time=float(row.get("Production_Time", 35)),
                    raw_quality=str(row.get("Raw_Material_Quality", "Grade A")),
                    final_weight=float(row.get("Final_Product_Weight", 450)),
                    quality_result=str(row.get("Quality_Result", "PASS"))
                )
                imported += 1
            except Exception:
                errors += 1

            if (i + 1) % 100 == 0 or (i + 1) == total:
                progress.progress((i + 1) / total)

        st.success(f"✅ Import complete: {imported:,} records added, {errors} errors.")


def _download():
    st.subheader("⬇️ Download Datasets")

    if os.path.exists(CLEANED_PATH):
        with open(CLEANED_PATH, "rb") as f:
            st.download_button("📥 Download Cleaned Dataset (cleaned_production_data.csv)",
                               f.read(), file_name="cleaned_production_data.csv", mime="text/csv")

    if os.path.exists(RAW_PATH):
        with open(RAW_PATH, "rb") as f:
            st.download_button("📥 Download Raw Dataset (raw_production_data.csv)",
                               f.read(), file_name="raw_production_data.csv", mime="text/csv")

    st.divider()
    st.subheader("Export Current DB Records")
    batches = database.get_production_batches(limit=200000)
    if batches:
        df = pd.DataFrame(batches)
        csv = df.to_csv(index=False)
        st.download_button("📥 Export Production Batches from Database",
                           csv, file_name="db_production_batches.csv", mime="text/csv")
    else:
        st.info("No production batches in database to export.")


def _quality():
    st.subheader("🧹 Data Quality Report")
    df = _load_df(CLEANED_PATH)
    raw_df = _load_df(RAW_PATH)
    if df is None:
        st.info("No cleaned dataset found. Run `python src/preprocessing.py`")
        return

    col1, col2, col3 = st.columns(3)
    raw_rows  = sum(1 for _ in open(RAW_PATH)) - 2 if os.path.exists(RAW_PATH) else "N/A"
    clean_rows = sum(1 for _ in open(CLEANED_PATH)) - 1 if os.path.exists(CLEANED_PATH) else "N/A"
    removed    = (raw_rows - clean_rows) if isinstance(raw_rows, int) and isinstance(clean_rows, int) else "N/A"

    with col1:
        st.metric("Raw Records", f"{raw_rows:,}" if isinstance(raw_rows, int) else str(raw_rows))
    with col2:
        st.metric("Cleaned Records", f"{clean_rows:,}" if isinstance(clean_rows, int) else str(clean_rows))
    with col3:
        st.metric("Duplicates Removed", f"{removed:,}" if isinstance(removed, int) else str(removed))

    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        fig = px.bar(x=missing.index, y=missing.values,
                     labels={"x": "Column", "y": "Missing Count"},
                     title="Missing Values by Column", template="plotly_white",
                     color=missing.values, color_continuous_scale="Reds")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("✅ No missing values in cleaned dataset!")

    if "Quality_Result" in df.columns:
        qd = df["Quality_Result"].value_counts().reset_index()
        qd.columns = ["Result", "Count"]
        fig2 = px.pie(qd, names="Result", values="Count",
                      color="Result", color_discrete_map={"PASS": "#2563eb", "FAIL": "#dc2626"},
                      title="Quality Distribution")
        st.plotly_chart(fig2, use_container_width=True)


show()
