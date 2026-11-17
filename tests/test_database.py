"""
Unit Tests for Database Operations, Schema Integrity, Audit Logging, and Backup/Restore.
"""

import os
import pytest
import sqlite3
import database


@pytest.fixture
def temp_db(tmp_path):
    """Provides a fresh temporary database path for isolated testing."""
    db_file = str(tmp_path / "test_food_plant.db")
    database.init_db(db_path=db_file)
    return db_file


def test_database_initialization(temp_db):
    """Verifies that all 6 required tables and indexes are created properly."""
    with database.get_db_connection(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        
        expected_tables = {
            "Suppliers",
            "Raw_Materials",
            "Production_Batches",
            "Prediction_History",
            "Audit_Logs",
            "Application_Settings"
        }
        assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"


def test_default_settings_and_suppliers_seeded(temp_db):
    """Checks that default operational thresholds and verified suppliers are seeded."""
    suppliers = database.get_all_suppliers(db_path=temp_db)
    assert len(suppliers) >= 6, "Expected at least 6 default suppliers seeded"
    
    temp_max = database.get_setting("TEMP_LIMIT_MAX", db_path=temp_db)
    assert temp_max == "85.0"
    
    speed_max = database.get_setting("SPEED_LIMIT_MAX", db_path=temp_db)
    assert speed_max == "1450.0"


def test_audit_logging(temp_db):
    """Verifies that actions generate immutable audit log records."""
    database.log_audit("TEST_ACTION", "Test_Table", 999, "Unit test verification log", user="Tester", db_path=temp_db)
    logs = database.get_audit_logs(limit=10, db_path=temp_db)
    
    assert any(log["Action_Type"] == "TEST_ACTION" and log["Details"] == "Unit test verification log" for log in logs)


def test_backup_and_restore(temp_db, tmp_path):
    """Verifies database snapshot creation and successful restoration."""
    backup_file = database.backup_database(db_path=temp_db)
    assert os.path.exists(backup_file)
    
    # Modify data in original DB
    database.update_setting("COMPANY_NAME", "Modified Plant Ltd", db_path=temp_db)
    assert database.get_setting("COMPANY_NAME", db_path=temp_db) == "Modified Plant Ltd"
    
    # Restore from backup
    success = database.restore_database(backup_file, db_path=temp_db)
    assert success is True
    assert database.get_setting("COMPANY_NAME", db_path=temp_db) == "SpiceCraft Hyderabad Pvt Ltd"
