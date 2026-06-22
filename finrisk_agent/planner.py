from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from finrisk_agent.llm import LocalLLMClient


@dataclass(frozen=True)
class AnalysisPlan:
    task_type: str
    title: str
    sql: str
    dimensions: list[str]
    metrics: list[str]
    explanation: str


SYSTEM_PROMPT = """You are a financial risk data analysis planner.
Return strict JSON only. Do not include markdown.
The database is local demo data. You may only generate read-only SELECT SQL.
Required JSON keys: task_type, title, sql, dimensions, metrics, explanation.
"""


def make_plan(question: str, schema: str, llm: LocalLLMClient | None = None) -> AnalysisPlan:
    if llm:
        content = llm.chat(SYSTEM_PROMPT, f"Schema:\n{schema}\n\nQuestion:\n{question}")
        if content:
            parsed = _extract_json(content)
            if parsed:
                return AnalysisPlan(**parsed)

    return fallback_plan(question)


def fallback_plan(question: str) -> AnalysisPlan:
    if "策略" in question or "调整" in question or "收益" in question:
        return AnalysisPlan(
            task_type="strategy_impact",
            title="额度策略调整前后风险收益评估",
            sql="""
SELECT
  base.period,
  COUNT(*) AS applications,
  ROUND(AVG(base.approved), 4) AS approval_rate,
  ROUND(AVG(base.booked), 4) AS booking_rate,
  ROUND(AVG(base.mob3_m1_flag), 4) AS mob3_m1_rate,
  ROUND(SUM(base.mob3_balance), 2) AS mob3_balance,
  ROUND(SUM(base.mob3_net_income), 2) AS mob3_net_income
FROM (
  SELECT
    a.app_id,
    CASE WHEN a.apply_date < '2025-07-01' THEN 'before_policy' ELSE 'after_policy' END AS period,
    a.approved,
    CASE WHEN l.loan_id IS NOT NULL THEN 1 ELSE 0 END AS booked,
    MAX(CASE WHEN mp.mob = 3 THEN mp.m1_flag END) AS mob3_m1_flag,
    SUM(CASE WHEN mp.mob = 3 THEN mp.balance ELSE 0 END) AS mob3_balance,
    SUM(CASE WHEN mp.mob = 3 THEN mp.interest_income - mp.credit_loss ELSE 0 END) AS mob3_net_income
  FROM applications a
  LEFT JOIN loans l ON a.app_id = l.app_id
  LEFT JOIN monthly_performance mp ON l.loan_id = mp.loan_id
  WHERE a.apply_date BETWEEN '2025-04-01' AND '2025-09-30'
  GROUP BY a.app_id, period, a.approved, booked
) base
GROUP BY period
ORDER BY period
""",
            dimensions=["period"],
            metrics=["mob3_m1_rate", "approval_rate", "booking_rate", "mob3_net_income"],
            explanation="Compare applications before and after the July 2025 credit line policy event.",
        )

    if "日报" in question or "最近一个月" in question:
        return AnalysisPlan(
            task_type="risk_daily_report",
            title="最近一个月风险日报",
            sql="""
SELECT
  base.apply_month,
  base.channel,
  base.risk_grade,
  COUNT(*) AS applications,
  ROUND(AVG(base.approved), 4) AS approval_rate,
  ROUND(AVG(base.booked), 4) AS booking_rate,
  ROUND(AVG(base.mob1_m1_flag), 4) AS mob1_m1_rate,
  ROUND(SUM(base.mob1_balance), 2) AS mob1_balance
FROM (
  SELECT
    a.app_id,
    substr(a.apply_date, 1, 7) AS apply_month,
    a.channel,
    c.risk_grade,
    a.approved,
    CASE WHEN l.loan_id IS NOT NULL THEN 1 ELSE 0 END AS booked,
    MAX(CASE WHEN mp.mob = 1 THEN mp.m1_flag END) AS mob1_m1_flag,
    SUM(CASE WHEN mp.mob = 1 THEN mp.balance ELSE 0 END) AS mob1_balance
  FROM applications a
  JOIN customers c ON a.customer_id = c.customer_id
  LEFT JOIN loans l ON a.app_id = l.app_id
  LEFT JOIN monthly_performance mp ON l.loan_id = mp.loan_id
  WHERE a.apply_date BETWEEN '2025-11-01' AND '2025-11-30'
  GROUP BY a.app_id, apply_month, a.channel, c.risk_grade, a.approved, booked
) base
GROUP BY base.apply_month, base.channel, base.risk_grade
HAVING applications >= 30
ORDER BY mob1_m1_rate DESC, applications DESC
""",
            dimensions=["apply_month", "channel", "risk_grade"],
            metrics=["mob1_m1_rate", "approval_rate", "booking_rate", "mob1_balance"],
            explanation="Summarize current-month acquisition quality and early delinquency signals.",
        )

    return AnalysisPlan(
        task_type="delinquency_trend",
        title="近6个月M1/M2逾期率趋势与风险上升客群定位",
        sql="""
SELECT
  substr(a.apply_date, 1, 7) AS apply_month,
  a.channel,
  c.risk_grade,
  a.product_type,
  COUNT(DISTINCT l.loan_id) AS loans,
  ROUND(AVG(CASE WHEN mp.mob = 3 THEN mp.m1_flag END), 4) AS mob3_m1_rate,
  ROUND(AVG(CASE WHEN mp.mob = 3 THEN mp.m2_flag END), 4) AS mob3_m2_rate,
  ROUND(SUM(CASE WHEN mp.mob = 3 THEN mp.balance ELSE 0 END), 2) AS mob3_balance
FROM applications a
JOIN customers c ON a.customer_id = c.customer_id
JOIN loans l ON a.app_id = l.app_id
JOIN monthly_performance mp ON l.loan_id = mp.loan_id
WHERE a.apply_date BETWEEN '2025-06-01' AND '2025-11-30'
GROUP BY apply_month, a.channel, c.risk_grade, a.product_type
HAVING loans >= 20
ORDER BY apply_month, mob3_m1_rate DESC
""",
        dimensions=["apply_month", "channel", "risk_grade", "product_type"],
        metrics=["mob3_m1_rate", "mob3_m2_rate", "mob3_balance"],
        explanation="Track MOB3 M1/M2 delinquency by acquisition and risk segments.",
    )


def _extract_json(content: str) -> dict[str, Any] | None:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?", "", content).strip()
        content = re.sub(r"```$", "", content).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
