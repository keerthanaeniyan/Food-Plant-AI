"""
FOOD PLANT AI - Data Preprocessing Module
Cleans raw production data: standardises suppliers, converts units,
handles missing values, removes duplicates, engineers features,
and exports a cleaned dataset ready for ML training.
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Tuple

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# ── Supplier name standardisation map ─────────────────────────────────────────
SUPPLIER_MAP = {
    # Hyderabad Spice Traders
    "hyd spice traders":          "Hyderabad Spice Traders",
    "hyderabad spice trader":     "Hyderabad Spice Traders",
    "hyderabad spice traders":    "Hyderabad Spice Traders",
    # Telangana Agro Mills
    "tel agro mills":             "Telangana Agro Mills",
    "telangana agro mill":        "Telangana Agro Mills",
    "telangana agro mills":       "Telangana Agro Mills",
    # Guntur Spices Co
    "guntur spice co.":           "Guntur Spices Co",
    "guntur spices company":      "Guntur Spices Co",
    "guntur spices co":           "Guntur Spices Co",
    # Deccan Spice Organics
    "deccan organic spices":      "Deccan Spice Organics",
    "deccan spices organics":     "Deccan Spice Organics",
    "deccan spice organics":      "Deccan Spice Organics",
    # Nizamabad Turmeric Hub
    "nizam turmeric hub":         "Nizamabad Turmeric Hub",
    "nizamabad turmeric":         "Nizamabad Turmeric Hub",
    "nizamabad turmeric hub":     "Nizamabad Turmeric Hub",
    # Malabar Garam Masala Guild
    "malabar gm guild":           "Malabar Garam Masala Guild",
    "malabar masala guild":       "Malabar Garam Masala Guild",
    "malabar garam masala guild": "Malabar Garam Masala Guild",
}

GRADE_NUMERIC = {"Grade A": 4, "Grade B": 3, "Grade C": 2, "Grade D": 1}


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Load raw data  (skip the comment line at top of file)
# ─────────────────────────────────────────────────────────────────────────────

def load_raw_data(path: str) -> pd.DataFrame:
    """Load raw CSV, skipping the synthetic-data comment line if present."""
    # Try skipping first comment line
    try:
        df = pd.read_csv(path, comment="#", low_memory=False)
        return df
    except Exception:
        return pd.read_csv(path, low_memory=False)


# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Standardise supplier names
# ─────────────────────────────────────────────────────────────────────────────

def standardize_supplier_names(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Map all supplier name variants to canonical names."""
    df = df.copy()
    before_unique = df["Supplier_Name"].nunique()
    df["Supplier_Name"] = (
        df["Supplier_Name"]
        .str.strip()
        .str.lower()
        .map(SUPPLIER_MAP)
        .fillna(df["Supplier_Name"].str.strip())     # fall back to stripped original
    )
    after_unique = df["Supplier_Name"].nunique()
    return df, {"before_unique": before_unique, "after_unique": after_unique}


# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Convert weights to kg
# ─────────────────────────────────────────────────────────────────────────────

def convert_weights_to_kg(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Convert all gram records to kg. Final_Product_Weight is always in kg after this step."""
    df = df.copy()
    gram_mask = df["Weight_Unit"].str.lower() == "grams"
    n_converted = gram_mask.sum()
    df.loc[gram_mask, "Raw_Material_Weight"] = df.loc[gram_mask, "Raw_Material_Weight"] / 1000.0
    df.loc[gram_mask, "Weight_Unit"] = "kg"
    # Final product weight is already in same unit — convert for grams rows
    # (Generator stores final weight in same unit as input)
    df.loc[gram_mask, "Final_Product_Weight"] = df.loc[gram_mask, "Final_Product_Weight"] / 1000.0
    df.rename(columns={
        "Raw_Material_Weight": "Raw_Material_Weight_Kg",
        "Final_Product_Weight": "Final_Product_Weight_Kg",
    }, inplace=True)
    return df, int(n_converted)


# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Handle missing values
# ─────────────────────────────────────────────────────────────────────────────

def handle_missing_values(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Impute missing Moisture_Level and Machine_Temperature using line-level median."""
    df = df.copy()
    before_missing = {
        "Moisture_Level": df["Moisture_Level"].isna().sum(),
        "Machine_Temperature": df["Machine_Temperature"].isna().sum(),
    }
    for col in ["Moisture_Level", "Machine_Temperature"]:
        line_medians = df.groupby("Production_Line")[col].transform("median")
        global_median = df[col].median()
        df[col] = df[col].fillna(line_medians).fillna(global_median)

    after_missing = {
        "Moisture_Level": df["Moisture_Level"].isna().sum(),
        "Machine_Temperature": df["Machine_Temperature"].isna().sum(),
    }
    return df, {"before": before_missing, "after": after_missing}


# ─────────────────────────────────────────────────────────────────────────────
# Step 5: Detect and remove duplicates
# ─────────────────────────────────────────────────────────────────────────────

def detect_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Remove exact duplicate rows. Reused Batch_IDs on different dates are NOT duplicates."""
    before = len(df)
    df = df.drop_duplicates()
    after  = len(df)
    return df, before - after


# ─────────────────────────────────────────────────────────────────────────────
# Step 6: Feature engineering
# ─────────────────────────────────────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features used by the ML model."""
    df = df.copy()
    df["Grade_Numeric"]   = df["Raw_Material_Quality"].map(GRADE_NUMERIC).fillna(1).astype(int)
    df["Efficiency_Ratio"]= (df["Final_Product_Weight_Kg"] / df["Raw_Material_Weight_Kg"].replace(0, np.nan)).fillna(0).round(4)
    df["Temp_in_Range"]   = df["Machine_Temperature"].between(65, 85).astype(int)
    df["Speed_in_Range"]  = df["Machine_Speed"].between(1100, 1450).astype(int)
    df["Moisture_Risk"]   = (df["Moisture_Level"] > 12).astype(int)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Full pipeline
# ─────────────────────────────────────────────────────────────────────────────

def preprocess_full(
    input_path: str,
    output_path: str,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Runs all preprocessing steps and saves the cleaned dataset.

    Parameters
    ----------
    input_path : str   Path to raw_production_data.csv
    output_path: str   Where to save cleaned_production_data.csv
    verbose    : bool  Print step-by-step summary

    Returns
    -------
    Cleaned DataFrame
    """
    if verbose:
        print("=" * 65)
        print("FOOD PLANT AI — Data Preprocessing Pipeline")
        print("=" * 65)

    # Step 0: Load
    df = load_raw_data(input_path)
    if verbose:
        print(f"\nStep 0 — Loaded   : {len(df):>10,} rows × {df.shape[1]} columns")

    # Step 1: Supplier standardisation
    df, sup_stats = standardize_supplier_names(df)
    if verbose:
        print(f"Step 1 — Supplier : {sup_stats['before_unique']} → {sup_stats['after_unique']} unique names")

    # Step 2: Weight conversion
    df, n_gram = convert_weights_to_kg(df)
    if verbose:
        print(f"Step 2 — Weights  : {n_gram:,} gram rows converted to kg")

    # Step 3: Missing value imputation
    df, miss_stats = handle_missing_values(df)
    if verbose:
        for col, before in miss_stats["before"].items():
            print(f"Step 3 — Missing  : {col} — {before:,} → {miss_stats['after'][col]:,} missing")

    # Step 4: Duplicate removal
    df, n_dupes = detect_duplicates(df)
    if verbose:
        print(f"Step 4 — Dupes    : {n_dupes:,} exact duplicate rows removed")

    # Step 5: Feature engineering
    df = engineer_features(df)
    if verbose:
        print(f"Step 5 — Features : Added Grade_Numeric, Efficiency_Ratio, Temp_in_Range, Speed_in_Range, Moisture_Risk")

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    if verbose:
        pass_pct = (df["Quality_Result"] == "PASS").mean() * 100
        fail_pct = 100 - pass_pct
        print(f"\n✅ Cleaned dataset : {len(df):,} rows saved → {output_path}")
        print(f"   PASS: {pass_pct:.1f}%   FAIL: {fail_pct:.1f}%")
        print("=" * 65)

    return df


if __name__ == "__main__":
    raw  = os.path.join(DATA_DIR, "raw_production_data.csv")
    out  = os.path.join(DATA_DIR, "cleaned_production_data.csv")
    if not os.path.exists(raw):
        print(f"ERROR: {raw} not found. Run src/data_generator.py first.")
        sys.exit(1)
    preprocess_full(raw, out, verbose=True)
