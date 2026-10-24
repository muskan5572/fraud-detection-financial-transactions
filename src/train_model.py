"""
End-to-End Machine Learning Training Pipeline for Financial Fraud Detection.
Trains an ensemble model (RandomForest/XGBoost) and saves evaluation metrics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = ROOT_DIR / "outputs"
MODELS_DIR = ROOT_DIR / "models"
MODEL_PATH = ROOT_DIR / "fraud_model.pkl"


def generate_synthetic_transactions(n_samples: int = 10000, random_state: int = 42) -> Tuple[pd.DataFrame, pd.Series]:
    """Generate representative synthetic financial transaction data for training."""
    np.random.seed(random_state)

    # 96.5% genuine, 3.5% fraudulent transactions (realistic class imbalance)
    y = np.random.binomial(1, 0.035, size=n_samples)

    # Amounts: genuine transactions follow log-normal, fraud has higher variance & spikes
    amounts = np.where(
        y == 1,
        np.random.exponential(scale=650, size=n_samples) + 200,
        np.random.lognormal(mean=4.2, sigma=1.1, size=n_samples),
    )
    amounts = np.round(np.clip(amounts, 1.0, 10000.0), 2)

    # Feature engineering vectors (IEEE-CIS inspired)
    c1 = np.where(y == 1, np.random.poisson(12, n_samples), np.random.poisson(2, n_samples))
    c2 = np.where(y == 1, np.random.poisson(15, n_samples), np.random.poisson(2, n_samples))
    c13 = np.where(y == 1, np.random.poisson(25, n_samples), np.random.poisson(5, n_samples))
    c14 = np.where(y == 1, np.random.poisson(8, n_samples), np.random.poisson(1, n_samples))

    d1 = np.where(y == 1, np.random.exponential(15, n_samples), np.random.exponential(120, n_samples))
    v1 = np.random.normal(0, 1, n_samples)
    v2 = np.where(y == 1, np.random.normal(3.5, 1.5, n_samples), np.random.normal(0.2, 0.8, n_samples))

    df = pd.DataFrame({
        "TransactionAmt": amounts,
        "C1": c1,
        "C2": c2,
        "C13": c13,
        "C14": c14,
        "D1": d1,
        "V1": v1,
        "V2": v2,
    })

    return df, pd.Series(y, name="isFraud")


def train_and_evaluate() -> Dict[str, float]:
    """Train the model, calculate evaluation metrics, and export visualizations."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating training dataset...")
    X, y = generate_synthetic_transactions(n_samples=12000)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    print(f"Training set: {len(X_train)} samples, Test set: {len(X_test)} samples")
    print("Fitting Random Forest Classifier with balanced class weights...")

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred)), 4),
    }

    print("\n--- Model Performance Summary ---")
    for k, v in metrics.items():
        print(f"  {k.upper()}: {v:.4f}")

    # Save metrics JSON
    with open(OUTPUTS_DIR / "training_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # Plot ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    plt.figure(figsize=(7, 5))
    plt.plot(fpr, tpr, color="#2563eb", lw=2, label=f"ROC curve (AUC = {metrics['roc_auc']:.3f})")
    plt.plot([0, 1], [0, 1], color="#9ca3af", lw=1.5, linestyle="--")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate", fontsize=11)
    plt.ylabel("True Positive Rate (Recall)", fontsize=11)
    plt.title("Receiver Operating Characteristic (ROC) Curve", fontsize=13, fontweight="bold")
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUTS_DIR / "roc_curve.png", dpi=180)
    plt.close()

    # Plot Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(6, 5))
    plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    plt.title("Confusion Matrix", fontsize=13, fontweight="bold")
    plt.colorbar()
    tick_marks = np.arange(2)
    plt.xticks(tick_marks, ["Genuine", "Fraud"])
    plt.yticks(tick_marks, ["Genuine", "Fraud"])

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            color = "white" if cm[i, j] > cm.max() / 2 else "black"
            plt.text(j, i, format(cm[i, j], "d"), horizontalalignment="center", color=color, fontsize=12)

    plt.ylabel("True Label", fontsize=11)
    plt.xlabel("Predicted Label", fontsize=11)
    plt.tight_layout()
    plt.savefig(OUTPUTS_DIR / "confusion_matrix.png", dpi=180)
    plt.close()

    # Save model artifacts
    joblib.dump(model, MODELS_DIR / "fraud_model.pkl")
    print(f"Artifacts saved to {OUTPUTS_DIR}")
    return metrics


if __name__ == "__main__":
    train_and_evaluate()
