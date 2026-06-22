from __future__ import annotations

import pandas as pd
import streamlit as st

from finrisk_agent.agent import FinRiskAgent
from finrisk_agent.config import load_config


st.set_page_config(page_title="FinRisk Agent CN Demo", layout="wide")
st.title("FinRisk Agent CN Demo")
st.caption("Public demo: synthetic data, local model endpoint, controlled SQL execution, and closed-environment risk analysis workflow.")

PRESET_QUESTIONS = [
    "分析近6个月M1/M2逾期率变化，并定位主要风险上升客群",
    "评估2025年7月额度策略调整前后的通过率、M1逾期率和收益变化",
    "生成最近一个月风险日报，说明核心指标、异常波动和建议动作",
    "对比不同渠道和风险等级的资产质量表现",
]

with st.sidebar:
    st.header("Demo Guide")
    st.markdown(
        """
        This demo runs on synthetic consumer-credit data.

        1. Choose a preset question.
        2. Run the agent.
        3. Review the generated SQL, result table, and risk report.

        No real customer data is included.
        """
    )
    selected_question = st.radio("Preset questions", PRESET_QUESTIONS, index=0)

tab_demo, tab_architecture, tab_data = st.tabs(["Agent Demo", "Architecture", "Synthetic Data"])

question = st.text_area(
    "Analysis question",
    value=selected_question,
    height=90,
)

with tab_demo:
    if st.button("Run Analysis", type="primary"):
        with st.spinner("Agent is planning, validating SQL, executing locally, and rendering the report..."):
            response = FinRiskAgent(load_config()).run(question)

        metric_cols = st.columns(4)
        metric_cols[0].metric("Task Type", response.plan.task_type)
        metric_cols[1].metric("Rows Returned", len(response.result.rows))
        metric_cols[2].metric("Dimensions", len(response.plan.dimensions))
        metric_cols[3].metric("Metrics", len(response.plan.metrics))

        st.subheader("Risk Report")
        st.markdown(response.report)

        with st.expander("Generated SQL", expanded=True):
            st.code(response.plan.sql.strip(), language="sql")

        st.subheader("Query Result")
        st.dataframe(pd.DataFrame(response.result.rows), use_container_width=True)

with tab_architecture:
    st.subheader("Closed-Environment Agent Flow")
    st.markdown(
        """
        The agent uses a local model endpoint when configured, then validates and executes read-only SQL
        against a local SQLite database. The default fallback planner keeps the demo runnable even when no
        model service is available.
        """
    )
    st.code(
        """
User question
  -> Planner: local LLM JSON plan or fallback template
  -> SQL guardrail: read-only validation
  -> Local SQLite execution
  -> Metric rendering and report generation
        """.strip(),
        language="text",
    )

with tab_data:
    st.subheader("Synthetic Credit Data")
    st.markdown(
        """
        The demo database is generated locally and contains five synthetic tables:

        - `customers`: customer profile and risk grade
        - `applications`: credit applications and approval outcomes
        - `loans`: booked loans and contract information
        - `monthly_performance`: MOB-level balance, M1/M2 flags, income and loss
        - `strategy_events`: policy event metadata
        """
    )
