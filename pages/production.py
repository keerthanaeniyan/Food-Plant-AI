"""
FOOD PLANT AI - Production Management Page
Complete CRUD operations for manufacturing batch records.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import database

# ============================================================
# Helper: Spice & Line Options
# ============================================================
SPICE_TYPES = ["Chilli Powder", "Turmeric Powder", "Coriander Powder", "Garam Masala"]
PROD_LINES = ["Line 1", "Line 2", "Line 3"]
WEIGHT_UNITS = ["kg", "grams"]
QUALITY_GRADES = ["Grade A", "Grade B", "Grade C", "Grade D"]
QUALITY_RESULTS = ["PASS", "FAIL"]


def _supplier_options(db_path=None) -> dict:
    """Returns {name: supplier_id} dict from live database."""
    kw = {"db_path": db_path} if db_path else {}
    suppliers = database.get_all_suppliers(**kw)
    return {s["Supplier_Name"]: s["Supplier_ID"] for s in suppliers}


# ============================================================
# Main Production Management Page
# ============================================================
def show():
    st.markdown("""
        <div class="plant-header">
            <h1 class="plant-title">🏭 Production Management</h1>
            <span class="plant-tag">CRUD • BATCH RECORDS</span>
        </div>
    """, unsafe_allow_html=True)

    # Sub-tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 View & Search Batches",
        "➕ Add New Batch",
        "✏️ Edit Batch",
        "🗑️ Delete Batch"
    ])

    with tab1:
        view_batches_tab()

    with tab2:
        add_batch_tab()

    with tab3:
        edit_batch_tab()

    with tab4:
        delete_batch_tab()


# ============================================================
# TAB 1 — VIEW & SEARCH
# ============================================================
def view_batches_tab():
    st.subheader("🔍 Search & Filter Batches")

    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.text_input("🔎 Search by Batch ID, Supplier or Spice Type", placeholder="e.g. BCH-001, Guntur, Chilli")
    with col2:
        status_filter = st.selectbox("Quality Status", ["All", "PASS", "FAIL"])

    col3, col4, col5, col6 = st.columns(4)
    with col3:
        line_filter = st.selectbox("Production Line", ["All"] + PROD_LINES)
    with col4:
        spice_filter = st.selectbox("Spice Type", ["All"] + SPICE_TYPES)
    with col5:
        start_date = st.date_input("From Date", value=None)
    with col6:
        end_date = st.date_input("To Date", value=None)

    batches = database.get_production_batches(
        query=query or None,
        production_line=line_filter,
        spice_type=spice_filter,
        quality_status=status_filter,
        start_date=str(start_date) if start_date else None,
        end_date=str(end_date) if end_date else None,
        limit=500
    )

    st.markdown(f"**{len(batches)} records found**")

    if not batches:
        st.info("No production batches found. Add a batch using the **Add New Batch** tab.")
        return

    df = pd.DataFrame(batches)
    # Format for display
    display_cols = [
        "Record_ID", "Batch_ID", "Production_Date", "Production_Line",
        "Supplier_Name", "Spice_Type", "Standardized_Weight_Kg",
        "Moisture_Level", "Machine_Temperature", "Machine_Speed",
        "Production_Time", "Raw_Material_Quality", "Actual_Quality_Result"
    ]
    display_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

    # Export button
    csv_data = df.to_csv(index=False)
    st.download_button(
        "⬇️ Export to CSV",
        csv_data,
        file_name=f"production_batches_{date.today()}.csv",
        mime="text/csv"
    )


# ============================================================
# TAB 2 — ADD BATCH
# ============================================================
def add_batch_tab():
    st.subheader("➕ Add New Production Batch")

    supplier_map = _supplier_options()
    supplier_names = list(supplier_map.keys())

    with st.form("add_batch_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            batch_id = st.text_input("Batch Number *", placeholder="e.g. BCH-2025-001")
            prod_date = st.date_input("Production Date *", value=date.today())
            prod_line = st.selectbox("Production Line *", PROD_LINES)
            supplier_name = st.selectbox("Supplier *", supplier_names if supplier_names else ["No suppliers — add one first"])
            spice_type = st.selectbox("Spice Type *", SPICE_TYPES)
        with col2:
            raw_weight = st.number_input("Raw Material Weight *", min_value=0.1, value=500.0, step=10.0)
            weight_unit = st.selectbox("Weight Unit *", WEIGHT_UNITS)
            moisture = st.number_input("Moisture Level (%) *", min_value=0.0, max_value=30.0, value=8.5, step=0.1)
            temperature = st.number_input("Machine Temperature (°C) *", min_value=20.0, max_value=150.0, value=75.0, step=0.5)
            speed = st.number_input("Machine Speed (RPM) *", min_value=100.0, max_value=3000.0, value=1250.0, step=10.0)

        col3, col4 = st.columns(2)
        with col3:
            prod_time = st.number_input("Production Time (minutes) *", min_value=1.0, max_value=240.0, value=35.0, step=1.0)
            raw_quality = st.selectbox("Raw Material Quality *", QUALITY_GRADES)
        with col4:
            final_weight = st.number_input("Final Product Weight (kg) *", min_value=0.1, value=450.0, step=10.0)
            quality_result = st.selectbox("Actual Quality Result *", QUALITY_RESULTS)

        submitted = st.form_submit_button("💾 Save Batch", type="primary")

        if submitted:
            if not batch_id.strip():
                st.error("❌ Batch number is required.")
            elif not supplier_names:
                st.error("❌ Please add at least one supplier before adding batches.")
            else:
                supplier_id = supplier_map.get(supplier_name)
                record_id = database.add_production_batch(
                    batch_id=batch_id.strip().upper(),
                    prod_date=str(prod_date),
                    prod_line=prod_line,
                    supplier_id=supplier_id,
                    supplier_name=supplier_name,
                    spice_type=spice_type,
                    raw_weight=raw_weight,
                    weight_unit=weight_unit,
                    moisture=moisture,
                    temperature=temperature,
                    speed=speed,
                    prod_time=prod_time,
                    raw_quality=raw_quality,
                    final_weight=final_weight,
                    quality_result=quality_result
                )
                st.success(f"✅ Batch **{batch_id.upper()}** saved successfully! (Record ID: {record_id})")


# ============================================================
# TAB 3 — EDIT BATCH
# ============================================================
def edit_batch_tab():
    st.subheader("✏️ Edit Existing Batch")

    batches = database.get_production_batches(limit=500)
    if not batches:
        st.info("No batches available to edit.")
        return

    df = pd.DataFrame(batches)
    batch_options = {
        f"Record #{r['Record_ID']} | {r['Batch_ID']} | {r['Spice_Type']} | {r['Production_Date']}": r['Record_ID']
        for r in batches
    }
    selected_label = st.selectbox("Select Batch to Edit", list(batch_options.keys()))
    selected_id = batch_options[selected_label]

    record = next((r for r in batches if r['Record_ID'] == selected_id), None)
    if not record:
        st.error("Batch record not found.")
        return

    supplier_map = _supplier_options()
    supplier_names = list(supplier_map.keys())

    with st.form("edit_batch_form"):
        col1, col2 = st.columns(2)
        with col1:
            batch_id = st.text_input("Batch Number *", value=record["Batch_ID"])
            prod_date_str = record.get("Production_Date", str(date.today()))
            try:
                prod_date_val = date.fromisoformat(prod_date_str)
            except Exception:
                prod_date_val = date.today()
            prod_date = st.date_input("Production Date *", value=prod_date_val)
            prod_line = st.selectbox("Production Line *", PROD_LINES,
                                     index=PROD_LINES.index(record["Production_Line"]) if record["Production_Line"] in PROD_LINES else 0)
            supplier_name_default = record.get("Supplier_Name", supplier_names[0] if supplier_names else "")
            supplier_name = st.selectbox("Supplier *", supplier_names,
                                         index=supplier_names.index(supplier_name_default) if supplier_name_default in supplier_names else 0)
            spice_type = st.selectbox("Spice Type *", SPICE_TYPES,
                                      index=SPICE_TYPES.index(record["Spice_Type"]) if record["Spice_Type"] in SPICE_TYPES else 0)
        with col2:
            raw_weight = st.number_input("Raw Material Weight *", min_value=0.1, value=float(record.get("Raw_Material_Weight", 500.0)), step=10.0)
            weight_unit = st.selectbox("Weight Unit *", WEIGHT_UNITS,
                                       index=WEIGHT_UNITS.index(record["Weight_Unit"]) if record.get("Weight_Unit") in WEIGHT_UNITS else 0)
            moisture = st.number_input("Moisture Level (%) *", min_value=0.0, max_value=30.0, value=float(record.get("Moisture_Level", 8.5)), step=0.1)
            temperature = st.number_input("Machine Temperature (°C) *", min_value=20.0, max_value=150.0, value=float(record.get("Machine_Temperature", 75.0)), step=0.5)
            speed = st.number_input("Machine Speed (RPM) *", min_value=100.0, max_value=3000.0, value=float(record.get("Machine_Speed", 1250.0)), step=10.0)

        col3, col4 = st.columns(2)
        with col3:
            prod_time = st.number_input("Production Time (minutes) *", min_value=1.0, max_value=240.0, value=float(record.get("Production_Time", 35.0)), step=1.0)
            current_quality = record.get("Raw_Material_Quality", "Grade A")
            raw_quality = st.selectbox("Raw Material Quality *", QUALITY_GRADES,
                                       index=QUALITY_GRADES.index(current_quality) if current_quality in QUALITY_GRADES else 0)
        with col4:
            final_weight = st.number_input("Final Product Weight (kg) *", min_value=0.1, value=float(record.get("Final_Product_Weight", 450.0)), step=10.0)
            current_result = record.get("Actual_Quality_Result", "PASS")
            quality_result = st.selectbox("Actual Quality Result *", QUALITY_RESULTS,
                                          index=QUALITY_RESULTS.index(current_result) if current_result in QUALITY_RESULTS else 0)

        submitted = st.form_submit_button("💾 Update Batch", type="primary")

        if submitted:
            supplier_id = supplier_map.get(supplier_name)
            success = database.update_production_batch(
                record_id=selected_id,
                batch_id=batch_id.strip().upper(),
                prod_date=str(prod_date),
                prod_line=prod_line,
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                spice_type=spice_type,
                raw_weight=raw_weight,
                weight_unit=weight_unit,
                moisture=moisture,
                temperature=temperature,
                speed=speed,
                prod_time=prod_time,
                raw_quality=raw_quality,
                final_weight=final_weight,
                quality_result=quality_result
            )
            if success:
                st.success(f"✅ Batch Record #{selected_id} updated successfully!")
            else:
                st.error("❌ Update failed. Please try again.")


# ============================================================
# TAB 4 — DELETE BATCH
# ============================================================
def delete_batch_tab():
    st.subheader("🗑️ Delete Batch Record")
    st.warning("⚠️ **Important:** This action is permanent. The audit log will preserve a record of the deletion.")

    batches = database.get_production_batches(limit=500)
    if not batches:
        st.info("No batches available.")
        return

    batch_options = {
        f"Record #{r['Record_ID']} | {r['Batch_ID']} | {r['Spice_Type']} | {r['Actual_Quality_Result']}": r['Record_ID']
        for r in batches
    }
    selected_label = st.selectbox("Select Batch to Delete", list(batch_options.keys()))
    selected_id = batch_options[selected_label]

    record = next((r for r in batches if r['Record_ID'] == selected_id), None)
    if record:
        st.markdown(f"""
        **Selected Batch Details:**
        - **Record ID:** {record['Record_ID']}
        - **Batch ID:** {record['Batch_ID']}
        - **Spice Type:** {record['Spice_Type']}
        - **Production Line:** {record['Production_Line']}
        - **Date:** {record['Production_Date']}
        - **Quality Result:** {record['Actual_Quality_Result']}
        """)

    confirm = st.checkbox("✅ I confirm that I want to permanently delete this batch record.")

    if st.button("🗑️ Delete Batch", type="primary", disabled=not confirm):
        success = database.delete_production_batch(selected_id)
        if success:
            st.success(f"✅ Batch Record #{selected_id} deleted successfully.")
            st.rerun()
        else:
            st.error("❌ Deletion failed. Please refresh and try again.")


show()
