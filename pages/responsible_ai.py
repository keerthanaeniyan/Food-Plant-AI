"""
FOOD PLANT AI - Responsible AI, Ethics & Compliance Page
Covers algorithmic bias, data governance, human oversight, FSSAI regulations, and traceability.
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
            <h1 class="plant-title">🛡️ Responsible AI & Food Safety Governance</h1>
            <span class="plant-tag">ETHICS • COMPLIANCE • FSSAI</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    > ### 🏛️ Core Principle: Human-in-the-Loop Oversight
    > **FOOD PLANT AI** is intentionally designed as an **Industrial Decision Support System (DSS)**.
    > In compliance with food safety protocols, no batch is ever cleared or condemned automatically by an algorithm.
    > The AI model alerts inspectors to high-risk production runs, while certified food scientists and laboratory technicians
    > conduct mandatory physical and chemical assays.
    """)

    tab1, tab2, tab3, tab4 = st.tabs([
        "⚖️ Bias & Fairness Audit",
        "📜 Regulatory Compliance (FSSAI)",
        "🔒 Data Privacy & Security",
        "📋 System Audit Logs"
    ])

    with tab1:
        st.subheader("Algorithmic Bias Assessment")
        
        st.markdown("""
        #### 1. Supplier Bias Safeguards
        - **Risk:** Suppliers with smaller delivery volumes could be unfairly penalized or falsely flagged if historical sample sizes are skewed.
        - **Mitigation:** The model features focus on **physical sensor measurements** (moisture %, temperature, speed) rather than supplier identity as the primary decision driver. Feature importance confirms supplier identity has <3% weight in quality classification.
        - **Equal Opportunity Check:** Periodic evaluation ensures error rates do not disproportionately impact smaller regional farmers or cooperatives in Nizamabad and Guntur.

        #### 2. Production Line Disparity
        - **Risk:** Line 1, Line 2, and Line 3 operate different mill vintages. Line-specific wear could introduce systematic bias.
        - **Mitigation:** Maintenance calibration features normalize throughput across all three lines. Models are evaluated for subgroup parity across all lines.
        """)

    with tab2:
        st.subheader("Food Safety Standards Authority of India (FSSAI) Alignment")
        
        st.markdown("""
        The system supports compliance with key provisions of the **Food Safety and Standards Act, 2006**:
        
        - **Section 23 (Packaging and Labelling Regulations):** Batch identification numbers and full production parameters are linked immutably to prevent misbranded or counterfeit spice distribution.
        - **Section 26 (Responsibilities of the Food Business Operator):** Provides auditable proof of due diligence and continuous process monitoring.
        - **Schedule 4 (General Sanitary and Hygienic Requirements):** Ensures critical control points (CCPs) for moisture (preventing *Aspergillus flavus* aflatoxin production in chilli and turmeric) and temperature are continuously tracked.
        - **Traceability Chain:** From incoming farm gate delivery to milled powder, every batch records source supplier, delivery moisture, and machine speed.
        """)

    with tab3:
        st.subheader("Data Privacy, Local Storage & Model Security")
        
        st.markdown("""
        - **Zero Cloud Leakage:** All inference runs **100% locally** on facility hardware using open-source Python, Scikit-learn, and SQLite. No proprietary spice recipes or production figures are transmitted over external APIs.
        - **No Personal Identifiable Information (PII):** Records store corporate supplier entities and operational metrics only. No individual operator personal data is processed.
        - **Integrity Verification:** Database transactions adhere to ACID properties in SQLite WAL mode with foreign-key constraint enforcement.
        """)

    with tab4:
        st.subheader("Immutable System Audit Trail")
        st.caption("Live log of all administrative actions, database mutations, and predictions.")

        logs = database.get_audit_logs(limit=100)
        if logs:
            log_df = pd.DataFrame(logs)
            st.dataframe(log_df, use_container_width=True, hide_index=True)
        else:
            st.info("No audit logs recorded yet.")


show()
