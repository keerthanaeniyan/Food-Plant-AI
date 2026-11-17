"""
FOOD PLANT AI - Raw Material Management Page
Complete CRUD operations for raw material inventory.
"""

import streamlit as st
import pandas as pd
from datetime import date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import database

QUALITY_GRADES = ["Grade A", "Grade B", "Grade C", "Grade D"]
WEIGHT_UNITS = ["kg", "grams"]
INSPECTION_RESULTS = ["PASS", "FAIL", "PENDING"]


def _update_raw_material(mat_id, name, supplier_id, supplier_name, qty, unit, std_kg,
                          purchase_date, moisture, grade, inspection):
    from datetime import datetime
    now = datetime.now().isoformat()
    with database.get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE Raw_Materials SET
                Material_Name=?, Supplier_ID=?, Supplier_Name=?,
                Quantity=?, Unit=?, Standardized_Quantity_Kg=?,
                Purchase_Date=?, Moisture_Level=?, Quality_Grade=?, Inspection_Result=?
            WHERE Material_ID=?
        """, (name, supplier_id, supplier_name, qty, unit, std_kg,
              purchase_date, moisture, grade, inspection, mat_id))
        conn.commit()
    database.log_audit("UPDATE", "Raw_Materials", mat_id, f"Updated material {name}")


def _delete_raw_material(mat_id, mat_name):
    with database.get_db_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM Raw_Materials WHERE Material_ID=?", (mat_id,))
        conn.commit()
    database.log_audit("DELETE", "Raw_Materials", mat_id, f"Deleted material {mat_name}")


def show():
    st.markdown("""
        <div class="plant-header">
            <h1 class="plant-title">📦 Raw Material Management</h1>
            <span class="plant-tag">INVENTORY CONTROL</span>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 View Materials",
        "➕ Add Material",
        "✏️ Edit Material",
        "🗑️ Delete Material"
    ])

    with tab1:
        _view_materials()
    with tab2:
        _add_material()
    with tab3:
        _edit_material()
    with tab4:
        _delete_material()


def _view_materials():
    st.subheader("🔍 Material Inventory")
    col1, col2 = st.columns(2)
    with col1:
        query = st.text_input("Search by material name or supplier", placeholder="e.g. Chilli, Guntur")
    with col2:
        suppliers = database.get_all_suppliers()
        sup_names = ["All"] + [s["Supplier_Name"] for s in suppliers]
        sup_filter = st.selectbox("Filter by Supplier", sup_names)

    materials = database.get_all_raw_materials()
    if not materials:
        st.info("No raw materials recorded. Use **Add Material** tab to log incoming shipments.")
        return

    df = pd.DataFrame(materials)
    if query:
        mask = (df["Material_Name"].str.contains(query, case=False, na=False) |
                df["Supplier_Name"].str.contains(query, case=False, na=False))
        df = df[mask]
    if sup_filter != "All":
        df = df[df["Supplier_Name"] == sup_filter]

    display_cols = ["Material_Code", "Material_Name", "Supplier_Name", "Quantity", "Unit",
                    "Standardized_Quantity_Kg", "Purchase_Date", "Moisture_Level",
                    "Quality_Grade", "Inspection_Result"]
    display_cols = [c for c in display_cols if c in df.columns]
    st.markdown(f"**{len(df)} material records found**")
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False)
    st.download_button("⬇️ Export CSV", csv, file_name="raw_materials.csv", mime="text/csv")


def _add_material():
    st.subheader("➕ Log New Raw Material Shipment")
    suppliers = database.get_all_suppliers()
    sup_names = [s["Supplier_Name"] for s in suppliers]
    sup_map = {s["Supplier_Name"]: s["Supplier_ID"] for s in suppliers}

    with st.form("add_material_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Material Name *", placeholder="e.g. Dry Red Chilli")
            supplier_name = st.selectbox("Supplier *", sup_names if sup_names else ["No suppliers — add one first"])
            qty = st.number_input("Quantity *", min_value=0.1, value=1000.0, step=10.0)
            unit = st.selectbox("Unit *", WEIGHT_UNITS)
        with col2:
            purchase_date = st.date_input("Purchase Date *", value=date.today())
            moisture = st.number_input("Moisture Level (%)", min_value=0.0, max_value=30.0, value=8.5, step=0.1)
            grade = st.selectbox("Quality Grade *", QUALITY_GRADES)
            inspection = st.selectbox("Inspection Result *", INSPECTION_RESULTS)

        submitted = st.form_submit_button("💾 Save Material", type="primary")
        if submitted:
            if not name.strip() or not sup_names:
                st.error("❌ Material name and a registered supplier are required.")
            else:
                sid = sup_map.get(supplier_name)
                mid = database.add_raw_material(
                    name.strip(), sid, supplier_name, qty, unit,
                    str(purchase_date), moisture, grade, inspection
                )
                std = qty if unit == "kg" else qty / 1000
                st.success(f"✅ **{name}** logged! ({std:.1f} kg standardized, Material ID: {mid})")


def _edit_material():
    st.subheader("✏️ Edit Material Record")
    materials = database.get_all_raw_materials()
    if not materials:
        st.info("No materials available to edit.")
        return

    opts = {f"MAT-{m['Material_ID']} | {m['Material_Name']} | {m['Supplier_Name']}": m["Material_ID"]
            for m in materials}
    selected = st.selectbox("Select Material to Edit", list(opts.keys()))
    mat_id = opts[selected]
    rec = next(m for m in materials if m["Material_ID"] == mat_id)

    suppliers = database.get_all_suppliers()
    sup_names = [s["Supplier_Name"] for s in suppliers]
    sup_map = {s["Supplier_Name"]: s["Supplier_ID"] for s in suppliers}

    with st.form("edit_material_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Material Name *", value=rec.get("Material_Name", ""))
            cur_sup = rec.get("Supplier_Name", sup_names[0] if sup_names else "")
            supplier_name = st.selectbox("Supplier *", sup_names,
                                         index=sup_names.index(cur_sup) if cur_sup in sup_names else 0)
            qty = st.number_input("Quantity *", min_value=0.1, value=float(rec.get("Quantity", 1000.0)))
            unit = st.selectbox("Unit *", WEIGHT_UNITS,
                                 index=WEIGHT_UNITS.index(rec.get("Unit", "kg")) if rec.get("Unit") in WEIGHT_UNITS else 0)
        with col2:
            try:
                pd_val = date.fromisoformat(rec.get("Purchase_Date", str(date.today())))
            except Exception:
                pd_val = date.today()
            purchase_date = st.date_input("Purchase Date *", value=pd_val)
            moisture = st.number_input("Moisture Level (%)", min_value=0.0, max_value=30.0,
                                        value=float(rec.get("Moisture_Level", 8.5)))
            cur_grade = rec.get("Quality_Grade", "Grade A")
            grade = st.selectbox("Quality Grade *", QUALITY_GRADES,
                                  index=QUALITY_GRADES.index(cur_grade) if cur_grade in QUALITY_GRADES else 0)
            cur_insp = rec.get("Inspection_Result", "PASS")
            inspection = st.selectbox("Inspection Result *", INSPECTION_RESULTS,
                                       index=INSPECTION_RESULTS.index(cur_insp) if cur_insp in INSPECTION_RESULTS else 0)

        submitted = st.form_submit_button("💾 Update Material", type="primary")
        if submitted:
            sid = sup_map.get(supplier_name)
            std_kg = qty if unit == "kg" else qty / 1000
            _update_raw_material(mat_id, name, sid, supplier_name, qty, unit, std_kg,
                                  str(purchase_date), moisture, grade, inspection)
            st.success(f"✅ Material **{name}** updated successfully!")


def _delete_material():
    st.subheader("🗑️ Remove Material Record")
    materials = database.get_all_raw_materials()
    if not materials:
        st.info("No materials available.")
        return

    opts = {f"MAT-{m['Material_ID']} | {m['Material_Name']} | {m['Supplier_Name']}": m["Material_ID"]
            for m in materials}
    selected = st.selectbox("Select Material to Delete", list(opts.keys()))
    mat_id = opts[selected]
    rec = next(m for m in materials if m["Material_ID"] == mat_id)

    st.markdown(f"""
    **Material:** {rec['Material_Name']}  
    **Supplier:** {rec['Supplier_Name']}  
    **Quantity:** {rec['Quantity']} {rec['Unit']}  
    **Purchase Date:** {rec.get('Purchase_Date', '—')}
    """)

    confirm = st.checkbox("✅ I confirm deletion of this raw material record.")
    if st.button("🗑️ Delete Material", type="primary", disabled=not confirm):
        _delete_raw_material(mat_id, rec["Material_Name"])
        st.success(f"✅ Material **{rec['Material_Name']}** deleted.")
        st.rerun()


show()
