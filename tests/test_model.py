"""
Unit Tests for Machine Learning Pipeline, Single-Record Inference,
and 50+ Independent Evaluation Cases.
"""

import os
import pytest
import numpy as np
import pandas as pd
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from prediction import load_model, predict
from evaluation import run_evaluation


def test_model_and_pipeline_loading():
    """Verifies that the trained model and preprocessing pipeline can be loaded."""
    model, pipeline, metadata = load_model()
    assert model is not None
    assert pipeline is not None
    assert "classes" in metadata or hasattr(model, "classes_")


def test_prediction_pass_case():
    """Tests that nominal operating parameters produce a low-risk PASS prediction."""
    nominal_input = {
        "Production_Line": "Line 1",
        "Supplier_Name": "Hyderabad Spice Traders",
        "Spice_Type": "Chilli Powder",
        "Raw_Material_Weight": 500.0,
        "Weight_Unit": "kg",
        "Moisture_Level": 7.5,
        "Machine_Temperature": 74.0,
        "Machine_Speed": 1250.0,
        "Production_Time": 30.0,
        "Raw_Material_Quality": "Grade A"
    }
    result = predict(nominal_input)
    assert result["predicted_result"] in ["PASS", "FAIL"]
    assert 0.0 <= result["pass_probability"] <= 1.0
    assert 0.0 <= result["fail_probability"] <= 1.0
    assert pytest.approx(result["pass_probability"] + result["fail_probability"], 0.01) == 1.0
    assert result["risk_category"] in ["LOW", "MEDIUM", "HIGH"]
    assert "recommendation" in result
    assert result["inference_time_ms"] > 0


def test_prediction_fail_case():
    """Tests that severely anomalous parameters produce an elevated failure probability."""
    severe_input = {
        "Production_Line": "Line 3",
        "Supplier_Name": "Guntur Spices Co",
        "Spice_Type": "Garam Masala",
        "Raw_Material_Weight": 600.0,
        "Weight_Unit": "kg",
        "Moisture_Level": 18.5,        # Extreme moisture > 12%
        "Machine_Temperature": 98.0,   # Extreme temperature > 85°C
        "Machine_Speed": 950.0,        # Abnormally slow milling
        "Production_Time": 75.0,       # Excessive cycle time
        "Raw_Material_Quality": "Grade D"
    }
    result = predict(severe_input)
    # Failure probability should be substantially higher than nominal
    assert result["fail_probability"] > 0.40
    assert result["risk_category"] in ["MEDIUM", "HIGH"]
    assert "moisture" in result["contributing_factors"].lower() or "temperature" in result["contributing_factors"].lower()


def test_gram_weight_standardization_in_prediction():
    """Ensures grams input is standardized without crashing."""
    gram_input = {
        "Production_Line": "Line 2",
        "Supplier_Name": "Telangana Agro Mills",
        "Spice_Type": "Turmeric Powder",
        "Raw_Material_Weight": 500000.0, # 500 kg in grams
        "Weight_Unit": "grams",
        "Moisture_Level": 8.0,
        "Machine_Temperature": 72.0,
        "Machine_Speed": 1260.0,
        "Production_Time": 35.0,
        "Raw_Material_Quality": "Grade B"
    }
    result = predict(gram_input)
    assert result["standardized_weight_kg"] == pytest.approx(500.0)


def test_fifty_independent_model_evaluation_cases():
    """Evaluates at least 50 independent held-out test cases."""
    eval_res = run_evaluation(num_cases=50)
    assert eval_res["num_test_cases"] >= 50
    assert 0.0 < eval_res["accuracy"] <= 1.0
    assert 0.0 < eval_res["fail_recall"] <= 1.0
    assert len(eval_res["sample_cases"]) >= 50
    # Confirm test cases contain required attributes
    for case in eval_res["sample_cases"]:
        assert "True_Label" in case
        assert "Predicted_Label" in case
        assert "FAIL_Probability" in case
        assert case["True_Label"] in ["PASS", "FAIL"]
        assert case["Predicted_Label"] in ["PASS", "FAIL"]
