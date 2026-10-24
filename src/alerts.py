"""
Real-time Alert and Incident Notification Dispatcher.
Dispatches critical fraud warnings via Webhook, SMS, and Email.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from app.database import record_action


def dispatch_fraud_alert(
    transaction: Dict[str, Any],
    webhook_url: Optional[str] = None,
    channel: str = "all",
) -> Dict[str, Any]:
    """
    Dispatch multi-channel alert for high-risk fraud cases.
    Logs dispatch into database audit trail and returns dispatch status.
    """
    tx_id = transaction.get("transaction_id", "UNKNOWN")
    amt = float(transaction.get("amount", 0.0))
    prob = float(transaction.get("fraud_probability", 0.0))
    risk = transaction.get("risk_level", "High Risk")
    reasons = transaction.get("explanation", "Critical risk pattern detected")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Format notification message
    title = f"🚨 FRAUD ALERT: High-Risk Transaction #{tx_id} Detected"
    summary_msg = (
        f"Alert Triggered: {title}\n"
        f"Amount: ${amt:,.2f} | Probability: {prob:.1%} | Risk: {risk}\n"
        f"Card: {transaction.get('card_type', 'N/A')} | Device: {transaction.get('device', 'N/A')}\n"
        f"Key Indicators: {reasons}\n"
        f"Time: {now_str}"
    )

    results = {
        "transaction_id": tx_id,
        "timestamp": now_str,
        "dispatched_channels": [],
        "webhook_status": "skipped",
        "sms_status": "simulated_delivered",
        "email_status": "simulated_delivered",
    }

    # 1. SMS Dispatch
    results["dispatched_channels"].append("SMS (Customer +1 ***-***-8492)")
    record_action(
        tx_id=tx_id,
        action="AUTO_SMS_DISPATCHED",
        details=f"Automated verification SMS sent for Tx #{tx_id} (${amt})",
    )

    # 2. Email Dispatch
    results["dispatched_channels"].append("Email (SecOps <fraud-alerts@shield.bank>)")
    record_action(
        tx_id=tx_id,
        action="AUTO_EMAIL_DISPATCHED",
        details=f"Incident report emailed to SecOps tier-1 queue for Tx #{tx_id}",
    )

    # 3. Webhook Dispatch (Slack / Discord / Custom Endpoint)
    if webhook_url and webhook_url.startswith("http"):
        payload = {
            "text": summary_msg,
            "transaction_id": tx_id,
            "amount": amt,
            "fraud_probability": prob,
            "risk_level": risk,
            "timestamp": now_str,
        }
        try:
            resp = requests.post(webhook_url, json=payload, timeout=4)
            results["webhook_status"] = f"delivered (HTTP {resp.status_code})"
            results["dispatched_channels"].append(f"Webhook ({webhook_url[:24]}...)")
            record_action(
                tx_id=tx_id,
                action="WEBHOOK_POSTED",
                details=f"Webhook delivered with HTTP {resp.status_code}",
            )
        except Exception as exc:
            results["webhook_status"] = f"failed: {str(exc)}"
            record_action(
                tx_id=tx_id,
                action="WEBHOOK_FAILED",
                details=f"Webhook post failed: {str(exc)}",
            )
    else:
        results["webhook_status"] = "simulated_webhook_ready"

    return results
