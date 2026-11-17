"""
FOOD PLANT AI - Database Management System
Handles SQLite database connection, table schemas, transactions,
foreign keys, audit logging, and backup/restore functionality.
"""

import sqlite3
import os
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "food_plant.db")
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "backups")


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Creates and returns a connection to the SQLite database with WAL mode and foreign keys enabled."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Initializes the SQLite database with all 6 required tables, indexes, and default records."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Suppliers Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Suppliers (
                Supplier_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Supplier_Code TEXT UNIQUE NOT NULL,
                Supplier_Name TEXT NOT NULL,
                Contact_Details TEXT,
                Location TEXT,
                Material_Supplied TEXT,
                Registration_Date TEXT NOT NULL,
                Created_At TEXT NOT NULL,
                Updated_At TEXT NOT NULL
            );
        """)

        # 2. Raw_Materials Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Raw_Materials (
                Material_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Material_Code TEXT UNIQUE NOT NULL,
                Material_Name TEXT NOT NULL,
                Supplier_ID INTEGER,
                Supplier_Name TEXT NOT NULL,
                Quantity REAL NOT NULL,
                Unit TEXT NOT NULL,
                Standardized_Quantity_Kg REAL NOT NULL,
                Purchase_Date TEXT NOT NULL,
                Moisture_Level REAL NOT NULL,
                Quality_Grade TEXT NOT NULL,
                Inspection_Result TEXT NOT NULL,
                Created_At TEXT NOT NULL,
                FOREIGN KEY (Supplier_ID) REFERENCES Suppliers (Supplier_ID) ON DELETE RESTRICT
            );
        """)

        # 3. Production_Batches Table
        # Note: Record_ID is the unique primary key, Batch_ID can repeat across years/shifts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Production_Batches (
                Record_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Batch_ID TEXT NOT NULL,
                Production_Date TEXT NOT NULL,
                Production_Line TEXT NOT NULL,
                Supplier_ID INTEGER,
                Supplier_Name TEXT NOT NULL,
                Spice_Type TEXT NOT NULL,
                Raw_Material_Weight REAL NOT NULL,
                Weight_Unit TEXT NOT NULL,
                Standardized_Weight_Kg REAL NOT NULL,
                Moisture_Level REAL NOT NULL,
                Machine_Temperature REAL NOT NULL,
                Machine_Speed REAL NOT NULL,
                Production_Time REAL NOT NULL,
                Raw_Material_Quality TEXT NOT NULL,
                Final_Product_Weight REAL NOT NULL,
                Actual_Quality_Result TEXT NOT NULL,
                Created_At TEXT NOT NULL,
                Updated_At TEXT NOT NULL,
                FOREIGN KEY (Supplier_ID) REFERENCES Suppliers (Supplier_ID) ON DELETE RESTRICT
            );
        """)

        # 4. Prediction_History Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Prediction_History (
                Prediction_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Batch_ID TEXT,
                Prediction_Date TEXT NOT NULL,
                Production_Line TEXT NOT NULL,
                Supplier_Name TEXT NOT NULL,
                Spice_Type TEXT NOT NULL,
                Raw_Material_Weight_Kg REAL NOT NULL,
                Moisture_Level REAL NOT NULL,
                Machine_Temperature REAL NOT NULL,
                Machine_Speed REAL NOT NULL,
                Production_Time REAL NOT NULL,
                Raw_Material_Quality TEXT NOT NULL,
                Predicted_Result TEXT NOT NULL,
                Failure_Probability REAL NOT NULL,
                Pass_Probability REAL NOT NULL,
                Risk_Category TEXT NOT NULL,
                Contributing_Factors TEXT,
                Recommendation TEXT NOT NULL,
                Actual_Result TEXT,
                Created_At TEXT NOT NULL
            );
        """)

        # 5. Audit_Logs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Audit_Logs (
                Log_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Timestamp TEXT NOT NULL,
                Action_Type TEXT NOT NULL,
                Table_Name TEXT NOT NULL,
                Record_ID INTEGER,
                Details TEXT NOT NULL,
                User TEXT NOT NULL
            );
        """)

        # 6. Application_Settings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Application_Settings (
                Setting_Key TEXT PRIMARY KEY,
                Setting_Value TEXT NOT NULL,
                Description TEXT,
                Updated_At TEXT NOT NULL
            );
        """)

        # Performance Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_date ON Production_Batches(Production_Date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_line ON Production_Batches(Production_Line);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_supplier ON Production_Batches(Supplier_Name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_quality ON Production_Batches(Actual_Quality_Result);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_time ON Audit_Logs(Timestamp);")

        conn.commit()

        # Seed default settings and suppliers if empty
        _seed_default_settings(cursor)
        _seed_default_suppliers(cursor)
        conn.commit()


def _seed_default_settings(cursor: sqlite3.Cursor) -> None:
    """Seeds standard operational parameters and configurable limits."""
    defaults = [
        ("TEMP_LIMIT_MIN", "65.0", "Minimum machine operating temperature in °C"),
        ("TEMP_LIMIT_MAX", "85.0", "Maximum machine operating temperature in °C"),
        ("SPEED_LIMIT_MIN", "1100.0", "Minimum milling machine speed in RPM"),
        ("SPEED_LIMIT_MAX", "1450.0", "Maximum milling machine speed in RPM"),
        ("MOISTURE_LIMIT_MAX", "12.0", "Maximum acceptable moisture level percentage"),
        ("PROD_TIME_MAX", "55.0", "Maximum standard batch cycle time in minutes"),
        ("COMPANY_NAME", "SpiceCraft Hyderabad Pvt Ltd", "Manufacturing facility name"),
        ("FACILITY_LOCATION", "Kattedan Industrial Area, Hyderabad", "Factory plant location"),
        ("ACTIVE_LINES", "Line 1,Line 2,Line 3", "Active spice manufacturing production lines")
    ]
    now = datetime.now().isoformat()
    for key, val, desc in defaults:
        cursor.execute("""
            INSERT OR IGNORE INTO Application_Settings (Setting_Key, Setting_Value, Description, Updated_At)
            VALUES (?, ?, ?, ?)
        """, (key, val, desc, now))


def _seed_default_suppliers(cursor: sqlite3.Cursor) -> None:
    """Seeds verified spice suppliers in Hyderabad and Telangana region if table is empty."""
    cursor.execute("SELECT COUNT(*) FROM Suppliers;")
    if cursor.fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d")
        created_at = datetime.now().isoformat()
        suppliers = [
            ("SUP-HYD-001", "Hyderabad Spice Traders", "+91 98490 12345", "Begum Bazaar, Hyderabad", "Dry Red Chilli, Coriander Seeds", now, created_at, created_at),
            ("SUP-NIZ-002", "Telangana Agro Mills", "+91 94401 23456", "Nizamabad Road, Hyderabad", "Raw Turmeric Fingers", now, created_at, created_at),
            ("SUP-GNT-003", "Guntur Spices Co", "+91 97012 34567", "Guntur / Shamshabad Depot", "Teja Chilli, Guntur S4 Chilli", now, created_at, created_at),
            ("SUP-DEC-004", "Deccan Spice Organics", "+91 98855 67890", "Kattedan, Hyderabad", "Coriander, Cumin, Black Pepper", now, created_at, created_at),
            ("SUP-WAR-005", "Nizamabad Turmeric Hub", "+91 99512 89012", "Duggirala / Nizamabad", "Curcumin High Grade Turmeric", now, created_at, created_at),
            ("SUP-MAL-006", "Malabar Garam Masala Guild", "+91 98480 34567", "Secunderabad Wholesale Terminal", "Cloves, Cardamom, Cinnamon, Star Anise", now, created_at, created_at)
        ]
        cursor.executemany("""
            INSERT INTO Suppliers (Supplier_Code, Supplier_Name, Contact_Details, Location, Material_Supplied, Registration_Date, Created_At, Updated_At)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, suppliers)


# ---------------- AUDIT LOGGING ----------------

def log_audit(action_type: str, table_name: str, record_id: Optional[int], details: str, user: str = "Quality Supervisor", db_path: str = DB_PATH) -> None:
    """Appends an event to the immutable Audit_Logs table."""
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Audit_Logs (Timestamp, Action_Type, Table_Name, Record_ID, Details, User)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (datetime.now().isoformat(), action_type, table_name, record_id, details, user))
            conn.commit()
    except Exception as e:
        print(f"Audit log error: {e}")


# ---------------- SUPPLIER CRUD ----------------

def add_supplier(name: str, contact: str, location: str, materials: str, reg_date: str, code: Optional[str] = None, db_path: str = DB_PATH) -> int:
    """Adds a new supplier with a generated code if omitted."""
    now = datetime.now().isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        if not code:
            cursor.execute("SELECT COUNT(*) FROM Suppliers;")
            count = cursor.fetchone()[0] + 1
            code = f"SUP-{count:03d}"
        cursor.execute("""
            INSERT INTO Suppliers (Supplier_Code, Supplier_Name, Contact_Details, Location, Material_Supplied, Registration_Date, Created_At, Updated_At)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (code, name, contact, location, materials, reg_date, now, now))
        supplier_id = cursor.lastrowid
        conn.commit()
    log_audit("INSERT", "Suppliers", supplier_id, f"Added supplier {name} ({code})", db_path=db_path)
    return supplier_id


def update_supplier(supplier_id: int, name: str, contact: str, location: str, materials: str, reg_date: str, db_path: str = DB_PATH) -> bool:
    """Updates an existing supplier's details."""
    now = datetime.now().isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Suppliers
            SET Supplier_Name = ?, Contact_Details = ?, Location = ?, Material_Supplied = ?, Registration_Date = ?, Updated_At = ?
            WHERE Supplier_ID = ?
        """, (name, contact, location, materials, reg_date, now, supplier_id))
        conn.commit()
        success = cursor.rowcount > 0
    if success:
        log_audit("UPDATE", "Suppliers", supplier_id, f"Updated supplier {name}", db_path=db_path)
    return success


def delete_supplier(supplier_id: int, db_path: str = DB_PATH) -> Tuple[bool, str]:
    """Safely deletes a supplier only if no production batches or raw materials reference it."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        # Check production batches
        cursor.execute("SELECT COUNT(*) FROM Production_Batches WHERE Supplier_ID = ?;", (supplier_id,))
        batch_count = cursor.fetchone()[0]
        if batch_count > 0:
            return False, f"Cannot delete supplier: {batch_count} production batches reference this supplier."

        # Check raw materials
        cursor.execute("SELECT COUNT(*) FROM Raw_Materials WHERE Supplier_ID = ?;", (supplier_id,))
        mat_count = cursor.fetchone()[0]
        if mat_count > 0:
            return False, f"Cannot delete supplier: {mat_count} raw material records reference this supplier."

        cursor.execute("SELECT Supplier_Name FROM Suppliers WHERE Supplier_ID = ?;", (supplier_id,))
        row = cursor.fetchone()
        name = row[0] if row else f"ID {supplier_id}"

        cursor.execute("DELETE FROM Suppliers WHERE Supplier_ID = ?;", (supplier_id,))
        conn.commit()
        success = cursor.rowcount > 0

    if success:
        log_audit("DELETE", "Suppliers", supplier_id, f"Deleted supplier {name}", db_path=db_path)
        return True, f"Supplier '{name}' deleted successfully."
    return False, "Supplier record not found."


def get_all_suppliers(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Returns all suppliers as a list of dictionaries."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Suppliers ORDER BY Supplier_Name ASC;")
        rows = [dict(r) for r in cursor.fetchall()]
    return rows


# ---------------- RAW MATERIALS CRUD ----------------

def add_raw_material(name: str, supplier_id: Optional[int], supplier_name: str, quantity: float,
                     unit: str, purchase_date: str, moisture: float, quality_grade: str,
                     inspection: str, code: Optional[str] = None, db_path: str = DB_PATH) -> int:
    """Adds a raw material shipment, standardizing weight to kilograms."""
    std_kg = quantity if unit.lower() == "kg" else quantity / 1000.0
    now = datetime.now().isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        if not code:
            cursor.execute("SELECT COUNT(*) FROM Raw_Materials;")
            code = f"MAT-{(cursor.fetchone()[0] + 1):04d}"
        cursor.execute("""
            INSERT INTO Raw_Materials (Material_Code, Material_Name, Supplier_ID, Supplier_Name,
                                      Quantity, Unit, Standardized_Quantity_Kg, Purchase_Date,
                                      Moisture_Level, Quality_Grade, Inspection_Result, Created_At)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (code, name, supplier_id, supplier_name, quantity, unit, std_kg, purchase_date,
              moisture, quality_grade, inspection, now))
        mat_id = cursor.lastrowid
        conn.commit()
    log_audit("INSERT", "Raw_Materials", mat_id, f"Added raw material {name} ({quantity} {unit}) from {supplier_name}", db_path=db_path)
    return mat_id


def get_all_raw_materials(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Returns all raw materials with supplier information."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Raw_Materials ORDER BY Purchase_Date DESC, Material_ID DESC;")
        return [dict(r) for r in cursor.fetchall()]


# ---------------- PRODUCTION BATCHES CRUD ----------------

def add_production_batch(batch_id: str, prod_date: str, prod_line: str,
                         supplier_id: Optional[int], supplier_name: str, spice_type: str,
                         raw_weight: float, weight_unit: str, moisture: float,
                         temperature: float, speed: float, prod_time: float,
                         raw_quality: str, final_weight: float, quality_result: str,
                         db_path: str = DB_PATH) -> int:
    """Inserts a new manufacturing batch record with standardized kilograms and audit trail."""
    std_kg = raw_weight if weight_unit.lower() == "kg" else raw_weight / 1000.0
    now = datetime.now().isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Production_Batches (
                Batch_ID, Production_Date, Production_Line, Supplier_ID, Supplier_Name,
                Spice_Type, Raw_Material_Weight, Weight_Unit, Standardized_Weight_Kg,
                Moisture_Level, Machine_Temperature, Machine_Speed, Production_Time,
                Raw_Material_Quality, Final_Product_Weight, Actual_Quality_Result,
                Created_At, Updated_At
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (batch_id, prod_date, prod_line, supplier_id, supplier_name,
              spice_type, raw_weight, weight_unit, std_kg,
              moisture, temperature, speed, prod_time,
              raw_quality, final_weight, quality_result,
              now, now))
        record_id = cursor.lastrowid
        conn.commit()
    log_audit("INSERT", "Production_Batches", record_id, f"Batch {batch_id} ({spice_type}, {prod_line}): {quality_result}", db_path=db_path)
    return record_id


def update_production_batch(record_id: int, batch_id: str, prod_date: str, prod_line: str,
                            supplier_id: Optional[int], supplier_name: str, spice_type: str,
                            raw_weight: float, weight_unit: str, moisture: float,
                            temperature: float, speed: float, prod_time: float,
                            raw_quality: str, final_weight: float, quality_result: str,
                            db_path: str = DB_PATH) -> bool:
    """Updates an existing production batch identified by its unique Record_ID."""
    std_kg = raw_weight if weight_unit.lower() == "kg" else raw_weight / 1000.0
    now = datetime.now().isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Production_Batches SET
                Batch_ID = ?, Production_Date = ?, Production_Line = ?, Supplier_ID = ?,
                Supplier_Name = ?, Spice_Type = ?, Raw_Material_Weight = ?, Weight_Unit = ?,
                Standardized_Weight_Kg = ?, Moisture_Level = ?, Machine_Temperature = ?,
                Machine_Speed = ?, Production_Time = ?, Raw_Material_Quality = ?,
                Final_Product_Weight = ?, Actual_Quality_Result = ?, Updated_At = ?
            WHERE Record_ID = ?
        """, (batch_id, prod_date, prod_line, supplier_id,
              supplier_name, spice_type, raw_weight, weight_unit,
              std_kg, moisture, temperature, speed, prod_time,
              raw_quality, final_weight, quality_result, now, record_id))
        conn.commit()
        success = cursor.rowcount > 0
    if success:
        log_audit("UPDATE", "Production_Batches", record_id, f"Updated batch {batch_id} (Record #{record_id})", db_path=db_path)
    return success


def delete_production_batch(record_id: int, db_path: str = DB_PATH) -> bool:
    """Deletes a production batch record by Record_ID with audit preservation."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Batch_ID, Spice_Type FROM Production_Batches WHERE Record_ID = ?;", (record_id,))
        row = cursor.fetchone()
        batch_info = f"Batch {row[0]} ({row[1]})" if row else f"Record #{record_id}"

        cursor.execute("DELETE FROM Production_Batches WHERE Record_ID = ?;", (record_id,))
        conn.commit()
        success = cursor.rowcount > 0
    if success:
        log_audit("DELETE", "Production_Batches", record_id, f"Deleted {batch_info}", db_path=db_path)
    return success


def get_production_batches(query: Optional[str] = None,
                           production_line: Optional[str] = None,
                           spice_type: Optional[str] = None,
                           supplier_name: Optional[str] = None,
                           quality_status: Optional[str] = None,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None,
                           limit: int = 500,
                           db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Flexible query and filter interface for production batches."""
    sql = "SELECT * FROM Production_Batches WHERE 1=1"
    params: List[Any] = []

    if query:
        sql += " AND (Batch_ID LIKE ? OR Supplier_Name LIKE ? OR Spice_Type LIKE ?)"
        wildcard = f"%{query}%"
        params.extend([wildcard, wildcard, wildcard])

    if production_line and production_line != "All":
        sql += " AND Production_Line = ?"
        params.append(production_line)

    if spice_type and spice_type != "All":
        sql += " AND Spice_Type = ?"
        params.append(spice_type)

    if supplier_name and supplier_name != "All":
        sql += " AND Supplier_Name = ?"
        params.append(supplier_name)

    if quality_status and quality_status != "All":
        sql += " AND Actual_Quality_Result = ?"
        params.append(quality_status)

    if start_date:
        sql += " AND Production_Date >= ?"
        params.append(start_date)

    if end_date:
        sql += " AND Production_Date <= ?"
        params.append(end_date)

    sql += " ORDER BY Production_Date DESC, Record_ID DESC LIMIT ?"
    params.append(limit)

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        return [dict(r) for r in cursor.fetchall()]


# ---------------- PREDICTION HISTORY ----------------

def save_prediction(batch_id: str, prod_line: str, supplier_name: str, spice_type: str,
                    weight_kg: float, moisture: float, temp: float, speed: float,
                    prod_time: float, raw_quality: str, pred_result: str,
                    fail_prob: float, pass_prob: float, risk_cat: str,
                    factors: str, recommendation: str, actual_result: Optional[str] = None,
                    db_path: str = DB_PATH) -> int:
    """Persists model inference outcome to the database."""
    now = datetime.now().isoformat()
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Prediction_History (
                Batch_ID, Prediction_Date, Production_Line, Supplier_Name, Spice_Type,
                Raw_Material_Weight_Kg, Moisture_Level, Machine_Temperature, Machine_Speed,
                Production_Time, Raw_Material_Quality, Predicted_Result, Failure_Probability,
                Pass_Probability, Risk_Category, Contributing_Factors, Recommendation,
                Actual_Result, Created_At
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (batch_id, today, prod_line, supplier_name, spice_type,
              weight_kg, moisture, temp, speed,
              prod_time, raw_quality, pred_result, fail_prob,
              pass_prob, risk_cat, factors, recommendation,
              actual_result, now))
        pred_id = cursor.lastrowid
        conn.commit()
    log_audit("PREDICT", "Prediction_History", pred_id, f"Inference for Batch {batch_id}: {pred_result} (Fail Prob: {fail_prob:.1%})", db_path=db_path)
    return pred_id


def update_prediction_actual_result(pred_id: int, actual_result: str, db_path: str = DB_PATH) -> bool:
    """Allows authorized lab managers to record the confirmed laboratory test result."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Prediction_History
            SET Actual_Result = ?
            WHERE Prediction_ID = ?
        """, (actual_result, pred_id))
        conn.commit()
        success = cursor.rowcount > 0
    if success:
        log_audit("UPDATE", "Prediction_History", pred_id, f"Lab result confirmed: {actual_result}", db_path=db_path)
    return success


def get_prediction_history(limit: int = 200, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Returns inference history ordered newest first."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Prediction_History ORDER BY Prediction_ID DESC LIMIT ?;", (limit,))
        return [dict(r) for r in cursor.fetchall()]


# ---------------- SETTINGS & CONFIG ----------------

def get_setting(key: str, default: str = "", db_path: str = DB_PATH) -> str:
    """Retrieves an application configuration value."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Setting_Value FROM Application_Settings WHERE Setting_Key = ?;", (key,))
        row = cursor.fetchone()
        return row[0] if row else default


def update_setting(key: str, value: str, description: Optional[str] = None, db_path: str = DB_PATH) -> None:
    """Updates or inserts an application configuration parameter."""
    now = datetime.now().isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Application_Settings (Setting_Key, Setting_Value, Description, Updated_At)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(Setting_Key) DO UPDATE SET
                Setting_Value = excluded.Setting_Value,
                Description = COALESCE(excluded.Description, Application_Settings.Description),
                Updated_At = excluded.Updated_At;
        """, (key, value, description, now))
        conn.commit()
    log_audit("UPDATE", "Application_Settings", None, f"Setting '{key}' set to '{value}'", db_path=db_path)


def get_all_settings(db_path: str = DB_PATH) -> Dict[str, str]:
    """Returns all application settings as key-value pairs."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Setting_Key, Setting_Value FROM Application_Settings;")
        return {r[0]: r[1] for r in cursor.fetchall()}


# ---------------- AUDIT LOGS RETRIEVAL ----------------

def get_audit_logs(limit: int = 100, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Fetches the latest audit logs."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Audit_Logs ORDER BY Log_ID DESC LIMIT ?;", (limit,))
        return [dict(r) for r in cursor.fetchall()]


# ---------------- BACKUP & RESTORE ----------------

def backup_database(db_path: str = DB_PATH) -> str:
    """Creates a timestamped snapshot using SQLite online backup API (WAL-safe)."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"food_plant_backup_{timestamp}.db")
    # Use SQLite's built-in backup API which handles WAL correctly
    src = sqlite3.connect(db_path)
    dst = sqlite3.connect(backup_file)
    src.backup(dst)
    src.close()
    dst.close()
    log_audit("BACKUP", "System", None, f"Database backup created: {os.path.basename(backup_file)}", db_path=db_path)
    return backup_file


def list_backups() -> List[str]:
    """Lists available database backups."""
    if not os.path.exists(BACKUP_DIR):
        return []
    files = [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.endswith(".db")]
    files.sort(key=os.path.getmtime, reverse=True)
    return files


def restore_database(backup_path: str, db_path: str = DB_PATH) -> bool:
    """Restores the database from a backup file, using SQLite online backup API for safety."""
    if not os.path.exists(backup_path):
        return False
    # Safety snapshot of current database
    try:
        shutil.copy2(db_path, db_path + ".before_restore")
    except Exception:
        pass
    # Use SQLite backup API to safely overwrite the target database without file locks
    try:
        src_conn = sqlite3.connect(backup_path)
        dst_conn = sqlite3.connect(db_path)
        src_conn.backup(dst_conn)
        src_conn.close()
        dst_conn.close()
    except Exception as e:
        print(f"Restore error: {e}")
        return False
    log_audit("RESTORE", "System", None, f"Database restored from {os.path.basename(backup_path)}", db_path=db_path)
    return True
