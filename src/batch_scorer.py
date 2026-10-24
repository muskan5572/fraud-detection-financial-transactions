"""
Batch Transaction Scoring Engine.
Processes multi-record CSV files, assigns fraud risk, and generates summaries.
"""

from __future__ import annotations

from typing import Dict, Tuple
import pandas as pd

from src.predictor import score_transaction


def process_batch_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Score a batch DataFrame and return the enriched DataFrame with summary stats.
    Gracefully handles flexible column naming.
    """
    scored_records = []

    # Map possible column names
    col_map = {c.lower(): c for c in df.columns}
    amt_col = col_map.get("amount") or col_map.get("transactionamt") or col_map.get("amt")
    card_col = col_map.get("card_type") or col_map.get("card") or col_map.get("payment_method")
    cat_col = col_map.get("product_category") or col_map.get("category") or col_map.get("productcd")
    dev_col = col_map.get("device") or col_map.get("deviceinfo") or col_map.get("client_device")
    id_col = col_map.get("transaction_id") or col_map.get("transactionid") or col_map.get("id")

    for idx, row in df.iterrows():
        tx_id = row[id_col] if id_col and pd.notna(row[id_col]) else 4000000 + idx
        try:
            amt = float(row[amt_col]) if amt_col and pd.notna(row[amt_col]) else 100.0
        except (ValueError, TypeError):
            amt = 100.0

        card = str(row[card_col]) if card_col and pd.notna(row[card_col]) else "Visa Debit"
        cat = str(row[cat_col]) if cat_col and pd.notna(row[cat_col]) else "E-Commerce (W)"
        dev = str(row[dev_col]) if dev_col and pd.notna(row[dev_col]) else "Windows Chrome"

        res = score_transaction(
            amount=amt,
            card_type=card,
            category=cat,
            device=dev,
        )

        res["transaction_id"] = tx_id
        scored_records.append(res)

    results_df = pd.DataFrame(scored_records)

    total_count = len(results_df)
    high_risk_count = len(results_df[results_df["risk_level"] == "High Risk"])
    avg_prob = float(results_df["fraud_probability"].mean()) if total_count > 0 else 0.0
    total_flagged_amt = float(results_df[results_df["risk_level"] == "High Risk"]["amount"].sum())

    summary = {
        "total_scored": total_count,
        "high_risk_count": high_risk_count,
        "high_risk_ratio": round((high_risk_count / total_count) if total_count > 0 else 0.0, 4),
        "avg_probability": round(avg_prob, 4),
        "total_flagged_amount": round(total_flagged_amt, 2),
    }

    return results_df, summary


def generate_sample_batch_csv() -> str:
    """Generate a sample CSV template for users to test batch scoring."""
    sample_df = pd.DataFrame([
        {"transaction_id": 9001, "amount": 145.20, "card_type": "Visa Debit", "product_category": "E-Commerce (W)", "device": "Windows Chrome"},
        {"transaction_id": 9002, "amount": 3200.00, "card_type": "Discover Prepaid", "product_category": "Hotel/Travel (H)", "device": "Linux Firefox"},
        {"transaction_id": 9003, "amount": 42.50, "card_type": "Mastercard Credit", "product_category": "Retail Checkout (C)", "device": "iOS Safari"},
        {"transaction_id": 9004, "amount": 2890.00, "card_type": "Amex Corporate", "product_category": "Software (S)", "device": "Android App"},
        {"transaction_id": 9005, "amount": 12.00, "card_type": "Visa Debit", "product_category": "Subscription (R)", "device": "MacOS Safari"},
    ])
    return sample_df.to_csv(index=False)
