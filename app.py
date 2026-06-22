from __future__ import annotations

import pandas as pd
import streamlit as st

from finrisk_agent.agent import FinRiskAgent
from finrisk_agent.config import load_config


st.set_page_config(page_title="FinRisk Agent CN Demo", layout="wide")
st.title("FinRisk Agent CN Demo")
st.caption("公开展示用 demo：合成数据、本地模型接口、封闭环境金融风险分析工作流。")

question = st.text_area(
    "分析问题",
    value="分析近6个月M1/M2逾期率变化，并定位主要风险上升客群",
    height=90,
)

if st.button("运行分析", type="primary"):
    with st.spinner("Agent 正在规划、执行 SQL 并生成报告..."):
        response = FinRiskAgent(load_config()).run(question)

    st.subheader("分析报告")
    st.markdown(response.report)

    with st.expander("生成的 SQL"):
        st.code(response.plan.sql.strip(), language="sql")

    st.subheader("查询结果")
    st.dataframe(pd.DataFrame(response.result.rows), use_container_width=True)
