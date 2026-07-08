import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="GRC Compliance Dashboard",
    layout="wide"
)

st.title("🛡️ GRC Compliance Dashboard")

df = pd.read_csv("data/risk_register.csv")

high_risks = len(df[df["Risk_Level"] == "High"])
open_risks = len(df[df["Status"] == "Open"])
implemented_controls = len(df[df["Control_Status"] == "Implemented"])

col1, col2, col3 = st.columns(3)

col1.metric("High Risks", high_risks)
col2.metric("Open Risks", open_risks)
col3.metric("Implemented Controls", implemented_controls)

st.subheader("Control Status")

control_chart = px.pie(
    df,
    names="Control_Status"
)

st.plotly_chart(control_chart, width="stretch")

st.subheader("Risk Distribution")

risk_chart = px.bar(
    df["Risk_Level"].value_counts()
)

st.plotly_chart(risk_chart, width="stretch")

st.subheader("Risk Register")

st.dataframe(df, width="stretch")