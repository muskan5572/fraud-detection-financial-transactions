# 🛡️ Real-Time Fraud Detection & Case Management System

[![FraudShield CI](https://github.com/muskan5572/fraud-detection-financial-transactions/actions/workflows/ci.yml/badge.svg)](https://github.com/muskan5572/fraud-detection-financial-transactions/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![ROC-AUC](https://img.shields.io/badge/ROC--AUC-89.90%25-success.svg)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end, enterprise-grade financial fraud surveillance platform built with Machine Learning, Streamlit, SQLite persistence, batch CSV scoring, real-time alert dispatchers, and a high-throughput REST API.

---

## 📑 Quick Links
- **[Career & Interview Guide (SHOWCASE.md)](SHOWCASE.md)** — Resume bullet points, LinkedIn announcement post, and technical interview FAQ.
- **[Cloud Deployment Guide (DEPLOYMENT.md)](DEPLOYMENT.md)** — Free 1-click deployment on Streamlit Cloud & Render.

---

## 🌟 Key Features

- **Executive Analytics Dashboard:** Real-time KPIs, transaction volume metrics, risk breakdown donut charts, and amount vs. fraud probability distributions.
- **Explainable AI (XAI) Case Triage:** Interactive case workbench featuring fraud probability gauges, natural language risk attribution, and analyst action controls (SMS alerts, card freezing).
- **High-Throughput Batch CSV Scoring:** Drag-and-drop CSV upload to score thousands of transactions in bulk with exportable reports and database ingestion.
- **Multi-Channel Incident Alerts:** Automated dispatch of critical fraud warnings via Webhooks (Slack/Discord), Customer SMS simulation, and SecOps email.
- **Persistent SQLite Database:** Structured audit trails, transaction records, and analyst review history stored persistently in `outputs/fraud_cases.db`.
- **Live Risk Scoring Simulator:** Test what-if payment scenarios and score custom transactions instantaneously.
- **RESTful API Service:** High-performance Starlette/Uvicorn API serving real-time scoring, case retrieval, and security actions.
- **Docker & Cloud Ready:** Containerized with `Dockerfile` and `docker-compose.yml`, ready for 1-click deployment to Streamlit Community Cloud and Render.
- **CI/CD Pipeline:** Automated testing workflow configured with GitHub Actions.

---

## 🏗️ Project Architecture

```
fraud-detection-financial-transactions/
├── .github/
│   └── workflows/
│       └── ci.yml              # Automated GitHub Actions test workflow
├── app/
│   ├── database.py             # SQLite persistence, seeding, case management & audit logging
│   └── streamlit_app.py        # 7-tab enterprise analytics, triage & batch dashboard
├── api/
│   └── server.py               # REST API (metrics, transactions, scoring, security actions)
├── src/
│   ├── alerts.py               # Multi-channel webhook & incident notification dispatcher
│   ├── batch_scorer.py         # Bulk CSV scoring engine and template generator
│   ├── explainability.py       # Risk factor attribution and feature importance
│   ├── predictor.py            # Real-time transaction scoring engine
│   └── train_model.py          # ML training pipeline, ROC curves & confusion matrix
├── tests/
│   └── test_system.py          # Automated integration & unit test suite (7 tests)
├── outputs/
│   ├── fraud_cases.db          # Live SQLite database
│   ├── roc_curve.png           # Model ROC curve plot
│   ├── confusion_matrix.png    # Validation confusion matrix plot
│   └── training_metrics.json   # Exported metrics (ROC-AUC, Precision, Recall, F1)
├── .streamlit/
│   └── config.toml             # Streamlit visual theme and production configuration
├── Dockerfile                  # Container definition for dashboard & API
├── docker-compose.yml          # Multi-container orchestration
├── DEPLOYMENT.md               # 1-click cloud deployment guide
├── SHOWCASE.md                 # Resume bullet points & LinkedIn announcement
├── requirements.txt
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Run with Docker (Recommended)
```bash
docker compose up -d --build
```
- Dashboard: [http://localhost:8501](http://localhost:8501)
- REST API: [http://localhost:8000](http://localhost:8000)

---

### 2. Run Locally in Python
```powershell
# Activate existing virtual environment
.\venv\Scripts\Activate.ps1

# Run the Streamlit Dashboard
.\venv\Scripts\streamlit.exe run app/streamlit_app.py

# Run the REST API Server (Optional)
.\venv\Scripts\python.exe api/server.py
```

---

### 3. Run Automated Tests
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
