# Demo Walkthrough

This walkthrough is written for reviewers who want to understand the demo without reading the code first.

## 1. What To Look For

The demo is not a generic chatbot. It is a constrained financial data analysis agent:

- It works on a local synthetic credit database.
- It converts natural language questions into structured analysis plans.
- It validates SQL before execution.
- It produces risk analysis reports with explicit metrics and segments.
- It can run in a closed environment with a local Chinese open-weight model, or in fallback mode without a model.

## 2. Start The Demo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_demo_data.py
streamlit run app.py
```

Open the Streamlit URL and choose one of the preset questions.

## 3. Suggested Review Flow

### Scenario A: Delinquency Trend

Question:

```text
分析近6个月M1/M2逾期率变化，并定位主要风险上升客群
```

Expected behavior:

- The agent builds a MOB3 delinquency analysis.
- It groups by month, channel, risk grade, and product type.
- It reports the highest-risk segment and whether the trend rises or falls.

### Scenario B: Strategy Impact

Question:

```text
评估2025年7月额度策略调整前后的通过率、M1逾期率和收益变化
```

Expected behavior:

- The agent compares the period before and after the July 2025 policy event.
- It avoids duplicated application counts by aggregating at application level before period-level aggregation.
- It reports approval rate, booking rate, MOB3 M1 rate, balance, and net income.

### Scenario C: Risk Daily Report

Question:

```text
生成最近一个月风险日报，说明核心指标、异常波动和建议动作
```

Expected behavior:

- The agent produces a current-month risk summary.
- It applies a minimum sample-size filter to avoid over-interpreting tiny groups.
- It identifies the top risk segment and provides monitoring suggestions.

## 4. Closed-Environment Controls

The demo includes these controls to mimic a private financial analytics environment:

| Control | Implementation |
| --- | --- |
| Local data only | `scripts/generate_demo_data.py` creates `data/finrisk_demo.sqlite` |
| Read-only SQL | `finrisk_agent/sql_tools.py` blocks mutation statements |
| Table whitelist | Schema is limited to synthetic demo tables |
| Local LLM endpoint | `finrisk_agent/llm.py` calls an OpenAI-compatible local endpoint |
| Fallback mode | `finrisk_agent/planner.py` contains deterministic templates |

## 5. What Is Intentionally Out Of Scope

- No real customer data
- No real underwriting strategy
- No production credit decisioning
- No regulatory advice
- No online search or external data dependency during analysis
