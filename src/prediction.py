"""
FOOD PLANT AI - Prediction Module
Handles loading of trained machine learning model, pipeline, and single-record inference.
Provides probability estimation, risk categorization, contributing factors, and recommendations.
"""

import os
import time
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

_MODEL = None
_PIPELINE = None
_METADATA = None

GRADE_MAP = {"Grade A": 4, "Grade B": 3, "Grade C": 2, "Grade D": 1}


def load_model(models_dir: str = MODELS_DIR):
    """Loads the trained model, preprocessing pipeline, and metadata into memory (cached)."""
    global _MODEL, _PIPELINE, _METADATA
    if _MODEL is None:
        model_path = os.path.join(models_dir, "quality_model.pkl")
        pipeline_path = os.path.join(models_dir, "preprocessing_pipeline.pkl")
        metadata_path = os.path.join(models_dir, "model_metadata.pkl")

        if not (os.path.exists(model_path) and os.path.exists(pipeline_path)):
            raise FileNotFoundError("Trained model or pipeline not found in models directory. Run src/train_model.py first.")

        _MODEL = joblib.load(model_path)
        _PIPELINE = joblib.load(pipeline_path)
        if os.path.exists(metadata_path):
            _METADATA = joblib.load(metadata_path)
        else:
            _METADATA = {}
    return _MODEL, _PIPELINE, _METADATA


def predict(raw_input: Dict[str, Any], models_dir: str = MODELS_DIR) -> Dict[str, Any]:
    """
    Performs inference for a single batch input.

    Expected raw_input keys:
    - Production_Line (str): e.g. "Line 1"
    - Supplier_Name (str): e.g. "Hyderabad Spice Traders"
    - Spice_Type (str): e.g. "Chilli Powder"
    - Raw_Material_Weight (float): weight value
    - Weight_Unit (str): "kg" or "grams"
    - Moisture_Level (float): %
    - Machine_Temperature (float): °C
    - Machine_Speed (float): RPM
    - Production_Time (float): minutes
    - Raw_Material_Quality (str): "Grade A", "Grade B", "Grade C", "Grade D"
    """
    model, pipeline, metadata = load_model(models_dir)

    # 1. Standardize weight
    raw_weight = float(raw_input.get("Raw_Material_Weight", 500.0))
    weight_unit = str(raw_input.get("Weight_Unit", "kg")).lower()
    weight_kg = raw_weight if weight_unit == "kg" else raw_weight / 1000.0

    moisture = float(raw_input.get("Moisture_Level", 8.5))
    temp = float(raw_input.get("Machine_Temperature", 75.0))
    speed = float(raw_input.get("Machine_Speed", 1250.0))
    prod_time = float(raw_input.get("Production_Time", 35.0))
    quality_grade = str(raw_input.get("Raw_Material_Quality", "Grade A"))
    grade_numeric = GRADE_MAP.get(quality_grade, 3)

    # Derived rule flags
    temp_in_range = int(65.0 <= temp <= 85.0)
    speed_in_range = int(1100.0 <= speed <= 1450.0)
    moisture_risk = int(moisture > 12.0)
    # Default estimated efficiency ratio
    efficiency_ratio = 0.88

    prod_line = str(raw_input.get("Production_Line", "Line 1"))
    spice_type = str(raw_input.get("Spice_Type", "Chilli Powder"))

    # Build feature record matching training feature names
    feature_columns = metadata.get("feature_columns", [
        'Raw_Material_Weight_Kg', 'Moisture_Level', 'Machine_Temperature', 'Machine_Speed',
        'Production_Time', 'Grade_Numeric', 'Efficiency_Ratio', 'Temp_in_Range',
        'Speed_in_Range', 'Moisture_Risk', 'Production_Line_Line 1', 'Production_Line_Line 2',
        'Production_Line_Line 3', 'Spice_Type_Chilli Powder', 'Spice_Type_Coriander Powder',
        'Spice_Type_Garam Masala', 'Spice_Type_Turmeric Powder'
    ])

    data = {
        'Raw_Material_Weight_Kg': weight_kg,
        'Moisture_Level': moisture,
        'Machine_Temperature': temp,
        'Machine_Speed': speed,
        'Production_Time': prod_time,
        'Grade_Numeric': grade_numeric,
        'Efficiency_Ratio': efficiency_ratio,
        'Temp_in_Range': temp_in_range,
        'Speed_in_Range': speed_in_range,
        'Moisture_Risk': moisture_risk,
        'Production_Line_Line 1': int(prod_line == "Line 1"),
        'Production_Line_Line 2': int(prod_line == "Line 2"),
        'Production_Line_Line 3': int(prod_line == "Line 3"),
        'Spice_Type_Chilli Powder': int(spice_type == "Chilli Powder"),
        'Spice_Type_Coriander Powder': int(spice_type == "Coriander Powder"),
        'Spice_Type_Garam Masala': int(spice_type == "Garam Masala"),
        'Spice_Type_Turmeric Powder': int(spice_type == "Turmeric Powder")
    }

    df_single = pd.DataFrame([data])
    # Ensure all feature_columns exist
    for col in feature_columns:
        if col not in df_single.columns:
            df_single[col] = 0
    df_single = df_single[feature_columns]

    # Preprocess and infer
    t0 = time.perf_counter()
    X_tr = pd.DataFrame(pipeline.transform(df_single))
    probabilities = model.predict_proba(X_tr)[0]
    t1 = time.perf_counter()
    inference_time_ms = round((t1 - t0) * 1000, 3)

    # Class 0: FAIL, Class 1: PASS
    fail_prob = float(probabilities[0])
    pass_prob = float(probabilities[1])

    predicted_result = "PASS" if pass_prob >= 0.5 else "FAIL"

    # Risk categorization based on failure probability
    if fail_prob < 0.30:
        risk_category = "LOW"
    elif fail_prob <= 0.60:
        risk_category = "MEDIUM"
    else:
        risk_category = "HIGH"

    # Contributing factors analysis
    factors = []
    if moisture > 12.0:
        factors.append(f"Elevated raw material moisture ({moisture:.1f}% > 12.0% safe threshold)")
    if temp > 85.0:
        factors.append(f"Excessive milling temperature ({temp:.1f}°C > 85.0°C limit)")
    elif temp < 65.0:
        factors.append(f"Sub-optimal milling temperature ({temp:.1f}°C < 65.0°C limit)")
    if speed < 1100.0 or speed > 1450.0:
        factors.append(f"Milling speed deviation ({speed:.0f} RPM outside 1100-1450 RPM)")
    if prod_time > 55.0:
        factors.append(f"Extended batch processing time ({prod_time:.1f} min > 55.0 min)")
    if quality_grade in ["Grade C", "Grade D"]:
        factors.append(f"Lower raw material quality grade ({quality_grade})")

    if not factors:
        factors.append("All operational parameters within standard operating ranges")

    contributing_str = "; ".join(factors)

    # Operational recommendations
    if risk_category == "LOW":
        recommendation = "Continue normal quality inspection. Parameters within optimal range."
    elif risk_category == "MEDIUM":
        recommendation = "Review production parameters. Perform targeted laboratory spot check before packaging."
    else:
        recommendation = "HOLD batch for full quality inspection. High probability of failing standards."

    return {
        "predicted_result": predicted_result,
        "pass_probability": round(pass_prob, 4),
        "fail_probability": round(fail_prob, 4),
        "risk_category": risk_category,
        "contributing_factors": contributing_str,
        "recommendation": recommendation,
        "inference_time_ms": inference_time_ms,
        "standardized_weight_kg": weight_kg
    }
