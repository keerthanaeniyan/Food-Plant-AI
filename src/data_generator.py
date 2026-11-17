"""
Synthetic Dataset Generator for FOOD PLANT AI
Generates ~300,000 spice manufacturing production records for Hyderabad factory.
SYNTHETIC DEMONSTRATION DATA - Not actual company records
"""

import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

# ── Constants ────────────────────────────────────────────────────────────────

PRODUCTION_LINES = ["Line 1", "Line 2", "Line 3"]

SPICE_TYPES = ["Chilli Powder", "Turmeric Powder", "Coriander Powder", "Garam Masala"]

SUPPLIERS = {
    "Hyderabad Spice Traders": [
        "Hyderabad Spice Traders", "HYD Spice Traders",
        "Hyderabad Spice Trader", "hyd spice traders"
    ],
    "Telangana Agro Mills": [
        "Telangana Agro Mills", "Telangana Agro Mill", "Tel Agro Mills"
    ],
    "Guntur Spices Co": [
        "Guntur Spices Co", "Guntur Spices Company", "Guntur Spice Co."
    ],
    "Deccan Spice Organics": [
        "Deccan Spice Organics", "Deccan Spices Organics", "Deccan Organic Spices"
    ],
    "Nizamabad Turmeric Hub": [
        "Nizamabad Turmeric Hub", "Nizamabad Turmeric", "Nizam Turmeric Hub"
    ],
    "Malabar Garam Masala Guild": [
        "Malabar Garam Masala Guild", "Malabar Masala Guild", "Malabar GM Guild"
    ],
}

# Flat list of all supplier name variants with their weights
ALL_SUPPLIER_VARIANTS = []
SUPPLIER_VARIANT_WEIGHTS = []
for canonical, variants in SUPPLIERS.items():
    for v in variants:
        ALL_SUPPLIER_VARIANTS.append(v)
        # Give equal weight within group; groups get roughly equal share
        SUPPLIER_VARIANT_WEIGHTS.append(1.0 / len(variants))

# Normalize weights
_total = sum(SUPPLIER_VARIANT_WEIGHTS)
SUPPLIER_VARIANT_WEIGHTS = [w / _total for w in SUPPLIER_VARIANT_WEIGHTS]

GRADE_CHOICES = ["Grade A", "Grade B", "Grade C", "Grade D"]
GRADE_WEIGHTS = [0.40, 0.35, 0.20, 0.05]

TOTAL_RECORDS = 300_000
CHUNK_SIZE = 10_000
NUM_UNIQUE_BATCHES = 2000

START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2024, 12, 31)
DATE_RANGE_DAYS = (END_DATE - START_DATE).days


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def compute_fail_probability(moisture, temperature, speed, prod_time, grade):
    """
    Compute FAIL probability using logistic combination of risk factors.
    Target ~25-30% overall FAIL rate.
    """
    logit = -1.5  # base intercept (keeps overall ~25% FAIL without other risks)

    # Moisture risk (strong)
    logit += np.where(moisture > 12, 1.8, 0.0)

    # Temperature risk (moderate)
    logit += np.where((temperature > 85) | (temperature < 65), 1.0, 0.0)

    # Speed risk (moderate)
    logit += np.where((speed < 1100) | (speed > 1450), 0.9, 0.0)

    # Production time risk (moderate)
    logit += np.where(prod_time > 55, 0.8, 0.0)

    # Grade risk (strong)
    grade_risk = np.select(
        [grade == "Grade C", grade == "Grade D"],
        [1.4, 2.2],
        default=0.0
    )
    logit += grade_risk

    return _sigmoid(logit)


def generate_chunk(start_idx, chunk_size, batch_pool, rng):
    """Generate a single chunk of records."""
    n = chunk_size

    # Record IDs
    record_ids = np.arange(start_idx + 1, start_idx + n + 1)

    # Batch IDs — randomly pick from pool (intentional reuse)
    batch_indices = rng.integers(0, len(batch_pool), size=n)
    batch_ids = batch_pool[batch_indices]

    # Production dates
    day_offsets = rng.integers(0, DATE_RANGE_DAYS + 1, size=n)
    dates = [START_DATE + timedelta(days=int(d)) for d in day_offsets]
    prod_dates = [d.strftime("%Y-%m-%d") for d in dates]

    # Production lines
    lines = rng.choice(PRODUCTION_LINES, size=n)

    # Supplier names (with intentional inconsistency)
    suppliers = rng.choice(
        ALL_SUPPLIER_VARIANTS,
        size=n,
        p=SUPPLIER_VARIANT_WEIGHTS
    )

    # Spice types
    spices = rng.choice(SPICE_TYPES, size=n)

    # Weight unit: 70% kg, 30% grams
    weight_unit_mask = rng.random(n) < 0.70  # True → kg
    weight_units = np.where(weight_unit_mask, "kg", "grams")

    # Raw material weight
    kg_weights = rng.uniform(200, 2000, size=n)
    gram_weights = rng.uniform(200_000, 2_000_000, size=n)
    raw_weights = np.where(weight_unit_mask, kg_weights, gram_weights)
    raw_weights = np.round(raw_weights, 2)

    # Moisture level (normally dist, clipped)
    moisture = rng.normal(8.5, 2.5, size=n)
    moisture = np.clip(moisture, 1, 20)
    moisture = np.round(moisture, 3)

    # Machine temperature
    temperature = rng.normal(75, 8, size=n)
    temperature = np.clip(temperature, 50, 110)
    temperature = np.round(temperature, 2)

    # Machine speed
    speed = rng.normal(1250, 150, size=n)
    speed = np.clip(speed, 900, 1600)
    speed = np.round(speed, 1)

    # Production time
    prod_time = rng.normal(35, 10, size=n)
    prod_time = np.clip(prod_time, 10, 90)
    prod_time = np.round(prod_time, 2)

    # Raw material quality
    grades = rng.choice(GRADE_CHOICES, size=n, p=GRADE_WEIGHTS)

    # Final product weight: conversion factor 0.80–0.95 + small noise
    base_conversion = rng.uniform(0.80, 0.95, size=n)
    noise = rng.normal(0, 0.01, size=n)
    conversion = np.clip(base_conversion + noise, 0.78, 0.97)
    # For grams, we keep the same conversion; Final_Product_Weight always in same unit as input
    final_weights = np.round(raw_weights * conversion, 2)

    # Quality result — realistic rules
    fail_prob = compute_fail_probability(moisture, temperature, speed, prod_time, grades)
    rand_draw = rng.random(n)
    quality = np.where(rand_draw < fail_prob, "FAIL", "PASS")

    df = pd.DataFrame({
        "Record_ID": record_ids,
        "Batch_ID": batch_ids,
        "Production_Date": prod_dates,
        "Production_Line": lines,
        "Supplier_Name": suppliers,
        "Spice_Type": spices,
        "Raw_Material_Weight": raw_weights,
        "Weight_Unit": weight_units,
        "Moisture_Level": moisture,
        "Machine_Temperature": temperature,
        "Machine_Speed": speed,
        "Production_Time": prod_time,
        "Raw_Material_Quality": grades,
        "Final_Product_Weight": final_weights,
        "Quality_Result": quality,
    })
    return df


def introduce_missing_values(df, rng):
    """Introduce deliberate missing values."""
    n = len(df)
    # 5% missing in Moisture_Level
    moisture_missing = rng.random(n) < 0.05
    df.loc[moisture_missing, "Moisture_Level"] = np.nan

    # 3% missing in Machine_Temperature
    temp_missing = rng.random(n) < 0.03
    df.loc[temp_missing, "Machine_Temperature"] = np.nan

    return df


def introduce_duplicates(df, rng, dup_fraction=0.02):
    """Add ~2% duplicate rows."""
    n_dups = int(len(df) * dup_fraction)
    dup_indices = rng.integers(0, len(df), size=n_dups)
    dups = df.iloc[dup_indices].copy()
    return pd.concat([df, dups], ignore_index=True)


def create_data_dictionary():
    """Create a data dictionary CSV."""
    dd = pd.DataFrame([
        {"Column": "Record_ID", "Type": "Integer", "Description": "Unique sequential record identifier"},
        {"Column": "Batch_ID", "Type": "String", "Description": "Production batch identifier (BCH-XXXX); ~2000 unique values, intentionally reused across records"},
        {"Column": "Production_Date", "Type": "Date (YYYY-MM-DD)", "Description": "Date of production, ranging 2022-01-01 to 2024-12-31"},
        {"Column": "Production_Line", "Type": "Categorical", "Description": "Manufacturing line: Line 1, Line 2, or Line 3"},
        {"Column": "Supplier_Name", "Type": "String", "Description": "Raw material supplier name; intentionally inconsistent casing/spelling for cleaning challenge"},
        {"Column": "Spice_Type", "Type": "Categorical", "Description": "Product type: Chilli Powder, Turmeric Powder, Coriander Powder, or Garam Masala"},
        {"Column": "Raw_Material_Weight", "Type": "Float", "Description": "Weight of raw material input; 200-2000 for kg, 200000-2000000 for grams"},
        {"Column": "Weight_Unit", "Type": "Categorical", "Description": "Unit of weight: 'kg' (70%) or 'grams' (30%)"},
        {"Column": "Moisture_Level", "Type": "Float", "Description": "Moisture content percentage [1-20]; ~5% values missing (NaN)"},
        {"Column": "Machine_Temperature", "Type": "Float", "Description": "Processing machine temperature in °C [50-110]; ~3% values missing (NaN)"},
        {"Column": "Machine_Speed", "Type": "Float", "Description": "Machine rotation speed in RPM [900-1600]"},
        {"Column": "Production_Time", "Type": "Float", "Description": "Total production batch time in minutes [10-90]"},
        {"Column": "Raw_Material_Quality", "Type": "Categorical", "Description": "Quality grade of incoming raw material: Grade A (40%), B (35%), C (20%), D (5%)"},
        {"Column": "Final_Product_Weight", "Type": "Float", "Description": "Weight of finished product after processing; same unit as Raw_Material_Weight; conversion factor 0.80-0.95"},
        {"Column": "Quality_Result", "Type": "Categorical", "Description": "Final QC result: PASS or FAIL. Determined by logistic model of risk factors (moisture, temperature, speed, time, grade). Target ~25-30% FAIL rate"},
    ])
    return dd


def create_sample_data(df, n=1000):
    """Create a clean 1000-record sample (no missing values, no duplicates)."""
    clean = df.dropna(subset=["Moisture_Level", "Machine_Temperature"]).drop_duplicates()
    sample = clean.sample(n=min(n, len(clean)), random_state=42).reset_index(drop=True)
    return sample


def main():
    os.makedirs("data", exist_ok=True)

    rng = np.random.default_rng(42)

    # Pre-generate batch pool
    batch_numbers = rng.integers(1, 10000, size=NUM_UNIQUE_BATCHES)
    batch_pool = np.array([f"BCH-{n:04d}" for n in batch_numbers])

    output_path = "data/raw_production_data.csv"
    all_chunks = []

    print("=" * 60)
    print("FOOD PLANT AI — Synthetic Data Generator")
    print("=" * 60)
    print(f"Target records: {TOTAL_RECORDS:,}")
    print(f"Chunk size    : {CHUNK_SIZE:,}")
    print("-" * 60)

    num_chunks = TOTAL_RECORDS // CHUNK_SIZE
    generated = 0

    for i in range(num_chunks):
        start_idx = i * CHUNK_SIZE
        chunk = generate_chunk(start_idx, CHUNK_SIZE, batch_pool, rng)
        all_chunks.append(chunk)
        generated += CHUNK_SIZE

        if generated % 50_000 == 0:
            print(f"  Progress: {generated:>7,} / {TOTAL_RECORDS:,} records generated ...")

    # Handle remainder
    remainder = TOTAL_RECORDS - generated
    if remainder > 0:
        chunk = generate_chunk(generated, remainder, batch_pool, rng)
        all_chunks.append(chunk)
        generated += remainder

    print(f"  Progress: {generated:>7,} / {TOTAL_RECORDS:,} records generated ...")
    print("-" * 60)
    print("Concatenating chunks ...")
    df = pd.concat(all_chunks, ignore_index=True)

    print("Introducing missing values ...")
    df = introduce_missing_values(df, rng)

    print("Introducing duplicate rows ...")
    df = introduce_duplicates(df, rng, dup_fraction=0.02)

    # Re-assign Record_IDs after duplicates (keep originals; duplicates share same ID as source)
    # (This is intentional — duplicate detection will catch them)

    print(f"Total rows after duplicates: {len(df):,}")

    # ── Save raw CSV ──────────────────────────────────────────────────────────
    print("Saving raw_production_data.csv ...")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        f.write("# SYNTHETIC DEMONSTRATION DATA - Not actual company records\n")
    df.to_csv(output_path, mode="a", index=False, encoding="utf-8")
    print(f"  Saved → {output_path}")

    # ── Data dictionary ───────────────────────────────────────────────────────
    dd = create_data_dictionary()
    dd_path = "data/data_dictionary.csv"
    dd.to_csv(dd_path, index=False, encoding="utf-8")
    print(f"  Saved → {dd_path}")

    # ── Sample data ───────────────────────────────────────────────────────────
    sample = create_sample_data(df, n=1000)
    sample_path = "data/sample_data.csv"
    sample.to_csv(sample_path, index=False, encoding="utf-8")
    print(f"  Saved → {sample_path}")

    # ── Final statistics ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE — STATISTICS")
    print("=" * 60)
    total_records = len(df)
    pass_count = (df["Quality_Result"] == "PASS").sum()
    fail_count = (df["Quality_Result"] == "FAIL").sum()
    fail_rate = fail_count / total_records * 100

    print(f"Total records       : {total_records:>10,}")
    print(f"PASS count          : {pass_count:>10,}  ({100 - fail_rate:.1f}%)")
    print(f"FAIL count          : {fail_count:>10,}  ({fail_rate:.1f}%)")
    print()
    print("Missing value counts:")
    for col in ["Moisture_Level", "Machine_Temperature"]:
        missing = df[col].isna().sum()
        pct = missing / total_records * 100
        print(f"  {col:<25}: {missing:>8,}  ({pct:.1f}%)")
    print()
    dup_count = df.duplicated().sum()
    print(f"Duplicate rows      : {dup_count:>10,}")
    print(f"Unique Batch IDs    : {df['Batch_ID'].nunique():>10,}")
    print("=" * 60)


if __name__ == "__main__":
    main()
