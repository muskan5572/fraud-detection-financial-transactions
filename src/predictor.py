"""
Real-time fraud scoring and risk evaluation engine.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, Tuple

import joblib
import numpy as np

from src.explainability import generate_explanation

ROOT_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT_DIR / "fraud_model.pkl"

_cached_model = None


def load_model():
    global _cached_model
    if _cached_model is None and MODEL_PATH.exists():
        try:
            _cached_model = joblib.load(MODEL_PATH)
        except Exception:
            _cached_model = None
    return _cached_model


def score_transaction(
    amount: float,
    card_type: str = "Visa Debit",
    category: str = "E-Commerce (W)",
    device: str = "Windows Chrome",
    custom_risk_seed: int = 42,
) -> Dict[str, Any]:
    """
    Score a transaction in real-time, computing fraud probability,
    risk level, predicted class, and explainability factors.
    """
    # Base probability calculated from key risk vectors
    score = 0.08  # Baseline natural fraud rate

    # Amount weighting
    if amount > 2500:
        score += 0.45
    elif amount > 1000:
        score += 0.30
    elif amount > 400:
        score += 0.15
    elif amount < 5.0:
        score += 0.10  # Micro-transaction card testing

    # Card type weighting
    if "Prepaid" in card_type:
        score += 0.22
    elif "Corporate" in card_type:
        score += 0.12
    elif "Amex" in card_type:
        score += 0.08

    # Category weighting
    if "Software" in category or "Travel" in category or "Hotel" in category:
        score += 0.18
    elif "Subscription" in category:
        score += 0.09

    # Device weighting
    if "Linux" in device:
        score += 0.15
    elif "Android" in device:
        score += 0.08

    # Normalize score between 0.01 and 0.99
    fraud_prob = min(max(score, 0.015), 0.985)
    fraud_prob = round(float(fraud_prob), 4)

    # Risk level classification
    if fraud_prob >= 0.70:
        risk_level = "High Risk"
        predicted_fraud = 1
    elif fraud_prob >= 0.35:
        risk_level = "Medium Risk"
        predicted_fraud = 0
    else:
        risk_level = "Low Risk"
        predicted_fraud = 0

    explanation = generate_explanation(amount, card_type, device, category, fraud_prob)

    return {
        "amount": amount,
        "card_type": card_type,
        "product_category": category,
        "device": device,
        "fraud_probability": fraud_prob,
        "predicted_fraud": predicted_fraud,
        "risk_level": risk_level,
        "explanation": explanation,
    }
