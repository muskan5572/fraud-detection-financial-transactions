
import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(
    page_title="Fraud Detection Case Management",
    layout="wide"
)

st.title("Fraud Detection Case Management Dashboard")

DATA_PATH = "data/sample_fraud_predictions.csv"
FEEDBACK_PATH = "outputs/analyst_feedback.csv"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

data = load_data()

st.sidebar.header("Filters")

risk_filter = st.sidebar.multiselect(
    "Risk Level",
    options=data["risk_level"].unique(),
    default=list(data["risk_level"].unique())
)

filtered_data = data[data["risk_level"].isin(risk_filter)]

st.subheader("Transaction Overview")

col1, col2, col3 = st.columns(3)

col1.metric("Total Transactions", len(filtered_data))
col2.metric("High Risk Cases", len(filtered_data[filtered_data["risk_level"] == "High Risk"]))
col3.metric("Average Fraud Probability", round(filtered_data["fraud_probability"].mean(), 3))

st.dataframe(filtered_data, use_container_width=True)

st.subheader("Case Review")

transaction_ids = filtered_data["TransactionID"].tolist()

selected_transaction = st.selectbox(
    "Select Transaction ID",
    transaction_ids
)

case = filtered_data[filtered_data["TransactionID"] == selected_transaction].iloc[0]

left, right = st.columns(2)

with left:
    st.write("Transaction ID:", case["TransactionID"])
    st.write("Fraud Probability:", round(case["fraud_probability"], 4))
    st.write("Risk Level:", case["risk_level"])
    st.write("Predicted Fraud:", case["predicted_fraud"])
    st.write("Actual Fraud:", case["actual_fraud"])

with right:
    st.write("Explainable AI Reasoning:")
    st.info(case["explanation"])

analyst_decision = st.radio(
    "Analyst Decision",
    ["Fraud", "Genuine", "Needs Review"]
)

notes = st.text_area("Analyst Notes")

if st.button("Submit Analyst Decision"):
    feedback = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "TransactionID": case["TransactionID"],
        "fraud_probability": case["fraud_probability"],
        "risk_level": case["risk_level"],
        "analyst_decision": analyst_decision,
        "notes": notes
    }])

    os.makedirs("outputs", exist_ok=True)

    if os.path.exists(FEEDBACK_PATH):
        old_feedback = pd.read_csv(FEEDBACK_PATH)
        feedback = pd.concat([old_feedback, feedback], ignore_index=True)

    feedback.to_csv(FEEDBACK_PATH, index=False)
    st.success("Analyst feedback saved successfully.")

st.subheader("Customer Communication")

c1, c2 = st.columns(2)

with c1:
    if st.button("Send SMS Alert"):
        st.warning("SMS alert sent to customer. Simulation only.")

with c2:
    if st.button("Block Card"):
        st.error("Card blocked successfully. Simulation only.")

st.subheader("Feedback History")

if os.path.exists(FEEDBACK_PATH):
    feedback_history = pd.read_csv(FEEDBACK_PATH)
    st.dataframe(feedback_history, use_container_width=True)
else:
    st.write("No analyst feedback submitted yet.")
