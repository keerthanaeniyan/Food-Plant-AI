"""
FOOD PLANT AI - Settings Page
Configuration of operational thresholds, facility details, database backups, and restoration.
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
            <h1 class="plant-title">⚙️ Facility Settings & Configuration</h1>
            <span class="plant-tag">SYSTEM PARAMETERS & BACKUPS</span>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "🎛️ Operational Limits",
        "🏭 Facility Details",
        "💾 Database Backup & Restore"
    ])

    with tab1:
        st.subheader("Configurable Machine Operating Limits")
        st.caption("These demonstration thresholds govern alerting in the Machine Monitoring module.")

        current_settings = database.get_all_settings()

        with st.form("settings_limits_form"):
            col1, col2 = st.columns(2)
            with col1:
                temp_min = st.number_input("Min Operating Temperature (°C)", value=float(current_settings.get("TEMP_LIMIT_MIN", 65.0)), step=0.5)
                temp_max = st.number_input("Max Operating Temperature (°C)", value=float(current_settings.get("TEMP_LIMIT_MAX", 85.0)), step=0.5)
                moist_max = st.number_input("Max Acceptable Moisture Level (%)", value=float(current_settings.get("MOISTURE_LIMIT_MAX", 12.0)), step=0.1)
            with col2:
                speed_min = st.number_input("Min Milling Speed (RPM)", value=float(current_settings.get("SPEED_LIMIT_MIN", 1100.0)), step=25.0)
                speed_max = st.number_input("Max Milling Speed (RPM)", value=float(current_settings.get("SPEED_LIMIT_MAX", 1450.0)), step=25.0)
                time_max = st.number_input("Max Standard Cycle Time (min)", value=float(current_settings.get("PROD_TIME_MAX", 55.0)), step=1.0)

            save_limits = st.form_submit_button("💾 Save Operational Limits", type="primary")

            if save_limits:
                database.update_setting("TEMP_LIMIT_MIN", str(temp_min))
                database.update_setting("TEMP_LIMIT_MAX", str(temp_max))
                database.update_setting("SPEED_LIMIT_MIN", str(speed_min))
                database.update_setting("SPEED_LIMIT_MAX", str(speed_max))
                database.update_setting("MOISTURE_LIMIT_MAX", str(moist_max))
                database.update_setting("PROD_TIME_MAX", str(time_max))
                st.success("✅ Operational limits updated successfully!")

    with tab2:
        st.subheader("Plant & Facility Information")
        with st.form("facility_info_form"):
            company = st.text_input("Facility / Enterprise Name", value=current_settings.get("COMPANY_NAME", "SpiceCraft Hyderabad Pvt Ltd"))
            location = st.text_input("Plant Physical Address", value=current_settings.get("FACILITY_LOCATION", "Kattedan Industrial Area, Hyderabad"))
            lines = st.text_input("Active Production Lines (comma-separated)", value=current_settings.get("ACTIVE_LINES", "Line 1,Line 2,Line 3"))

            save_facility = st.form_submit_button("💾 Save Facility Details", type="primary")
            if save_facility:
                database.update_setting("COMPANY_NAME", company)
                database.update_setting("FACILITY_LOCATION", location)
                database.update_setting("ACTIVE_LINES", lines)
                st.success("✅ Facility details updated successfully!")

    with tab3:
        st.subheader("Database Backup & Disaster Recovery")
        st.caption("Creates an atomic, consistent SQLite WAL backup snapshot.")

        if st.button("📦 Create Instant Database Snapshot", type="primary"):
            backup_path = database.backup_database()
            st.success(f"✅ Backup created successfully at:\n`{backup_path}`")

        st.divider()

        st.subheader("Restore from Available Backups")
        backups = database.list_backups()
        if backups:
            backup_options = {os.path.basename(b): b for b in backups}
            selected_backup_name = st.selectbox("Select Snapshot to Restore", list(backup_options.keys()))
            selected_backup_path = backup_options[selected_backup_name]

            st.warning("⚠️ Restoring a database replaces the current database state with the backup snapshot.")
            confirm_restore = st.checkbox("I understand and confirm restoring this snapshot.")

            if st.button("🔄 Restore Selected Backup", disabled=not confirm_restore):
                success = database.restore_database(selected_backup_path)
                if success:
                    st.success(f"✅ Database successfully restored from {selected_backup_name}!")
                    st.rerun()
                else:
                    st.error("Restore failed.")
        else:
            st.info("No backups found in the backups/ directory. Click 'Create Instant Database Snapshot' above.")


show()
