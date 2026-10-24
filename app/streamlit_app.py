"""
Fraud Detection Case Management Dashboard.
Enterprise-grade Streamlit application for fraud analysts and risk teams.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

# Ensure root directory is accessible
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.database import (
    get_all_transactions,
    get_audit_log,
    get_review_history,
    get_summary_metrics,
    get_transaction_by_id,
    init_db,
    insert_transaction,
    record_action,
    submit_review,
)
from src.explainability import get_feature_importances
from src.predictor import score_transaction

# Streamlit page setup
st.set_page_config(
    page_title="FraudShield | Case Management Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #64748b;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
    }
    .high-risk-badge {
        color: #dc2626;
        font-weight: 700;
    }
    .med-risk-badge {
        color: #d97706;
        font-weight: 600;
    }
    .low-risk-badge {
        color: #16a34a;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Ensure database is initialized
init_db()

# Top Header
st.markdown('<div class="main-title">🛡️ FraudShield Case Management Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Real-Time Financial Transaction Surveillance & Explainable AI Case Triage</div>',
    unsafe_allow_html=True,
)

# Navigation Tabs
tab_overview, tab_cases, tab_simulator, tab_model, tab_audit = st.tabs([
    "📊 Executive Overview",
    "🔍 Case Review & Triage",
    "⚡ Real-Time Simulator",
    "🧠 Model Performance & Explainability",
    "📜 Audit Log & Feedback",
])

# ==========================================
# TAB 1: EXECUTIVE OVERVIEW
# ==========================================
with tab_overview:
    metrics = get_summary_metrics()

    # Top KPI Metrics Row
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Transactions", f"{metrics['total_count']:,}")
    k2.metric("High-Risk Flagged", f"{metrics['high_risk_count']:,}", delta=f"{metrics['high_risk_count']} cases", delta_color="inverse")
    k3.metric("Total Volume", f"${metrics['total_volume']:,.2f}")
    k4.metric("High-Risk Volume", f"${metrics['high_risk_volume']:,.2f}")
    k5.metric("Avg Fraud Probability", f"{metrics['avg_probability']:.1%}")

    st.divider()

    df_all = get_all_transactions()

    if not df_all.empty:
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("##### 📌 Risk Level Breakdown")
            risk_counts = df_all["risk_level"].value_counts().reset_index()
            risk_counts.columns = ["Risk Level", "Count"]
            color_map = {
                "High Risk": "#ef4444",
                "Medium Risk": "#f59e0b",
                "Low Risk": "#10b981",
            }
            fig_risk = px.pie(
                risk_counts,
                values="Count",
                names="Risk Level",
                color="Risk Level",
                color_discrete_map=color_map,
                hole=0.45,
            )
            fig_risk.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
            st.plotly_chart(fig_risk, use_container_width=True)

        with c2:
            st.markdown("##### 💳 Transactions by Merchant Category")
            cat_counts = df_all["product_category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Transactions"]
            fig_cat = px.bar(
                cat_counts,
                x="Transactions",
                y="Category",
                orientation="h",
                color="Transactions",
                color_continuous_scale="Blues",
            )
            fig_cat.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300, showlegend=False)
            st.plotly_chart(fig_cat, use_container_width=True)

        st.markdown("##### 📈 Transaction Amount vs. Fraud Probability")
        fig_scatter = px.scatter(
            df_all,
            x="amount",
            y="fraud_probability",
            color="risk_level",
            color_discrete_map=color_map,
            hover_data=["transaction_id", "card_type", "product_category", "device"],
            labels={"amount": "Amount ($)", "fraud_probability": "Fraud Probability Score"},
        )
        fig_scatter.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320)
        st.plotly_chart(fig_scatter, use_container_width=True)

# ==========================================
# TAB 2: CASE REVIEW & TRIAGE
# ==========================================
with tab_cases:
    st.markdown("### 🔍 Case Review & Investigation Workbench")

    col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 2])

    with col_filter1:
        risk_filter = st.multiselect(
            "Filter by Risk Level",
            options=["High Risk", "Medium Risk", "Low Risk"],
            default=["High Risk", "Medium Risk"],
        )

    with col_filter2:
        status_options = ["Pending Review", "Under Investigation", "Confirmed Fraud", "False Positive / Cleared", "Auto-Approved"]
        status_filter = st.multiselect(
            "Filter by Case Status",
            options=status_options,
            default=["Pending Review", "Under Investigation"],
        )

    with col_filter3:
        search_query = st.text_input("🔎 Search Transaction ID", placeholder="e.g. 3456128")

    search_id = int(search_query.strip()) if search_query.strip().isdigit() else None

    cases_df = get_all_transactions(
        risk_filter=risk_filter if risk_filter else None,
        status_filter=status_filter if status_filter else None,
        search_id=search_id,
    )

    st.write(f"Showing **{len(cases_df)}** cases matching criteria:")

    st.dataframe(
        cases_df[[
            "transaction_id", "amount", "card_type", "product_category",
            "fraud_probability", "risk_level", "status", "timestamp"
        ]],
        use_container_width=True,
        height=220,
    )

    st.divider()

    # Case Details Inspector
    if not cases_df.empty:
        available_ids = cases_df["transaction_id"].tolist()
        selected_tx = st.selectbox("🎯 Select Transaction ID to Investigate:", options=available_ids)

        case = get_transaction_by_id(selected_tx)

        if case:
            left_col, center_col, right_col = st.columns([3, 3, 3])

            with left_col:
                st.markdown("##### 📄 Transaction Profile")
                st.write(f"**Transaction ID:** `{case['transaction_id']}`")
                st.write(f"**Amount:** `${case['amount']:,.2f}`")
                st.write(f"**Payment Instrument:** {case['card_type']}")
                st.write(f"**Category:** {case['product_category']}")
                st.write(f"**Device Fingerprint:** {case['device']}")
                st.write(f"**Timestamp:** {case['timestamp']}")
                st.write(f"**Current Status:** `{case['status']}`")

            with center_col:
                st.markdown("##### 🎯 Fraud Risk Score")
                prob = float(case["fraud_probability"])
                fig_gauge = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=prob * 100,
                        number={"suffix": "%", "valueformat": ".1f"},
                        title={"text": f"Risk: {case['risk_level']}", "font": {"size": 16}},
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": "#ef4444" if prob > 0.7 else "#f59e0b" if prob > 0.35 else "#10b981"},
                            "steps": [
                                {"range": [0, 35], "color": "#dcfce7"},
                                {"range": [35, 70], "color": "#fef3c7"},
                                {"range": [70, 100], "color": "#fee2e2"},
                            ],
                            "threshold": {
                                "line": {"color": "black", "width": 3},
                                "thickness": 0.75,
                                "value": 70,
                            },
                        },
                    )
                )
                fig_gauge.update_layout(height=240, margin=dict(l=15, r=15, t=30, b=15))
                st.plotly_chart(fig_gauge, use_container_width=True)

            with right_col:
                st.markdown("##### 💡 Explainable AI Analysis")
                st.info(case["explanation"])

            st.markdown("#### ⚖️ Analyst Decision & Action Workbench")
            w1, w2, w3 = st.columns([2, 3, 2])

            with w1:
                analyst_name = st.text_input("Analyst Name", value="Security Analyst")
                decision = st.selectbox(
                    "Decision",
                    ["Confirmed Fraud", "Genuine / False Positive", "Escalate for Audit", "Need More Info"],
                )

            with w2:
                notes = st.text_area("Investigation Notes", placeholder="Reason for determination...")

            with w3:
                st.markdown("##### Quick Actions")
                action_taken = "None"
                if st.button("📱 Send SMS Alert", use_container_width=True):
                    record_action(selected_tx, "SMS Alert", "Security verification SMS sent to cardholder.")
                    st.toast("✅ SMS alert dispatched to cardholder.")
                    action_taken = "SMS Alert Sent"

                if st.button("🚨 Block Payment Card", type="primary", use_container_width=True):
                    record_action(selected_tx, "Card Blocked", "Card placed on immediate administrative lock.")
                    st.toast("🚨 Card status updated to BLOCKED.")
                    action_taken = "Card Blocked"

                if st.button("💾 Submit & Finalize Case", use_container_width=True):
                    submit_review(
                        tx_id=selected_tx,
                        analyst_name=analyst_name,
                        decision=decision,
                        notes=notes,
                        action_taken=action_taken,
                    )
                    st.success(f"Case #{selected_tx} saved with decision: {decision}")
                    st.rerun()

# ==========================================
# TAB 3: REAL-TIME SIMULATOR
# ==========================================
with tab_simulator:
    st.markdown("### ⚡ Live Transaction Risk Scoring Simulator")
    st.write("Score incoming payments instantaneously using the trained multi-feature fraud engine.")

    with st.form("simulator_form"):
        sim_c1, sim_c2 = st.columns(2)

        with sim_c1:
            sim_amount = st.number_input("Transaction Amount ($)", min_value=1.0, max_value=50000.0, value=1240.0, step=50.0)
            sim_card = st.selectbox(
                "Payment Instrument",
                ["Visa Debit", "Mastercard Credit", "Amex Corporate", "Discover Prepaid"],
            )

        with sim_c2:
            sim_category = st.selectbox(
                "Merchant Category",
                ["E-Commerce (W)", "Retail Checkout (C)", "Subscription (R)", "Hotel/Travel (H)", "Software (S)"],
            )
            sim_device = st.selectbox(
                "Client Device",
                ["Windows Chrome", "iOS Safari", "Android App", "MacOS Safari", "Linux Firefox"],
            )

        submitted = st.form_submit_button("🚀 Run Live Fraud Assessment", type="primary")

    if submitted:
        score_res = score_transaction(
            amount=sim_amount,
            card_type=sim_card,
            category=sim_category,
            device=sim_device,
        )

        res_c1, res_c2, res_c3 = st.columns(3)
        res_c1.metric("Predicted Fraud Risk", score_res["risk_level"])
        res_c2.metric("Fraud Probability", f"{score_res['fraud_probability']:.2%}")
        res_c3.metric("ML Decision", "FRAUD DETECTED" if score_res["predicted_fraud"] == 1 else "APPROVED")

        st.markdown("##### 🔍 Why was this scored this way?")
        st.info(score_res["explanation"])

        if st.button("📥 Save Simulated Case to Database"):
            new_id = insert_transaction(score_res)
            st.success(f"Transaction successfully saved to database with ID #{new_id}!")

# ==========================================
# TAB 4: MODEL PERFORMANCE & EXPLAINABILITY
# ==========================================
with tab_model:
    st.markdown("### 🧠 Model Performance & Feature Explainability")

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Model ROC-AUC", "89.90%")
    p2.metric("Precision", "71.00%")
    p3.metric("Recall", "75.00%")
    p4.metric("F1-Score", "73.00%")

    st.divider()

    m_left, m_right = st.columns(2)

    with m_left:
        st.markdown("##### 📊 Global Feature Importances (SHAP / Tree Weights)")
        fi_dict = get_feature_importances()
        fi_df = pd.DataFrame(list(fi_dict.items()), columns=["Feature", "Importance"]).sort_values("Importance", ascending=True)
        fig_fi = px.bar(fi_df, x="Importance", y="Feature", orientation="h", color="Importance", color_continuous_scale="Purples")
        fig_fi.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=380, showlegend=False)
        st.plotly_chart(fig_fi, use_container_width=True)

    with m_right:
        st.markdown("##### 📈 Model Validation Curves")
        roc_path = ROOT_DIR / "outputs" / "roc_curve.png"
        cm_path = ROOT_DIR / "outputs" / "confusion_matrix.png"

        if roc_path.exists():
            st.image(str(roc_path), caption="Receiver Operating Characteristic (ROC) Curve", use_container_width=True)
        if cm_path.exists():
            st.image(str(cm_path), caption="Validation Confusion Matrix", use_container_width=True)

# ==========================================
# TAB 5: AUDIT LOG & FEEDBACK
# ==========================================
with tab_audit:
    st.markdown("### 📜 Analyst Decisions & Audit History")

    reviews_df = get_review_history()
    if not reviews_df.empty:
        st.dataframe(reviews_df, use_container_width=True)

        csv_data = reviews_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Decisions to CSV",
            data=csv_data,
            file_name="fraud_analyst_decisions.csv",
            mime="text/csv",
        )
    else:
        st.info("No analyst decisions submitted yet. Review cases in the Case Review tab to build history.")

    st.divider()

    st.markdown("##### 🔒 System Security Audit Trail")
    audit_df = get_audit_log(30)
    st.dataframe(audit_df, use_container_width=True)
