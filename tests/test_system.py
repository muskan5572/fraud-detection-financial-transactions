"""
Automated unit and integration test suite for Fraud Detection System.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import unittest
from app.database import (
    get_all_transactions,
    get_summary_metrics,
    get_transaction_by_id,
    init_db,
    insert_transaction,
    record_action,
    submit_review,
)
from src.explainability import generate_explanation, get_feature_importances
from src.predictor import score_transaction


class TestFraudDetectionSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_database_initialization(self):
        metrics = get_summary_metrics()
        self.assertGreater(metrics["total_count"], 0)
        self.assertGreater(metrics["total_volume"], 0)
        self.assertIn("avg_probability", metrics)

    def test_get_transactions_filter(self):
        high_risk_df = get_all_transactions(risk_filter=["High Risk"])
        self.assertFalse(high_risk_df.empty)
        for _, row in high_risk_df.iterrows():
            self.assertEqual(row["risk_level"], "High Risk")

    def test_predictor_scoring(self):
        result_high = score_transaction(
            amount=4500.0,
            card_type="Discover Prepaid",
            category="Hotel/Travel (H)",
            device="Linux Firefox",
        )
        self.assertEqual(result_high["risk_level"], "High Risk")
        self.assertGreater(result_high["fraud_probability"], 0.70)
        self.assertIn("Unusually high transaction volume", result_high["explanation"])

        result_low = score_transaction(
            amount=25.0,
            card_type="Visa Debit",
            category="Retail Checkout (C)",
            device="Windows Chrome",
        )
        self.assertEqual(result_low["risk_level"], "Low Risk")
        self.assertLess(result_low["fraud_probability"], 0.35)

    def test_submit_review_and_status(self):
        df = get_all_transactions()
        sample_id = int(df.iloc[0]["transaction_id"])

        success = submit_review(
            tx_id=sample_id,
            analyst_name="Test Analyst",
            decision="Confirmed Fraud",
            notes="Automated test confirmation",
            action_taken="Card Blocked",
        )
        self.assertTrue(success)

        case = get_transaction_by_id(sample_id)
        self.assertEqual(case["status"], "Confirmed Fraud")
        self.assertEqual(case["assigned_analyst"], "Test Analyst")

    def test_explainability(self):
        importances = get_feature_importances()
        self.assertIn("Transaction Amount (TransactionAmt)", importances)
        self.assertGreater(len(importances), 5)


if __name__ == "__main__":
    unittest.main()
