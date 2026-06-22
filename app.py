from __future__ import annotations

import pandas as pd
import streamlit as st

from finrisk_agent.agent import FinRiskAgent
from finrisk_agent.config import load_config
from finrisk_agent.reporting import TASK_TYPE_LABELS


st.set_page_config(page_title="消费金融风控分析智能体演示项目", layout="wide")
st.title("消费金融风控分析智能体演示项目")
st.caption("公开演示项目：合成数据、本地模型接口、受控 SQL 执行、风控规则挖掘与策略开发闭环。")

PRESET_QUESTIONS = [
    "分析近6个月M1/M2逾期率变化，并定位主要风险上升客群",
    "挖掘高风险风控规则，按风险提升倍数排序并给出候选规则",
    "基于近期表现开发准入与额度策略候选方案，输出命中量、风险和建议动作",
    "评估2025年7月额度策略调整前后的通过率、M1逾期率和收益变化",
    "生成最近一个月风险日报，说明核心指标、异常波动和建议动作",
]

with st.sidebar:
    st.header("演示导航")
    st.markdown(
        """
        本演示项目使用合成消费金融数据，不包含任何真实客户信息。

        1. 选择一个预设问题。
        2. 点击运行分析。
        3. 查看分析报告、生成 SQL 和结果明细。

        默认模式不依赖外部模型服务；如配置本地大模型，会优先调用本地兼容 OpenAI 的接口。
        """
    )
    selected_question = st.radio("预设问题", PRESET_QUESTIONS, index=0)

tab_demo, tab_flow, tab_data = st.tabs(["功能演示", "执行链路", "合成数据"])

question = st.text_area(
    "分析问题",
    value=selected_question,
    height=90,
)

with tab_demo:
    if st.button("运行分析", type="primary"):
        with st.spinner("智能体正在规划任务、校验 SQL、执行本地查询并生成报告..."):
            response = FinRiskAgent(load_config()).run(question)

        metric_cols = st.columns(4)
        metric_cols[0].metric("任务类型", TASK_TYPE_LABELS.get(response.plan.task_type, response.plan.task_type))
        metric_cols[1].metric("返回行数", len(response.result.rows))
        metric_cols[2].metric("分析维度", len(response.plan.dimensions))
        metric_cols[3].metric("核心指标", len(response.plan.metrics))

        st.subheader("分析报告")
        st.markdown(response.report)

        with st.expander("生成 SQL", expanded=True):
            st.code(response.plan.sql.strip(), language="sql")

        st.subheader("查询结果")
        st.dataframe(pd.DataFrame(response.result.rows), use_container_width=True)

with tab_flow:
    st.subheader("封闭环境执行链路")
    st.markdown(
        """
        智能体在本地完成任务规划、SQL 安全校验、数据库查询、指标整理和报告生成。
        当配置了本地国产开源模型时，规划步骤可由模型完成；没有模型时，内置模板仍可跑通完整演示。
        """
    )
    st.code(
        """
用户问题
  -> 任务规划：本地大模型 JSON 计划或内置模板
  -> SQL 安全校验：只允许 SELECT，只访问合成演示表
  -> 本地 SQLite 执行
  -> 指标整理：风险分群、规则风险提升倍数、策略命中量与敞口
  -> 报告生成：核心发现、候选规则、策略建议
        """.strip(),
        language="text",
    )

with tab_data:
    st.subheader("合成信贷数据")
    st.markdown(
        """
        演示数据库由脚本本地生成，包含五张合成表：

        - `customers`：客户画像、城市等级、风险等级、收入带
        - `applications`：申请时间、渠道、产品、申请金额、审批结果
        - `loans`：放款本金、期限、利率
        - `monthly_performance`：MOB 余额、M1/M2 标记、利息收入、信用损失
        - `strategy_events`：策略事件说明，例如 2025 年 7 月额度策略调整

        数据生成逻辑刻意保留渠道差异、风险等级梯度、额度和收入带差异，用于展示规则挖掘和策略开发方法。
        """
    )
