"""
RESTful API for Real-Time Financial Fraud Detection.
Powered by Starlette and Uvicorn.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.database import (
    get_all_transactions,
    get_review_history,
    get_summary_metrics,
    get_transaction_by_id,
    init_db,
    insert_transaction,
    record_action,
    submit_review,
)
from src.predictor import score_transaction

# Initialize database on startup
init_db()


async def root(request: Request) -> JSONResponse:
    """Root health and discovery endpoint."""
    return JSONResponse({
        "status": "online",
        "service": "Fraud Detection API",
        "version": "2.0.0",
        "endpoints": {
            "GET /api/metrics": "Executive dashboard summary statistics",
            "GET /api/transactions": "List transactions (filters: risk, status, limit)",
            "GET /api/transactions/{id}": "Details and explainability for a transaction",
            "POST /api/score": "Score new transaction & persist to case database",
            "POST /api/cases/{id}/review": "Record analyst review decision",
            "POST /api/cases/{id}/action": "Simulate card block or SMS notification",
            "GET /api/reviews": "List analyst review decisions audit trail",
        },
    })


async def metrics_endpoint(request: Request) -> JSONResponse:
    """Return live aggregate metrics."""
    metrics = get_summary_metrics()
    return JSONResponse(metrics)


async def transactions_endpoint(request: Request) -> JSONResponse:
    """Fetch transactions with optional filtering."""
    risk = request.query_params.get("risk")
    status = request.query_params.get("status")

    risk_filter = [risk] if risk else None
    status_filter = [status] if status else None

    df = get_all_transactions(risk_filter=risk_filter, status_filter=status_filter)
    limit = int(request.query_params.get("limit", 100))
    records = df.head(limit).to_dict(orient="records")

    return JSONResponse({
        "total_returned": len(records),
        "data": records,
    })


async def transaction_detail(request: Request) -> JSONResponse:
    """Fetch a single transaction by ID."""
    tx_id_str = request.path_params.get("id")
    try:
        tx_id = int(tx_id_str)
    except (ValueError, TypeError):
        return JSONResponse({"error": "Invalid transaction ID"}, status_code=400)

    data = get_transaction_by_id(tx_id)
    if not data:
        return JSONResponse({"error": "Transaction not found"}, status_code=404)
    return JSONResponse(data)


async def score_endpoint(request: Request) -> JSONResponse:
    """Score a new transaction in real-time and store in the database."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    amount = float(body.get("amount", 100.0))
    card_type = str(body.get("card_type", "Visa Debit"))
    category = str(body.get("product_category", "E-Commerce (W)"))
    device = str(body.get("device", "Windows Chrome"))

    scored = score_transaction(
        amount=amount,
        card_type=card_type,
        category=category,
        device=device,
    )

    # Persist directly into SQLite
    tx_id = insert_transaction(scored)
    scored["transaction_id"] = tx_id

    return JSONResponse(scored, status_code=201)


async def review_endpoint(request: Request) -> JSONResponse:
    """Submit an analyst review decision."""
    tx_id_str = request.path_params.get("id")
    try:
        tx_id = int(tx_id_str)
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid payload or ID"}, status_code=400)

    analyst_name = body.get("analyst_name", "Lead Analyst")
    decision = body.get("decision", "Confirmed Fraud")
    notes = body.get("notes", "")
    action_taken = body.get("action_taken", "None")

    success = submit_review(
        tx_id=tx_id,
        analyst_name=analyst_name,
        decision=decision,
        notes=notes,
        action_taken=action_taken,
    )

    return JSONResponse({
        "success": success,
        "message": f"Case #{tx_id} successfully updated with decision '{decision}'",
    })


async def action_endpoint(request: Request) -> JSONResponse:
    """Execute simulated security action (block card / SMS alert)."""
    tx_id_str = request.path_params.get("id")
    try:
        tx_id = int(tx_id_str)
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid payload or ID"}, status_code=400)

    action = body.get("action", "Block Card")
    details = body.get("details", "Triggered via API")

    record_action(tx_id, action, details)

    return JSONResponse({
        "success": True,
        "transaction_id": tx_id,
        "action": action,
        "message": f"Action '{action}' simulated successfully for transaction #{tx_id}",
    })


async def reviews_history_endpoint(request: Request) -> JSONResponse:
    """Return historical decisions made by fraud analysts."""
    df = get_review_history()
    return JSONResponse(df.to_dict(orient="records"))


routes = [
    Route("/", root, methods=["GET"]),
    Route("/api/metrics", metrics_endpoint, methods=["GET"]),
    Route("/api/transactions", transactions_endpoint, methods=["GET"]),
    Route("/api/transactions/{id:int}", transaction_detail, methods=["GET"]),
    Route("/api/score", score_endpoint, methods=["POST"]),
    Route("/api/cases/{id:int}/review", review_endpoint, methods=["POST"]),
    Route("/api/cases/{id:int}/action", action_endpoint, methods=["POST"]),
    Route("/api/reviews", reviews_history_endpoint, methods=["GET"]),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = Starlette(debug=True, routes=routes, middleware=middleware)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.server:app", host="127.0.0.1", port=8000, reload=True)
