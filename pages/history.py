"""
FOOD PLANT AI - Prediction History Page
Audit log of all model inferences with ability to record actual laboratory results.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import database


def show():
    st.markdown("""
        <div class="plant-header">
            <h1 class="plant-title">📜 Prediction History</h1>
            <span class="plant-tag">MODEL AUDIT & GROUND TRUTH TRACKING</span>
        </div>
    """, unsafe_allow_html=True)

    records = database.get_prediction_history(limit=500)

    if not records:
        st.info("No AI predictions have been made yet. Visit the **AI Quality Prediction** page to generate inference records.")
        return

    df = pd.DataFrame(records)

    # Top search and filters
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        query = st.text_input("🔍 Search Batch ID or Supplier", placeholder="e.g. BCH, Hyderabad")
    with c2:
        line_filter = st.selectbox("Filter Production Line", ["All"] + sorted(list(df["Production_Line"].dropna().unique())))
    with c3:
        spice_filter = st.selectbox("Filter Spice Type", ["All"] + sorted(list(df["Spice_Type"].dropna().unique())))
    with c4:
        result_filter = st.selectbox("Predicted Result", ["All", "PASS", "FAIL"])

    # Apply filters
    filtered_df = df.copy()
    if query:
        filtered_df = filtered_df[
            filtered_df["Batch_ID"].astype(str).str.contains(query, case=False, na=False) |
            filtered_df["Supplier_Name"].astype(str).str.contains(query, case=False, na=False)
        ]
    if line_filter != "All":
        filtered_df = filtered_df[filtered_df["Production_Line"] == line_filter]
    if spice_filter != "All":
        filtered_df = filtered_df[filtered_df["Spice_Type"] == spice_filter]
    if result_filter != "All":
        filtered_df = filtered_df[filtered_df["Predicted_Result"] == result_filter]

    st.markdown(f"**Showing {len(filtered_df)} of {len(df)} total logged inferences**")

    # Display columns
    cols = [
        "Prediction_ID", "Batch_ID", "Prediction_Date", "Production_Line",
        "Supplier_Name", "Spice_Type", "Raw_Material_Weight_Kg",
        "Moisture_Level", "Machine_Temperature", "Predicted_Result",
        "Failure_Probability", "Risk_Category", "Actual_Result"
    ]
    cols = [c for c in cols if c in filtered_df.columns]
    st.dataframe(filtered_df[cols], use_container_width=True, hide_index=True)

    # Export CSV
    csv_data = filtered_df.to_csv(index=False)
    st.download_button("📥 Export History CSV", csv_data, file_name="prediction_history.csv", mime="text/csv")

    st.divider()

    # Form to record Ground Truth Actual Laboratory Result
    st.subheader("🧪 Record Confirmed Laboratory Test Result")
    st.caption("Authorized QA technicians can record the verified physical lab result against the earlier model prediction.")

    with st.form("record_actual_form"):
        pred_options = {
            f"Prediction #{r['Prediction_ID']} | Batch: {r['Batch_ID']} | Pred: {r['Predicted_Result']} (Current Actual: {r.get('Actual_Result') or 'Pending'})": r['Prediction_ID']
            for _, r in filtered_df.iterrows()
        }
        
        if pred_options:
            selected_pred_key = st.selectbox("Select Inference Record", list(pred_options.keys()))
            selected_pred_id = pred_options[selected_pred_key]
            
            actual_res = st.selectbox("Confirmed Laboratory Result", ["PASS", "FAIL"])
            update_btn = st.form_submit_button("💾 Save Verified Lab Result", type="primary")

            if update_btn:
                success = database.update_prediction_actual_result(selected_pred_id, actual_res)
                if success:
                    st.success(f"✅ Recorded actual lab result '{actual_res}' for Prediction #{selected_pred_id}!")
                    st.rerun()
                else:
                    st.error("Failed to update prediction record.")
        else:
            st.info("No matching records to update.")


show()
