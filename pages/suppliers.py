"""
FOOD PLANT AI - Supplier Management Page
Complete CRUD operations for spice suppliers.
"""

import streamlit as st
import pandas as pd
from datetime import date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import database


def show():
    st.markdown("""
        <div class="plant-header">
            <h1 class="plant-title">🤝 Supplier Management</h1>
            <span class="plant-tag">SUPPLIER REGISTRY</span>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 View Suppliers",
        "➕ Add Supplier",
        "✏️ Edit Supplier",
        "🗑️ Delete Supplier"
    ])

    with tab1:
        _view_suppliers()
    with tab2:
        _add_supplier()
    with tab3:
        _edit_supplier()
    with tab4:
        _delete_supplier()


def _batch_count_per_supplier(suppliers):
    batches = database.get_production_batches(limit=100000)
    counts = {}
    for b in batches:
        name = b.get("Supplier_Name", "")
        counts[name] = counts.get(name, 0) + 1
    return counts


def _view_suppliers():
    st.subheader("🔍 Supplier Registry")
    query = st.text_input("Search supplier by name or location", placeholder="e.g. Guntur, Hyderabad")
    suppliers = database.get_all_suppliers()
    batch_counts = _batch_count_per_supplier(suppliers)

    if not suppliers:
        st.info("No suppliers found. Use the **Add Supplier** tab to register a supplier.")
        return

    rows = []
    for s in suppliers:
        if query and query.lower() not in s["Supplier_Name"].lower() and query.lower() not in (s.get("Location") or "").lower():
            continue
        rows.append({
            "Supplier Code": s["Supplier_Code"],
            "Supplier Name": s["Supplier_Name"],
            "Contact": s.get("Contact_Details", ""),
            "Location": s.get("Location", ""),
            "Materials Supplied": s.get("Material_Supplied", ""),
            "Registration Date": s.get("Registration_Date", ""),
            "Total Batches": batch_counts.get(s["Supplier_Name"], 0),
        })

    if not rows:
        st.info("No suppliers match your search.")
        return

    df = pd.DataFrame(rows)
    st.markdown(f"**{len(df)} suppliers registered**")
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False)
    st.download_button("⬇️ Export Suppliers CSV", csv, file_name="suppliers.csv", mime="text/csv")


def _add_supplier():
    st.subheader("➕ Register New Supplier")
    with st.form("add_supplier_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Supplier Name *", placeholder="e.g. Guntur Spices Co")
            contact = st.text_input("Contact Details", placeholder="+91 9XXXXXXXXX / email")
            location = st.text_input("Location", placeholder="e.g. Guntur, Andhra Pradesh")
        with col2:
            materials = st.text_area("Materials Supplied", placeholder="e.g. Red Chilli, Turmeric", height=80)
            reg_date = st.date_input("Registration Date *", value=date.today())

        submitted = st.form_submit_button("💾 Register Supplier", type="primary")
        if submitted:
            if not name.strip():
                st.error("❌ Supplier name is required.")
            else:
                # Auto-generate code
                existing = database.get_all_suppliers()
                code = f"SUP-HYD-{(len(existing) + 1):03d}"
                sid = database.add_supplier(name.strip(), contact, location, materials, str(reg_date), code=code)
                st.success(f"✅ Supplier **{name}** registered! (Code: {code}, ID: {sid})")


def _edit_supplier():
    st.subheader("✏️ Edit Supplier Details")
    suppliers = database.get_all_suppliers()
    if not suppliers:
        st.info("No suppliers available to edit.")
        return

    opts = {f"{s['Supplier_Code']} | {s['Supplier_Name']}": s["Supplier_ID"] for s in suppliers}
    selected = st.selectbox("Select Supplier to Edit", list(opts.keys()))
    sid = opts[selected]
    rec = next(s for s in suppliers if s["Supplier_ID"] == sid)

    with st.form("edit_supplier_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Supplier Name *", value=rec.get("Supplier_Name", ""))
            contact = st.text_input("Contact Details", value=rec.get("Contact_Details", ""))
            location = st.text_input("Location", value=rec.get("Location", ""))
        with col2:
            materials = st.text_area("Materials Supplied", value=rec.get("Material_Supplied", ""), height=80)
            try:
                reg_val = date.fromisoformat(rec.get("Registration_Date", str(date.today())))
            except Exception:
                reg_val = date.today()
            reg_date = st.date_input("Registration Date *", value=reg_val)

        submitted = st.form_submit_button("💾 Update Supplier", type="primary")
        if submitted:
            ok = database.update_supplier(sid, name, contact, location, materials, str(reg_date))
            if ok:
                st.success(f"✅ Supplier **{name}** updated successfully!")
            else:
                st.error("❌ Update failed.")


def _delete_supplier():
    st.subheader("🗑️ Remove Supplier")
    st.warning("⚠️ Suppliers with linked production batches or raw materials cannot be deleted.")
    suppliers = database.get_all_suppliers()
    if not suppliers:
        st.info("No suppliers available.")
        return

    opts = {f"{s['Supplier_Code']} | {s['Supplier_Name']}": s["Supplier_ID"] for s in suppliers}
    selected = st.selectbox("Select Supplier to Delete", list(opts.keys()))
    sid = opts[selected]
    rec = next(s for s in suppliers if s["Supplier_ID"] == sid)

    st.markdown(f"""
    **Supplier:** {rec['Supplier_Name']}  
    **Code:** {rec['Supplier_Code']}  
    **Location:** {rec.get('Location', '—')}  
    **Materials:** {rec.get('Material_Supplied', '—')}
    """)

    confirm = st.checkbox("✅ I confirm deletion of this supplier record.")
    if st.button("🗑️ Delete Supplier", type="primary", disabled=not confirm):
        ok, msg = database.delete_supplier(sid)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)


show()
