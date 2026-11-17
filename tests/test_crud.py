"""
Unit Tests for Production Batch and Supplier CRUD operations.
Covers add, edit, delete, search, duplicate batch numbers, audit.
"""

import os
import pytest
import database


@pytest.fixture
def db(tmp_path):
    """Clean isolated database for each test."""
    db_file = str(tmp_path / "test_crud.db")
    database.init_db(db_path=db_file)
    return db_file


# ============================================================
# SUPPLIER TESTS
# ============================================================

def test_add_supplier(db):
    """Adding a supplier returns a positive integer ID."""
    sid = database.add_supplier("Test Spice Co", "+91 9000000000", "Hyderabad", "Chilli", "2025-01-01", db_path=db)
    assert isinstance(sid, int) and sid > 0

def test_add_and_retrieve_supplier(db):
    """Retrieves a supplier by name after insertion."""
    database.add_supplier("Retrieval Spice Ltd", "+91 9000000001", "Pune", "Turmeric", "2025-01-01", db_path=db)
    suppliers = database.get_all_suppliers(db_path=db)
    names = [s["Supplier_Name"] for s in suppliers]
    assert "Retrieval Spice Ltd" in names

def test_edit_supplier(db):
    """Supplier name is updated correctly."""
    sid = database.add_supplier("Old Name Traders", "+91 9111111111", "Mumbai", "Coriander", "2025-01-15", db_path=db)
    result = database.update_supplier(sid, "New Name Traders", "+91 9111111111", "Mumbai", "Coriander", "2025-01-15", db_path=db)
    assert result is True
    suppliers = database.get_all_suppliers(db_path=db)
    assert any(s["Supplier_Name"] == "New Name Traders" for s in suppliers)

def test_delete_supplier_no_batches(db):
    """A supplier with no linked batches can be deleted."""
    sid = database.add_supplier("Orphan Supplier", "+91 9000000002", "Delhi", "Pepper", "2025-01-01", db_path=db)
    success, msg = database.delete_supplier(sid, db_path=db)
    assert success is True
    suppliers = database.get_all_suppliers(db_path=db)
    assert all(s["Supplier_ID"] != sid for s in suppliers)

def test_delete_supplier_with_batches_blocked(db):
    """Deleting a supplier referenced by a batch is blocked with a clear message."""
    sid = database.add_supplier("Linked Supplier", "+91 9000000003", "Bangalore", "Chilli", "2025-01-01", db_path=db)
    database.add_production_batch(
        "BATCH-LINK", "2025-06-01", "Line 1",
        sid, "Linked Supplier", "Chilli Powder",
        500.0, "kg", 8.0, 75.0, 1200.0, 30.0, "Grade A", 450.0, "PASS",
        db_path=db
    )
    success, msg = database.delete_supplier(sid, db_path=db)
    assert success is False
    assert "Cannot delete" in msg


# ============================================================
# PRODUCTION BATCH TESTS
# ============================================================

def test_add_production_batch(db):
    """A new batch is inserted and returns a positive Record_ID."""
    # Use a seeded supplier
    suppliers = database.get_all_suppliers(db_path=db)
    s = suppliers[0]
    rid = database.add_production_batch(
        "BCH-001", "2025-07-01", "Line 1",
        s["Supplier_ID"], s["Supplier_Name"],
        "Chilli Powder", 500.0, "kg", 8.0, 75.0, 1200.0, 30.0, "Grade A", 450.0, "PASS",
        db_path=db
    )
    assert isinstance(rid, int) and rid > 0

def test_batch_persists_after_retrieval(db):
    """An added batch is returned by the query function."""
    suppliers = database.get_all_suppliers(db_path=db)
    s = suppliers[0]
    database.add_production_batch(
        "BCH-PERSIST", "2025-07-02", "Line 2",
        s["Supplier_ID"], s["Supplier_Name"],
        "Turmeric Powder", 300.0, "kg", 9.0, 72.0, 1300.0, 40.0, "Grade B", 270.0, "FAIL",
        db_path=db
    )
    batches = database.get_production_batches(db_path=db)
    assert any(b["Batch_ID"] == "BCH-PERSIST" for b in batches)

def test_batch_search_by_batch_id(db):
    """Search returns matching batches by batch ID."""
    suppliers = database.get_all_suppliers(db_path=db)
    s = suppliers[0]
    database.add_production_batch(
        "SEARCH-BCH-001", "2025-07-03", "Line 3",
        s["Supplier_ID"], s["Supplier_Name"],
        "Coriander Powder", 200.0, "kg", 10.0, 70.0, 1250.0, 45.0, "Grade C", 180.0, "PASS",
        db_path=db
    )
    results = database.get_production_batches(query="SEARCH-BCH", db_path=db)
    assert len(results) >= 1
    assert any("SEARCH-BCH" in b["Batch_ID"] for b in results)

def test_edit_production_batch(db):
    """Editing a batch changes its quality result."""
    suppliers = database.get_all_suppliers(db_path=db)
    s = suppliers[0]
    rid = database.add_production_batch(
        "BCH-EDIT", "2025-08-01", "Line 1",
        s["Supplier_ID"], s["Supplier_Name"],
        "Garam Masala", 400.0, "kg", 7.5, 78.0, 1180.0, 32.0, "Grade A", 360.0, "PASS",
        db_path=db
    )
    success = database.update_production_batch(
        record_id=rid,
        batch_id="BCH-EDIT",
        prod_date="2025-08-01",
        prod_line="Line 1",
        supplier_id=s["Supplier_ID"],
        supplier_name=s["Supplier_Name"],
        spice_type="Garam Masala",
        raw_weight=400.0,
        weight_unit="kg",
        moisture=11.5,  # Changed moisture
        temperature=88.0,  # Changed temperature
        speed=1180.0,
        prod_time=32.0,
        raw_quality="Grade B",
        final_weight=355.0,
        quality_result="FAIL",  # Changed result
        db_path=db
    )
    assert success is True
    batches = database.get_production_batches(query="BCH-EDIT", db_path=db)
    edited = next((b for b in batches if b["Record_ID"] == rid), None)
    assert edited is not None
    assert edited["Actual_Quality_Result"] == "FAIL"
    assert edited["Moisture_Level"] == pytest.approx(11.5)

def test_delete_production_batch(db):
    """A batch can be deleted and no longer appears in queries."""
    suppliers = database.get_all_suppliers(db_path=db)
    s = suppliers[0]
    rid = database.add_production_batch(
        "BCH-DEL", "2025-09-01", "Line 2",
        s["Supplier_ID"], s["Supplier_Name"],
        "Chilli Powder", 100.0, "kg", 9.0, 74.0, 1250.0, 28.0, "Grade A", 90.0, "PASS",
        db_path=db
    )
    success = database.delete_production_batch(rid, db_path=db)
    assert success is True
    batches = database.get_production_batches(db_path=db)
    assert all(b["Record_ID"] != rid for b in batches)

def test_reused_batch_number_allowed(db):
    """The same Batch_ID string can appear multiple times; unique identity is Record_ID."""
    suppliers = database.get_all_suppliers(db_path=db)
    s = suppliers[0]
    rid1 = database.add_production_batch(
        "BATCH-REUSE", "2024-01-01", "Line 1",
        s["Supplier_ID"], s["Supplier_Name"],
        "Chilli Powder", 500.0, "kg", 8.0, 75.0, 1200.0, 30.0, "Grade A", 450.0, "PASS",
        db_path=db
    )
    rid2 = database.add_production_batch(
        "BATCH-REUSE", "2025-01-01", "Line 1",
        s["Supplier_ID"], s["Supplier_Name"],
        "Chilli Powder", 500.0, "kg", 8.0, 75.0, 1200.0, 30.0, "Grade A", 450.0, "FAIL",
        db_path=db
    )
    assert rid1 != rid2, "Reused batch numbers must result in different Record_IDs"
    batches = database.get_production_batches(query="BATCH-REUSE", db_path=db)
    assert len(batches) == 2

def test_filter_by_quality_status(db):
    """Filtering by PASS returns only PASS records."""
    suppliers = database.get_all_suppliers(db_path=db)
    s = suppliers[0]
    database.add_production_batch("FLT-001", "2025-05-01", "Line 1", s["Supplier_ID"], s["Supplier_Name"], "Chilli Powder", 500.0, "kg", 8.0, 75.0, 1200.0, 30.0, "Grade A", 450.0, "PASS", db_path=db)
    database.add_production_batch("FLT-002", "2025-05-01", "Line 2", s["Supplier_ID"], s["Supplier_Name"], "Turmeric Powder", 500.0, "kg", 10.0, 80.0, 1100.0, 40.0, "Grade C", 400.0, "FAIL", db_path=db)
    pass_batches = database.get_production_batches(quality_status="PASS", db_path=db)
    assert all(b["Actual_Quality_Result"] == "PASS" for b in pass_batches)

def test_weight_unit_standardization_grams(db):
    """Input in grams is correctly converted and stored as kilograms."""
    suppliers = database.get_all_suppliers(db_path=db)
    s = suppliers[0]
    rid = database.add_production_batch(
        "GRAM-BATCH", "2025-06-01", "Line 1",
        s["Supplier_ID"], s["Supplier_Name"],
        "Coriander Powder", 500000.0, "grams", 8.0, 75.0, 1200.0, 30.0, "Grade A", 450.0, "PASS",
        db_path=db
    )
    batches = database.get_production_batches(query="GRAM-BATCH", db_path=db)
    record = next((b for b in batches if b["Record_ID"] == rid), None)
    assert record is not None
    assert record["Standardized_Weight_Kg"] == pytest.approx(500.0)

def test_audit_log_created_on_insert(db):
    """Adding a batch generates an audit log entry."""
    suppliers = database.get_all_suppliers(db_path=db)
    s = suppliers[0]
    database.add_production_batch(
        "AUDIT-BCH", "2025-01-01", "Line 1",
        s["Supplier_ID"], s["Supplier_Name"],
        "Garam Masala", 300.0, "kg", 7.0, 76.0, 1300.0, 25.0, "Grade A", 270.0, "PASS",
        db_path=db
    )
    logs = database.get_audit_logs(limit=10, db_path=db)
    assert any("AUDIT-BCH" in log.get("Details", "") for log in logs)

def test_audit_log_created_on_delete(db):
    """Deleting a batch creates an audit log entry."""
    suppliers = database.get_all_suppliers(db_path=db)
    s = suppliers[0]
    rid = database.add_production_batch(
        "DEL-AUDIT-BCH", "2025-01-15", "Line 2",
        s["Supplier_ID"], s["Supplier_Name"],
        "Chilli Powder", 200.0, "kg", 8.5, 73.0, 1200.0, 30.0, "Grade B", 180.0, "FAIL",
        db_path=db
    )
    database.delete_production_batch(rid, db_path=db)
    logs = database.get_audit_logs(limit=10, db_path=db)
    assert any("DELETE" == log.get("Action_Type") and log.get("Table_Name") == "Production_Batches" for log in logs)


# ============================================================
# RAW MATERIAL TESTS
# ============================================================

def test_add_raw_material(db):
    """Raw material insertion returns a positive Material_ID."""
    suppliers = database.get_all_suppliers(db_path=db)
    s = suppliers[0]
    mid = database.add_raw_material(
        "Red Chilli", s["Supplier_ID"], s["Supplier_Name"],
        1000.0, "kg", "2025-06-01", 9.0, "Grade A", "PASS",
        db_path=db
    )
    assert isinstance(mid, int) and mid > 0

def test_raw_material_gram_conversion(db):
    """500,000 grams is stored as 500 kg in Standardized_Quantity_Kg."""
    suppliers = database.get_all_suppliers(db_path=db)
    s = suppliers[0]
    database.add_raw_material(
        "Ground Turmeric", s["Supplier_ID"], s["Supplier_Name"],
        500000.0, "grams", "2025-07-01", 10.5, "Grade B", "PASS",
        db_path=db
    )
    materials = database.get_all_raw_materials(db_path=db)
    mat = next((m for m in materials if m["Material_Name"] == "Ground Turmeric"), None)
    assert mat is not None
    assert mat["Standardized_Quantity_Kg"] == pytest.approx(500.0)

def test_raw_material_persists(db):
    """Raw material records survive database connection closure."""
    suppliers = database.get_all_suppliers(db_path=db)
    s = suppliers[0]
    database.add_raw_material(
        "Coriander Seeds", s["Supplier_ID"], s["Supplier_Name"],
        750.0, "kg", "2025-08-15", 8.0, "Grade A", "PASS",
        db_path=db
    )
    materials = database.get_all_raw_materials(db_path=db)
    assert any(m["Material_Name"] == "Coriander Seeds" for m in materials)
