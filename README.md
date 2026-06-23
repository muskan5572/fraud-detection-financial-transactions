# Real-Time Fraud Detection System

This project detects fraudulent financial transactions using machine learning.

## Features

- Fraud probability scoring
- Low, Medium, High risk classification
- Explainable AI reasoning
- Streamlit fraud analyst dashboard
- Analyst feedback storage
- Simulated SMS alert
- Simulated card blocking

## Dataset

IEEE-CIS Fraud Detection dataset from Kaggle.

https://www.kaggle.com/c/ieee-fraud-detection/data

## Model Performance

Accuracy: 86.02%
ROC AUC: 89.90%
Fraud Precision: 71%
Fraud Recall: 75%
Fraud F1-score: 73%

## How to Run

Install requirements:

pip install -r requirements.txt

Run dashboard:

streamlit run app/streamlit_app.py

## Project Structure

app/streamlit_app.py
data/sample_fraud_predictions.csv
models/fraud_model.pkl
outputs/explainable_fraud_results.csv
requirements.txt
README.md
.gitignore

## Disclaimer

This is an educational prototype and not a production banking system.
