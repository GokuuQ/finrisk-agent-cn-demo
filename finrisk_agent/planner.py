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


SYSTEM_PROMPT = """你是金融风控数据分析规划器。
只能返回严格 JSON，不要包含 Markdown。
数据库是本地合成演示数据。只能生成只读 SELECT SQL。
必需 JSON 字段：task_type, title, sql, dimensions, metrics, explanation。
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
    if "规则" in question or "挖掘" in question:
        return AnalysisPlan(
            task_type="risk_rule_mining",
            title="风控规则挖掘与高风险客群发现",
            sql="""
WITH base AS (
  SELECT
    a.app_id,
    a.channel,
    a.product_type,
    c.risk_grade,
    c.city_tier,
    c.income_band,
    a.approved,
    CASE WHEN l.loan_id IS NOT NULL THEN 1 ELSE 0 END AS booked,
    MAX(CASE WHEN mp.mob = 3 THEN mp.m1_flag END) AS mob3_m1_flag,
    MAX(CASE WHEN mp.mob = 3 THEN mp.m2_flag END) AS mob3_m2_flag,
    SUM(CASE WHEN mp.mob = 3 THEN mp.balance ELSE 0 END) AS mob3_balance
  FROM applications a
  JOIN customers c ON a.customer_id = c.customer_id
  LEFT JOIN loans l ON a.app_id = l.app_id
  LEFT JOIN monthly_performance mp ON l.loan_id = mp.loan_id
  WHERE a.apply_date BETWEEN '2025-06-01' AND '2025-11-30'
  GROUP BY a.app_id, a.channel, a.product_type, c.risk_grade, c.city_tier, c.income_band, a.approved, booked
),
overall AS (
  SELECT AVG(mob3_m1_flag) AS overall_m1_rate
  FROM base
  WHERE booked = 1
),
segments AS (
  SELECT
    '渠道=' || channel || ' 且 风险等级=' || risk_grade ||
      ' 且 产品=' || product_type ||
      ' 且 城市等级=' || city_tier ||
      ' 且 收入带=' || income_band AS candidate_rule,
    channel,
    risk_grade,
    product_type,
    city_tier,
    income_band,
    COUNT(*) AS applications,
    SUM(booked) AS loans,
    ROUND(AVG(approved), 4) AS approval_rate,
    ROUND(AVG(booked), 4) AS booking_rate,
    ROUND(AVG(mob3_m1_flag), 4) AS mob3_m1_rate,
    ROUND(AVG(mob3_m2_flag), 4) AS mob3_m2_rate,
    ROUND(SUM(mob3_balance), 2) AS mob3_balance,
    ROUND(AVG(mob3_m1_flag) / NULLIF((SELECT overall_m1_rate FROM overall), 0), 2) AS risk_lift
  FROM base
  WHERE booked = 1
  GROUP BY channel, risk_grade, product_type, city_tier, income_band
)
SELECT
  candidate_rule,
  channel,
  risk_grade,
  product_type,
  city_tier,
  income_band,
  applications,
  loans,
  approval_rate,
  booking_rate,
  mob3_m1_rate,
  mob3_m2_rate,
  mob3_balance,
  risk_lift
FROM segments
WHERE loans >= 25
ORDER BY risk_lift DESC, mob3_m1_rate DESC, mob3_balance DESC
""",
            dimensions=["channel", "risk_grade", "product_type", "city_tier", "income_band"],
            metrics=["risk_lift", "mob3_m1_rate", "mob3_m2_rate", "mob3_balance"],
            explanation="按渠道、风险等级、产品、城市等级和收入带挖掘高风险分群，并用 M1 风险提升倍数衡量规则价值。",
        )

    if "策略开发" in question or "准入策略" in question or "额度策略" in question:
        return AnalysisPlan(
            task_type="strategy_development",
            title="准入与额度策略候选方案开发",
            sql="""
WITH base AS (
  SELECT
    a.app_id,
    a.channel,
    a.product_type,
    c.risk_grade,
    c.city_tier,
    c.income_band,
    a.requested_amount,
    a.approved,
    a.approved_amount,
    CASE WHEN l.loan_id IS NOT NULL THEN 1 ELSE 0 END AS booked,
    MAX(CASE WHEN mp.mob = 3 THEN mp.m1_flag END) AS mob3_m1_flag,
    MAX(CASE WHEN mp.mob = 3 THEN mp.m2_flag END) AS mob3_m2_flag,
    SUM(CASE WHEN mp.mob = 3 THEN mp.balance ELSE 0 END) AS mob3_balance,
    SUM(CASE WHEN mp.mob = 3 THEN mp.interest_income - mp.credit_loss ELSE 0 END) AS mob3_net_income
  FROM applications a
  JOIN customers c ON a.customer_id = c.customer_id
  LEFT JOIN loans l ON a.app_id = l.app_id
  LEFT JOIN monthly_performance mp ON l.loan_id = mp.loan_id
  WHERE a.apply_date BETWEEN '2025-06-01' AND '2025-11-30'
  GROUP BY a.app_id, a.channel, a.product_type, c.risk_grade, c.city_tier, c.income_band,
           a.requested_amount, a.approved, a.approved_amount, booked
),
rules AS (
  SELECT
    'R001' AS rule_id,
    '高风险渠道D/E收紧准入' AS rule_name,
    'channel IN (partner, ad_network) AND risk_grade IN (D, E)' AS rule_condition,
    '拒绝或转人工复核' AS suggested_action,
    *
  FROM base
  WHERE channel IN ('partner', 'ad_network') AND risk_grade IN ('D', 'E')
  UNION ALL
  SELECT
    'R002',
    '大额低收入客群额度下调',
    'income_band=low AND requested_amount>=20000',
    '额度上限下调至12000',
    *
  FROM base
  WHERE income_band = 'low' AND requested_amount >= 20000
  UNION ALL
  SELECT
    'R003',
    '广告渠道分期产品复核',
    'channel=ad_network AND product_type=installment',
    '增加二次校验或降低通过阈值',
    *
  FROM base
  WHERE channel = 'ad_network' AND product_type = 'installment'
)
SELECT
  rule_id,
  rule_name,
  rule_condition,
  suggested_action,
  COUNT(*) AS hit_applications,
  SUM(approved) AS current_approved,
  SUM(booked) AS current_loans,
  ROUND(AVG(approved), 4) AS current_approval_rate,
  ROUND(AVG(booked), 4) AS current_booking_rate,
  ROUND(AVG(mob3_m1_flag), 4) AS mob3_m1_rate,
  ROUND(AVG(mob3_m2_flag), 4) AS mob3_m2_rate,
  ROUND(SUM(mob3_balance), 2) AS mob3_balance,
  ROUND(SUM(mob3_net_income), 2) AS mob3_net_income,
  ROUND(SUM(CASE WHEN approved = 1 THEN approved_amount ELSE 0 END), 2) AS approved_amount_exposure
FROM rules
GROUP BY rule_id, rule_name, rule_condition, suggested_action
HAVING hit_applications >= 50
ORDER BY mob3_m1_rate DESC, approved_amount_exposure DESC
""",
            dimensions=["rule_id", "rule_name", "rule_condition", "suggested_action"],
            metrics=["mob3_m1_rate", "mob3_m2_rate", "approved_amount_exposure", "mob3_net_income"],
            explanation="基于规则命中样本、当前通过率、MOB3 逾期表现和敞口，生成可讨论的准入与额度策略候选方案。",
        )

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
            explanation="对比 2025 年 7 月额度策略事件前后的申请、通过、放款、MOB3 逾期和净收入表现。",
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
            explanation="汇总最近月份获客质量和早期逾期信号。",
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
        explanation="按获客渠道和风险分群跟踪 MOB3 M1/M2 逾期趋势。",
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
