# FOOD PLANT AI
### Smart Spice Production, Quality Prediction and Manufacturing Intelligence System

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B.svg)](https://streamlit.io/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.5+-F7931E.svg)](https://scikit-learn.org/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL--Mode-003B57.svg)](https://sqlite.org/)
[![Pytest](https://img.shields.io/badge/Pytest-Passing-brightgreen.svg)](https://docs.pytest.org/)
[![FSSAI](https://img.shields.io/badge/Compliance-FSSAI--Aligned-green.svg)](https://www.fssai.gov.in/)

---

## 1. Project Introduction
**FOOD PLANT AI** is an industrial-grade, AI-powered manufacturing intelligence and quality prediction system developed for a commercial spice manufacturing facility operating in **Hyderabad, Telangana**. 

The facility manufactures four high-volume spice products:
1. **Chilli Powder** (Guntur S4 & Teja chillies)
2. **Turmeric Powder** (Nizamabad & Duggirala turmeric)
3. **Coriander Powder** (Deccan & Begum Bazaar coriander seeds)
4. **Garam Masala** (Malabar whole spice blend)

Operating across three dedicated production lines (**Line 1, Line 2, Line 3**), the facility handles thousands of batches per month. FOOD PLANT AI introduces artificial intelligence and automated decision support to minimize batch rejection rates, optimize milling process parameters, track raw material suppliers, and maintain end-to-end traceability compliant with food safety regulations.

> ⚠️ **Dataset Notice:** The dataset of 306,000 raw production records and 300,000 cleaned records used for modeling and demonstration is **SYNTHETIC DEMONSTRATION DATA** generated via `src/data_generator.py`. It is generated with realistic manufacturing physics, realistic data-quality challenges, and reproducible random seeds. It does not represent proprietary records of any real commercial entity.

---

## 2. Problem Statement
Commercial spice grinding and processing operations suffer from high quality variability due to:
- **Excessive Thermal Degradation:** Unmonitored high-speed milling causes grinding chamber temperatures to exceed 85°C, burning volatile essential oils that give spices their aroma and medicinal value.
- **Microbial & Clumping Hazards:** Raw spice shipments arriving with moisture levels above 12% trigger microbial spoilage, caking, and potential aflatoxin risk.
- **Late-Stage Quality Discovery:** Traditional operations only discover defects after packaging when laboratory sample results return days later, wasting raw materials, energy, packaging, and labor.
- **Financial Loss:** A single failed commercial batch causes an average loss of **₹15,000 to ₹25,000** in rework, downgrading, or disposal.

---

## 3. Project Objectives
1. **Predict Quality Outcomes:** Train and deploy a supervised machine learning model that predicts batch quality (**PASS** or **FAIL**) in real time before final packaging.
2. **Early Warning Risk Scoring:** Categorize production risk into **LOW**, **MEDIUM**, and **HIGH** tiers with human-readable contributing factor explanations.
3. **End-to-End Enterprise Operations:** Implement a full **CRUD** system for production batches, suppliers, and raw materials with SQLite foreign-key constraints and immutable audit logging.
4. **Machine Parameter Monitoring:** Provide historical operating parameter tracking with configurable alert boundaries.
5. **Regulatory & Responsible AI Compliance:** Embed human-in-the-loop oversight aligned with the **Food Safety and Standards Act (FSSAI), 2006**.
6. **Financial ROI Demonstration:** Provide an interactive ROI calculator projecting monthly and annual net savings.

---

## 4. End-to-End Business Workflow

```
[ Farm / Supplier ] ──────> [ Raw Material Intake ] ──────> [ Batch Staging & Milling ]
  Begum Bazaar, Guntur,       Moisture Check (kg/g)         Lines 1, 2, 3 (RPM, Temp, Time)
  Nizamabad Hubs              Quality Grade A/B/C/D                        │
                                                                           ▼
[ Certified Dispatch ] <──── [ QA Decision Support ] <────── [ FOOD PLANT AI Inference ]
  FSSAI Traceable Batch       Human Inspector Clears        Predicted PASS/FAIL & Risk Tier
  Ground Truth Logged         or Quarantines Batch           Inference Latency: < 1.0 ms
```

---

## 5. Eight AI Opportunities & Prioritization Matrix

| # | AI Opportunity | Business Impact | Technical Feasibility | Implementation Complexity | Priority Score | Status |
|---|---|---|---|---|---|---|
| **1** | **Batch Quality Classification** | **High (Direct Loss Reduction)** | **High (Supervised ML)** | **Low (Software-only)** | **92 / 100** | **★ SELECTED** |
| 2 | Dynamic Thermal Throttling | Medium (Energy & Flavor) | Medium (PLC/IoT required) | Medium | 78 / 100 | Future Phase |
| 3 | Supplier Quality Rating Engine | High (Supply Chain Quality) | High (Relational Data) | Low | 85 / 100 | Integrated |
| 4 | Predictive Rotor Maintenance | High (Uptime & Downtime) | Medium (Vibration Sensors) | High | 71 / 100 | Future Phase |
| 5 | Yield Conversion Optimization | Medium (Waste Reduction) | High (Regression Model) | Low | 81 / 100 | Integrated |
| 6 | Automated Packaging Vision QC | Medium (Label/Sealing) | Medium (Camera System) | Medium | 75 / 100 | Future Phase |
| 7 | Dynamic Line Scheduling | Medium (Throughput) | Medium (Operations Research)| Medium | 68 / 100 | Future Phase |
| 8 | FSSAI Compliance Risk Audit | High (Legal & Quality) | High (Rule-based NLP) | Low | 88 / 100 | Integrated |

---

## 6. Selected AI Use Case: Pre-Packaging Quality Classification
- **Task:** Supervised Binary Classification (`Quality_Result` $\in$ {`PASS`, `FAIL`})
- **Input Features:** Raw material weight (kg), moisture level (%), machine temperature (°C), machine speed (RPM), production cycle time (min), raw material quality grade, production line, spice type.
- **Output:** Predicted outcome + continuous failure probability ($P(\text{FAIL})$) + risk category + specific operational recommendations.
- **Core Benefit:** Enables preemptive diversion of defective product before packaging, saving substantial financial and labor resources.

---

## 7. Dataset Description & Challenges

The dataset was generated in chunks using `src/data_generator.py` and saved to `data/raw_production_data.csv`:
- **Volume:** 306,000 raw production records across Lines 1, 2, and 3.
- **Time Window:** 3 complete years (January 1, 2022 to December 31, 2024).
- **Target Distribution:** 61.3% PASS (187,570) / 38.7% FAIL (118,430).
- **Deliberate Data-Quality Challenges:**
  - **19 Supplier Name Variations:** Simulating real-world manual entry errors (e.g., `hyd spice traders`, `Tel Agro Mills`).
  - **Mixed Measurement Units:** 30% of records recorded in grams, 70% in kilograms.
  - **Reused Batch Numbers:** Cycling pool of 1,785 unique `BCH-XXXX` labels to test non-unique external identifier handling.
  - **Missing Values:** 5% missing in `Moisture_Level` (15,233 rows), 3% missing in `Machine_Temperature` (9,201 rows).
  - **Duplicate Rows:** Exactly 6,000 duplicate rows (~2.0%) introduced into the raw stream.

---

## 8. Data Preprocessing Pipeline (`src/preprocessing.py`)
To prevent data leakage, preprocessing steps are strictly isolated:
1. **Supplier Canonicalization:** String-mapped 19 spelling variations down to 6 certified suppliers.
2. **Standardized Weight Conversion:** All gram rows converted to kilograms (`Standardized_Weight_Kg`).
3. **Missing Value Imputation:** Grouped line-median imputation for moisture and temperature.
4. **Deduplication:** Purged exact duplicate rows while retaining legitimately reused batch numbers with unique internal `Record_ID`s.
5. **Feature Engineering:**
   - $\text{Efficiency Ratio} = \frac{\text{Final Product Weight (kg)}}{\text{Raw Material Weight (kg)}}$
   - $\text{Temp in Range} = \mathbb{I}(65^\circ\text{C} \le T \le 85^\circ\text{C})$
   - $\text{Speed in Range} = \mathbb{I}(1100 \le \text{RPM} \le 1450)$
   - $\text{Moisture Risk} = \mathbb{I}(\text{Moisture} > 12.0\%)$
6. **Chronological Splitting:** 70% Train (210,000), 15% Validation (45,000), 15% Test (45,000).

---

## 9. Machine Learning Benchmarks (`src/train_model.py`)

Four machine learning classifiers were trained and benchmarked on the 45,000-record test set:

| Classifier | Test Accuracy | Weighted F1 | ROC-AUC | FAIL-Class Recall | Inference Latency | Selected |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Gradient Boosting** | **71.32%** | **0.6958** | **0.7446** | **44.74%** | **0.74 ms** | **★ BEST MODEL** |
| Random Forest | 71.35% | 0.6956 | 0.7441 | 44.45% | 38.53 ms | Alternative |
| Logistic Regression | 71.12% | 0.6934 | 0.7374 | 44.29% | 0.75 ms | Baseline |
| Decision Tree | 71.02% | 0.6916 | 0.7380 | 43.70% | 0.60 ms | Baseline |

> **Honest Performance Disclosure:** The ~71.3% test accuracy reflects genuine manufacturing physics where biological variance in agricultural products and ambient weather introduce real-world uncertainty. The model is tuned for high FAIL-class recall to prevent unsafe batches from escaping notice.

---

## 10. System Architecture

```
Food_Plant_AI/
│
├── app.py                       # Main Streamlit application with custom navigation
├── database.py                  # SQLite WAL database management & ACID transactions
├── requirements.txt             # Open-source Python dependencies
├── README.md                    # Project documentation
├── .gitignore                   # Excludes temporary files & virtual environments
│
├── data/
│   ├── sample_data.csv          # Clean 1,000-record sample dataset
│   ├── data_dictionary.csv      # Complete column schemas & descriptions
│   ├── raw_production_data.csv  # 306,000 synthetic production records
│   └── cleaned_production_data.csv # 300,000 preprocessed production records
│
├── models/
│   ├── quality_model.pkl        # Best trained model (Gradient Boosting)
│   ├── preprocessing_pipeline.pkl # Scikit-learn ColumnTransformer
│   └── model_metadata.pkl       # Feature names, metrics, and training metadata
│
├── src/
│   ├── data_generator.py        # Generates ~300k synthetic spice production records
│   ├── preprocessing.py         # Data cleaning, unit conversion, feature engineering
│   ├── train_model.py           # Model training, hyperparameter tuning & evaluation
│   ├── prediction.py            # Single-record inference & risk categorization
│   ├── evaluation.py            # Independent test case evaluation & cost metrics
│   ├── roi_calculator.py        # Business ROI simulation logic
│   └── generate_presentation.py # Script generating the 12-slide PowerPoint presentation
│
├── pages/
│   ├── dashboard.py             # 1. Executive Dashboard (KPIs & Plotly charts)
│   ├── production.py            # 2. Production Management (Full CRUD)
│   ├── suppliers.py             # 3. Supplier Management (CRUD & relationships)
│   ├── raw_materials.py         # 4. Raw Material Management (Inventory & moisture)
│   ├── dataset.py               # 5. Dataset Management (Upload/Download/Preview)
│   ├── prediction.py            # 6. AI Quality Prediction (Interactive inference)
│   ├── history.py               # 7. Prediction History (Ground truth recording)
│   ├── machine_monitoring.py    # 8. Machine Monitoring (Parameter trends & alerts)
│   ├── model_performance.py     # 9. Model Performance (Confusion matrix, ROC)
│   ├── roi.py                   # 10. ROI Calculator (Financial simulation)
│   ├── responsible_ai.py        # 11. Responsible AI (Ethics, FSSAI, bias audit)
│   └── settings.py              # 12. Settings (Operating limits & WAL backups)
│
├── tests/
│   ├── test_crud.py             # 18 unit tests for CRUD operations
│   ├── test_database.py         # 4 unit tests for SQLite, WAL, audit & backups
│   └── test_model.py            # 5 unit tests for ML pipeline & 50+ test cases
│
└── reports/
    ├── test_results.csv         # 45,000 independent test evaluation records
    ├── model_evaluation.txt     # Complete textual model benchmark report
    ├── confusion_matrix.png     # Gradient Boosting confusion matrix visualization
    ├── feature_importance.png   # Top 15 feature importance chart
    └── Food_Plant_AI_Business_Case.pptx # Professional 12-slide presentation
```

---

## 11. Application Features (12 Operational Pages)

1. **Executive Dashboard (`pages/dashboard.py`):** Real-time KPI summary cards, monthly stacked production charts, spice quality breakdowns, line performance comparisons, and supplier fail rates calculated dynamically from SQLite.
2. **Production Management (`pages/production.py`):** Complete CRUD system supporting creation, editing, deletion, and searching of production batches. Features automatic unit conversion, unique internal `Record_ID` tracking, and audit logging.
3. **Supplier Management (`pages/suppliers.py`):** Supplier registry with contact information, regional locations, material types, and relational foreign-key deletion protection.
4. **Raw Material Management (`pages/raw_materials.py`):** Warehouse intake logging with standardized kilogram conversions and quality grading.
5. **Dataset Management (`pages/dataset.py`):** File upload validation, CSV download, and automated data quality audits.
6. **AI Quality Prediction (`pages/prediction.py`):** Interactive prediction form outputting PASS/FAIL status, failure probabilities, risk categories (LOW, MEDIUM, HIGH), contributing factors, and inspection guidance.
7. **Prediction History (`pages/history.py`):** Searchable inference history allowing authorized QA staff to log actual laboratory test results against historical predictions.
8. **Machine Monitoring (`pages/machine_monitoring.py`):** Parameter trend scatter plots with configurable operating threshold reference lines.
9. **Model Performance (`pages/model_performance.py`):** Diagnostic charts, ROC curves, feature importance ranking, and verification of 50+ independent test cases.
10. **ROI Calculator (`pages/roi.py`):** Dynamic financial model simulating monthly savings, annual net benefit, payback periods, and 3-year projection curves.
11. **Responsible AI (`pages/responsible_ai.py`):** Algorithmic bias analysis, FSSAI food safety regulatory mapping, data privacy assurances, and immutable system audit logs.
12. **Settings (`pages/settings.py`):** Configuration of factory operating limits, plant metadata, and point-in-time SQLite database backups and restores.

---

## 12. Installation & Setup Instructions

### Prerequisites
- Python 3.10 to 3.14
- Operating System: Windows, Linux, or macOS

### Step 1: Clone or Open Project Directory
```powershell
cd "c:\Users\keert\OneDrive\Desktop\internship project"
```

### Step 2: Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 3: (Optional) Regenerate Synthetic Data & Models
If you wish to re-create the dataset and re-train the models from scratch:
```powershell
python src/data_generator.py
python src/preprocessing.py
python src/train_model.py
python src/generate_presentation.py
```

### Step 4: Run the Application
```powershell
python -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 13. Automated Test Suite

FOOD PLANT AI includes a comprehensive automated test suite powered by **Pytest**:

```powershell
python -m pytest tests/ -v
```

### Test Results Summary:
```
tests/test_crud.py::test_add_supplier PASSED
tests/test_crud.py::test_add_and_retrieve_supplier PASSED
tests/test_crud.py::test_edit_supplier PASSED
tests/test_crud.py::test_delete_supplier_no_batches PASSED
tests/test_crud.py::test_delete_supplier_with_batches_blocked PASSED
tests/test_crud.py::test_add_production_batch PASSED
tests/test_crud.py::test_batch_persists_after_retrieval PASSED
tests/test_crud.py::test_batch_search_by_batch_id PASSED
tests/test_crud.py::test_edit_production_batch PASSED
tests/test_crud.py::test_delete_production_batch PASSED
tests/test_crud.py::test_reused_batch_number_allowed PASSED
tests/test_crud.py::test_filter_by_quality_status PASSED
tests/test_crud.py::test_weight_unit_standardization_grams PASSED
tests/test_crud.py::test_audit_log_created_on_insert PASSED
tests/test_crud.py::test_audit_log_created_on_delete PASSED
tests/test_crud.py::test_add_raw_material PASSED
tests/test_crud.py::test_raw_material_gram_conversion PASSED
tests/test_crud.py::test_raw_material_persists PASSED
tests/test_database.py::test_database_initialization PASSED
tests/test_database.py::test_default_settings_and_suppliers_seeded PASSED
tests/test_database.py::test_audit_logging PASSED
tests/test_database.py::test_backup_and_restore PASSED
tests/test_model.py::test_model_and_pipeline_loading PASSED
tests/test_model.py::test_prediction_pass_case PASSED
tests/test_model.py::test_prediction_fail_case PASSED
tests/test_model.py::test_gram_weight_standardization_in_prediction PASSED
tests/test_model.py::test_fifty_independent_model_evaluation_cases PASSED

============================= 27 passed in 7.06s =============================
```

---

## 14. Return on Investment (ROI) Analysis

Based on standard spice production operations for a 500-batch/month milling facility:

$$\text{ROI} = \frac{\text{Net Annual Benefit} - 0}{\text{Initial Investment} + \text{Annual Maintenance}} \times 100$$

### Financial Breakdown:
- **Monthly Production:** 500 batches
- **Historical Failure Rate:** 25.0% (125 failed batches/month)
- **Financial Loss per Failure:** ₹15,000
- **Monthly Baseline Financial Loss:** ₹18,75,000
- **AI Preventable Defect Rate:** 65.0%
- **Monthly Net Savings:** **₹12,18,750**
- **Annual Gross Savings:** **₹1,46,25,000** (~₹1.46 Crores)
- **One-Time Development Investment:** ₹5,00,000
- **Annual Maintenance & Support:** ₹1,20,000
- **Net Annual Benefit:** **₹1,45,05,000**
- **Payback Period:** **0.4 Months (< 15 operating days)**

---

## 15. Responsible AI & FSSAI Regulatory Alignment
- **Human-in-the-Loop Governance:** AI strictly functions as a risk-screening aid. No food batch is released or discarded without an authorized QA signature.
- **FSSAI Compliance:** Process aligns with Section 23 and Schedule 4 of the Food Safety and Standards Act (2006) for moisture control and contamination prevention.
- **Supplier Fairness:** Physical sensor attributes drive >90% of model feature importance, mitigating geographic or supplier-size discrimination.
- **Immutable Audit Logging:** Every create, edit, delete, backup, and inference event is recorded with timestamps, user identities, and details in `Audit_Logs`.
- **Data Sovereignty:** Operates 100% locally with zero cloud API dependencies or data exposure.

---

## 16. Future Roadmap
- **Phase 2:** MQTT / Modbus IoT sensor integration for live PLC telemetry streaming.
- **Phase 3:** Computer vision grading for whole chilli and turmeric pods at the intake dock.
- **Phase 4:** Closed-loop automated milling speed control to prevent overheating in real time.
- **Phase 5:** Multi-plant federated learning across Telangana and Andhra Pradesh spice processing hubs.

---

## 17. License
Open-source software developed for academic research, internship project evaluation, and industrial demonstration. All tools and packages utilized are free and open-source.
