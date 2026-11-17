"""
FOOD PLANT AI - AI Quality Prediction Page
Interactive machine learning quality inference for new production batches.
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import database
from prediction import predict


def show():
    st.markdown("""
        <div class="plant-header">
            <h1 class="plant-title">🤖 AI Quality Prediction</h1>
            <span class="plant-tag">ML INFERENCE ENGINE</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    > ⚠️ **Decision Support Notice:** This AI system provides probabilistic quality risk assessment.
    > It is designed to assist quality supervisors and **must not replace** certified sensory, microbiological,
    > or laboratory testing required under regulatory standards.
    """)

    # Check model existence
    model_path = os.path.join(os.path.dirname(__file__), "..", "models", "quality_model.pkl")
    if not os.path.exists(model_path):
        st.error("⚠️ Trained ML model not found. Please train the model using `python src/train_model.py` or through the Dataset page.")
        return

    # Load suppliers from DB
    suppliers = database.get_all_suppliers()
    supplier_names = [s["Supplier_Name"] for s in suppliers] if suppliers else ["Hyderabad Spice Traders"]

    with st.form("ai_prediction_form"):
        st.subheader("⚙️ Production Batch Parameters")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            batch_id = st.text_input("Batch Identification Number *", value=f"BCH-PRED-{datetime.now().strftime('%H%M%S')}")
            prod_line = st.selectbox("Production Line *", ["Line 1", "Line 2", "Line 3"])
            supplier = st.selectbox("Raw Material Supplier *", supplier_names)
        with c2:
            spice_type = st.selectbox("Spice Type *", ["Chilli Powder", "Turmeric Powder", "Coriander Powder", "Garam Masala"])
            raw_weight = st.number_input("Raw Material Weight *", min_value=1.0, value=750.0, step=25.0)
            weight_unit = st.selectbox("Weight Measurement Unit *", ["kg", "grams"])
        with c3:
            raw_quality = st.selectbox("Raw Material Quality Grade *", ["Grade A", "Grade B", "Grade C", "Grade D"])
            moisture = st.number_input("Moisture Level (%) *", min_value=1.0, max_value=25.0, value=8.4, step=0.1)
            prod_time = st.number_input("Batch Production Time (minutes) *", min_value=5.0, max_value=120.0, value=35.0, step=1.0)

        st.subheader("⚡ Machine Operating Conditions")
        c4, c5 = st.columns(2)
        with c4:
            temperature = st.number_input("Machine Operating Temperature (°C) *", min_value=40.0, max_value=120.0, value=74.5, step=0.5)
        with c5:
            speed = st.number_input("Machine Milling Speed (RPM) *", min_value=800.0, max_value=1800.0, value=1240.0, step=10.0)

        submitted = st.form_submit_button("🚀 PREDICT QUALITY", type="primary", use_container_width=True)

    if submitted:
        input_dict = {
            "Production_Line": prod_line,
            "Supplier_Name": supplier,
            "Spice_Type": spice_type,
            "Raw_Material_Weight": raw_weight,
            "Weight_Unit": weight_unit,
            "Moisture_Level": moisture,
            "Machine_Temperature": temperature,
            "Machine_Speed": speed,
            "Production_Time": prod_time,
            "Raw_Material_Quality": raw_quality
        }

        with st.spinner("Processing sensor inputs and running ML inference pipeline..."):
            try:
                res = predict(input_dict)
                pred_result = res["predicted_result"]
                fail_prob = res["fail_probability"]
                pass_prob = res["pass_probability"]
                risk_cat = res["risk_category"]
                factors = res["contributing_factors"]
                rec = res["recommendation"]
                infer_ms = res["inference_time_ms"]
                std_kg = res["standardized_weight_kg"]

                # Save prediction to database
                pred_id = database.save_prediction(
                    batch_id=batch_id,
                    prod_line=prod_line,
                    supplier_name=supplier,
                    spice_type=spice_type,
                    weight_kg=std_kg,
                    moisture=moisture,
                    temp=temperature,
                    speed=speed,
                    prod_time=prod_time,
                    raw_quality=raw_quality,
                    pred_result=pred_result,
                    fail_prob=fail_prob,
                    pass_prob=pass_prob,
                    risk_cat=risk_cat,
                    factors=factors,
                    recommendation=rec
                )

                st.success(f"✅ Prediction completed and persisted to database! (Prediction ID: #{pred_id})")

                # Results Display
                st.divider()
                st.subheader("🎯 Inference Outcome & Risk Assessment")

                rc1, rc2, rc3, rc4 = st.columns(4)
                with rc1:
                    if pred_result == "PASS":
                        st.markdown("""
                            <div class="kpi-card" style="border-left: 4px solid #10b981;">
                                <div class="kpi-label">Predicted Outcome</div>
                                <div class="badge-pass" style="font-size: 1.4rem; padding: 0.4rem 1rem;">PASS</div>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                            <div class="kpi-card" style="border-left: 4px solid #ef4444;">
                                <div class="kpi-label">Predicted Outcome</div>
                                <div class="badge-fail" style="font-size: 1.4rem; padding: 0.4rem 1rem;">FAIL</div>
                            </div>
                        """, unsafe_allow_html=True)

                with rc2:
                    st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-label">Failure Probability</div>
                            <div class="kpi-value" style="color: {'#ef4444' if fail_prob > 0.5 else '#1e293b'};">{fail_prob * 100:.1f}%</div>
                            <div class="kpi-subtext">Pass: {pass_prob * 100:.1f}%</div>
                        </div>
                    """, unsafe_allow_html=True)

                with rc3:
                    risk_badge_class = "badge-risk-low" if risk_cat == "LOW" else ("badge-risk-med" if risk_cat == "MEDIUM" else "badge-risk-high")
                    st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-label">Risk Category</div>
                            <div style="margin-top: 0.25rem;"><span class="{risk_badge_class}" style="font-size: 1.1rem; padding: 0.3rem 0.8rem;">{risk_cat} RISK</span></div>
                            <div class="kpi-subtext">Threshold tier</div>
                        </div>
                    """, unsafe_allow_html=True)

                with rc4:
                    st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-label">Inference Latency</div>
                            <div class="kpi-value">{infer_ms:.1f} ms</div>
                            <div class="kpi-subtext">Local CPU compute</div>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Explanations & Recommendations
                st.subheader("🔍 Contributing Factors & Inspection Advice")
                st.info(f"**Identified Factors:** {factors}")

                if risk_cat == "HIGH":
                    st.error(f"🛑 **Inspector Recommendation:** {rec}")
                elif risk_cat == "MEDIUM":
                    st.warning(f"⚠️ **Inspector Recommendation:** {rec}")
                else:
                    st.success(f"✅ **Inspector Recommendation:** {rec}")

            except Exception as e:
                st.error(f"❌ Error during inference: {e}")


show()
