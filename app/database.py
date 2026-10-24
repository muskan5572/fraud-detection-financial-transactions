"""
Database management module for Fraud Detection System.
Provides SQLite persistence for transactions, case reviews, and audit logs.
"""

from __future__ import annotations

import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = ROOT_DIR / "outputs"
DATA_DIR = ROOT_DIR / "data"
DB_PATH = OUTPUTS_DIR / "fraud_cases.db"
CSV_FALLBACK = DATA_DIR / "sample_fraud_predictions.csv"
ROOT_CSV = ROOT_DIR / "sample_fraud_predictions.csv"


def get_connection() -> sqlite3.Connection:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables and seed if empty."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY,
            amount REAL NOT NULL,
            card_type TEXT NOT NULL,
            product_category TEXT NOT NULL,
            device TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            actual_fraud INTEGER NOT NULL,
            predicted_fraud INTEGER NOT NULL,
            fraud_probability REAL NOT NULL,
            risk_level TEXT NOT NULL,
            explanation TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending Review',
            assigned_analyst TEXT DEFAULT 'Unassigned',
            last_updated TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS analyst_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            analyst_name TEXT NOT NULL,
            decision TEXT NOT NULL,
            notes TEXT,
            action_taken TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            details TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )
    conn.commit()

    # Check if transactions table needs seeding
    cursor.execute("SELECT COUNT(*) FROM transactions")
    count = cursor.fetchone()[0]

    if count == 0:
        seed_database(conn)

    conn.close()


def seed_database(conn: sqlite3.Connection) -> None:
    """Seed the database using sample_fraud_predictions.csv with enriched fields."""
    csv_path = CSV_FALLBACK if CSV_FALLBACK.exists() else ROOT_CSV
    if not csv_path.exists():
        return

    df = pd.read_csv(csv_path)

    # Deterministic pseudo-random generation based on TransactionID
    records = []
    base_time = datetime.now() - timedelta(days=7)
    card_types = ["Visa Debit", "Mastercard Credit", "Amex Corporate", "Discover Prepaid"]
    categories = ["E-Commerce (W)", "Retail Checkout (C)", "Subscription (R)", "Hotel/Travel (H)", "Software (S)"]
    devices = ["Windows Chrome", "iOS Safari", "Android App", "MacOS Safari", "Linux Firefox"]

    for idx, row in df.iterrows():
        tx_id = int(row["TransactionID"])
        rng = random.Random(tx_id)

        # Higher risk transactions tend to have larger amounts
        prob = float(row["fraud_probability"])
        base_amt = rng.uniform(25.0, 450.0)
        if prob > 0.7:
            base_amt += rng.uniform(500.0, 2500.0)
        elif prob > 0.4:
            base_amt += rng.uniform(100.0, 600.0)
        amount = round(base_amt, 2)

        card = rng.choice(card_types)
        cat = rng.choice(categories)
        dev = rng.choice(devices)
        tx_time = (base_time + timedelta(minutes=int(rng.uniform(1, 10080)))).strftime("%Y-%m-%d %H:%M:%S")

        status = "Pending Review"
        if prob < 0.2 and row["actual_fraud"] == 0:
            status = "Auto-Approved"

        records.append(
            (
                tx_id,
                amount,
                card,
                cat,
                dev,
                tx_time,
                int(row["actual_fraud"]),
                int(row["predicted_fraud"]),
                round(prob, 4),
                str(row["risk_level"]),
                str(row.get("explanation", "Standard behavioral risk profile")),
                status,
                "Unassigned",
                tx_time,
            )
        )

    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT OR IGNORE INTO transactions (
            transaction_id, amount, card_type, product_category, device,
            timestamp, actual_fraud, predicted_fraud, fraud_probability,
            risk_level, explanation, status, assigned_analyst, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO audit_log (event_type, details, timestamp) VALUES (?, ?, ?)",
        ("DATABASE_INIT", f"Initialized and seeded {len(records)} cases from CSV.", now_str),
    )
    conn.commit()


def get_all_transactions(
    risk_filter: Optional[List[str]] = None,
    status_filter: Optional[List[str]] = None,
    search_id: Optional[int] = None,
) -> pd.DataFrame:
    """Retrieve transactions filtered by risk level, status, or ID."""
    conn = get_connection()
    query = "SELECT * FROM transactions WHERE 1=1"
    params: List[Any] = []

    if risk_filter:
        placeholders = ",".join("?" for _ in risk_filter)
        query += f" AND risk_level IN ({placeholders})"
        params.extend(risk_filter)

    if status_filter:
        placeholders = ",".join("?" for _ in status_filter)
        query += f" AND status IN ({placeholders})"
        params.extend(status_filter)

    if search_id is not None:
        query += " AND transaction_id = ?"
        params.append(search_id)

    query += " ORDER BY fraud_probability DESC"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_transaction_by_id(tx_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single transaction by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (tx_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def submit_review(
    tx_id: int,
    analyst_name: str,
    decision: str,
    notes: str,
    action_taken: str = "None",
) -> bool:
    """Record an analyst decision, update case status, and log the event."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Map decision to status
    status_map = {
        "Confirmed Fraud": "Confirmed Fraud",
        "Genuine / False Positive": "False Positive / Cleared",
        "Escalate for Audit": "Under Investigation",
        "Need More Info": "Pending Review",
    }
    new_status = status_map.get(decision, "Under Investigation")

    cursor.execute(
        """
        INSERT INTO analyst_reviews (
            transaction_id, analyst_name, decision, notes, action_taken, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (tx_id, analyst_name, decision, notes, action_taken, now_str),
    )

    cursor.execute(
        """
        UPDATE transactions
        SET status = ?, assigned_analyst = ?, last_updated = ?
        WHERE transaction_id = ?
        """,
        (new_status, analyst_name, now_str, tx_id),
    )

    cursor.execute(
        """
        INSERT INTO audit_log (event_type, details, timestamp)
        VALUES (?, ?, ?)
        """,
        (
            "ANALYST_DECISION",
            f"Case #{tx_id} marked as '{decision}' by {analyst_name}. Action: {action_taken}",
            now_str,
        ),
    )

    conn.commit()
    conn.close()
    return True


def record_action(tx_id: int, action: str, details: str) -> None:
    """Record an emergency action like Block Card or Send Alert."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT INTO audit_log (event_type, details, timestamp)
        VALUES (?, ?, ?)
        """,
        ("SECURITY_ACTION", f"Action '{action}' on Tx #{tx_id}: {details}", now_str),
    )
    conn.commit()
    conn.close()


def get_review_history() -> pd.DataFrame:
    """Fetch review history ordered by timestamp descending."""
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT r.id, r.transaction_id, r.analyst_name, r.decision,
               r.action_taken, r.notes, r.timestamp,
               t.amount, t.fraud_probability, t.risk_level
        FROM analyst_reviews r
        LEFT JOIN transactions t ON r.transaction_id = t.transaction_id
        ORDER BY r.timestamp DESC
        """,
        conn,
    )
    conn.close()
    return df


def get_audit_log(limit: int = 50) -> pd.DataFrame:
    """Fetch recent audit log entries."""
    conn = get_connection()
    df = pd.read_sql_query(
        f"SELECT * FROM audit_log ORDER BY id DESC LIMIT {limit}",
        conn,
    )
    conn.close()
    return df


def get_summary_metrics() -> Dict[str, Any]:
    """Calculate key fraud metrics for the executive dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*), AVG(amount), AVG(fraud_probability), SUM(amount) FROM transactions")
    total_count, avg_amt, avg_prob, total_vol = cursor.fetchone()

    cursor.execute("SELECT COUNT(*), SUM(amount) FROM transactions WHERE risk_level = 'High Risk'")
    high_risk_count, high_risk_vol = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM transactions WHERE status = 'Confirmed Fraud'")
    confirmed_fraud_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM transactions WHERE status = 'Pending Review'")
    pending_count = cursor.fetchone()[0]

    conn.close()

    return {
        "total_count": total_count or 0,
        "avg_amount": round(avg_amt or 0.0, 2),
        "avg_probability": round(avg_prob or 0.0, 3),
        "total_volume": round(total_vol or 0.0, 2),
        "high_risk_count": high_risk_count or 0,
        "high_risk_volume": round(high_risk_vol or 0.0, 2),
        "confirmed_fraud_count": confirmed_fraud_count or 0,
        "pending_count": pending_count or 0,
    }


def insert_transaction(data: Dict[str, Any]) -> int:
    """Insert a new transaction into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    tx_id = data.get("transaction_id")
    if tx_id is None:
        cursor.execute("SELECT MAX(transaction_id) FROM transactions")
        max_id = cursor.fetchone()[0] or 3600000
        tx_id = max_id + 1

    cursor.execute(
        """
        INSERT INTO transactions (
            transaction_id, amount, card_type, product_category, device,
            timestamp, actual_fraud, predicted_fraud, fraud_probability,
            risk_level, explanation, status, assigned_analyst, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tx_id,
            float(data.get("amount", 100.0)),
            str(data.get("card_type", "Visa Debit")),
            str(data.get("product_category", "E-Commerce (W)")),
            str(data.get("device", "Windows Chrome")),
            data.get("timestamp", now_str),
            int(data.get("actual_fraud", 0)),
            int(data.get("predicted_fraud", 0)),
            round(float(data.get("fraud_probability", 0.0)), 4),
            str(data.get("risk_level", "Low Risk")),
            str(data.get("explanation", "Scored via Real-time Engine")),
            str(data.get("status", "Pending Review")),
            str(data.get("assigned_analyst", "Unassigned")),
            now_str,
        ),
    )

    cursor.execute(
        "INSERT INTO audit_log (event_type, details, timestamp) VALUES (?, ?, ?)",
        ("TRANSACTION_INGESTED", f"Ingested new transaction #{tx_id} (${data.get('amount')})", now_str),
    )

    conn.commit()
    conn.close()
    return tx_id
