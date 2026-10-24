# Real-Time Fraud Detection & Case Management System

An end-to-end, enterprise-grade financial fraud detection platform built with Machine Learning, Streamlit, SQLite persistence, and a high-throughput REST API.

---

## 🌟 Key Features

- **Executive Analytics Dashboard:** Real-time KPIs, transaction volume metrics, risk breakdown donut charts, and amount vs. fraud probability distributions.
- **Explainable AI (XAI) Case Triage:** Interactive case workbench featuring fraud probability gauges, natural language risk attribution, and analyst action controls (SMS alerts, card freezing).
- **Persistent SQLite Database:** Structured audit trails, transaction records, and analyst review history stored persistently in `outputs/fraud_cases.db`.
- **Live Risk Scoring Simulator:** Test what-if payment scenarios and score custom transactions instantaneously.
- **RESTful API Service:** High-performance Starlette/Uvicorn API serving real-time scoring, case retrieval, and security actions.
- **Machine Learning Pipeline:** End-to-end training pipeline for Random Forest and XGBoost with class-imbalance weighting, ROC-AUC evaluation, and artifact generation.

---

## 🏗️ Project Architecture

```
fraud-detection-financial-transactions/
├── app/
│   ├── database.py             # SQLite persistence, seeding, case management & audit logging
│   └── streamlit_app.py        # 5-tab enterprise analytics & triage dashboard
├── api/
│   └── server.py               # REST API (metrics, transactions, scoring, security actions)
├── src/
│   ├── explainability.py       # Risk factor attribution and feature importance
│   ├── predictor.py            # Real-time transaction scoring engine
│   └── train_model.py          # ML training pipeline, ROC curves & confusion matrix
├── tests/
│   └── test_system.py          # Automated integration & unit test suite
├── outputs/
│   ├── fraud_cases.db          # Live SQLite database
│   ├── roc_curve.png           # Model ROC curve plot
│   ├── confusion_matrix.png    # Validation confusion matrix plot
│   └── training_metrics.json   # Exported metrics (ROC-AUC, Precision, Recall, F1)
├── data/
│   └── sample_fraud_predictions.csv
├── models/
│   └── fraud_model.pkl
├── requirements.txt
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Environment Setup
```powershell
# Activate existing virtual environment
.\venv\Scripts\Activate.ps1

# Or install dependencies
pip install -r requirements.txt
```

### 2. Run the Streamlit Dashboard
```powershell
.\venv\Scripts\streamlit.exe run app/streamlit_app.py
```
Open your browser at **http://localhost:8501** (or port indicated in the terminal, e.g. **8502**).

### 3. Run the REST API Server (Optional)
```powershell
.\venv\Scripts\python.exe api/server.py
```
API runs on **http://127.0.0.1:8000**:
- `GET /api/metrics` — Dashboard aggregate KPIs
- `GET /api/transactions` — Query cases with risk/status filters
- `POST /api/score` — Score a new transaction in real-time
- `POST /api/cases/{id}/review` — Submit analyst determination
- `POST /api/cases/{id}/action` — Simulate card block or SMS alert

### 4. Retrain the ML Model
```powershell
.\venv\Scripts\python.exe src/train_model.py
```

### 5. Run the Automated Test Suite
```powershell
.\venv\Scripts\python.exe tests/test_system.py
```

---

## 📊 Model Performance

| Metric | Score |
| :--- | :--- |
| **ROC AUC** | **89.90%** |
| **Accuracy** | **86.02%** |
| **Precision** | **71.00%** |
| **Recall** | **75.00%** |
| **F1-Score** | **73.00%** |

---

## 🔒 Security & Audit Log

Every analyst review, customer alert, and payment card lock is logged in `outputs/fraud_cases.db` with exact timestamps and analyst credentials, exportable at any time as CSV from the **Audit Log & Feedback** tab.
