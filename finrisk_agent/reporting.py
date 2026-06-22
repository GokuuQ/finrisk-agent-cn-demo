from __future__ import annotations

from collections import defaultdict
from typing import Any

from finrisk_agent.planner import AnalysisPlan
from finrisk_agent.sql_tools import SQLResult


def render_report(question: str, plan: AnalysisPlan, result: SQLResult) -> str:
    lines = [
        f"# {plan.title}",
        "",
        f"**用户问题**：{question}",
        "",
        f"**任务类型**：{plan.task_type}",
        f"**分析口径**：{plan.explanation}",
        "",
        "## 核心发现",
    ]

    if not result.rows:
        lines.append("- 未查询到符合条件的数据，请检查时间窗口或筛选条件。")
        return "\n".join(lines)

    lines.extend(_findings(plan, result.rows))
    lines.extend(
        [
            "",
            "## 建议动作",
            "- 对高 M1/M2 风险且余额占比较高的客群进行准入、额度或定价复核。",
            "- 将渠道、风险等级、产品类型作为优先监控维度，建立周度异常波动看板。",
            "- 对策略调整前后的通过率、资产质量和净收入进行联合评估，避免单指标优化。",
            "",
            "## Demo 说明",
            "本报告基于合成数据生成，仅用于展示封闭环境金融数据分析 Agent 的工作流。",
        ]
    )
    return "\n".join(lines)


def _findings(plan: AnalysisPlan, rows: list[dict[str, Any]]) -> list[str]:
    metric = _pick_metric(plan.metrics, rows)
    if not metric:
        return [f"- 查询返回 {len(rows)} 行结果，可进一步查看明细表。"]

    sorted_rows = sorted(rows, key=lambda row: row.get(metric) or 0, reverse=True)
    top = sorted_rows[0]
    group_text = _group_label(top)
    findings = [
        f"- 本次分析返回 {len(rows)} 个分组结果，重点指标为 `{metric}`。",
        f"- 最高风险分组为 {group_text}，`{metric}`={_format_value(top.get(metric))}。",
    ]

    month_key = "apply_month" if "apply_month" in top else None
    if month_key:
        monthly = defaultdict(list)
        for row in rows:
            monthly[row[month_key]].append(row.get(metric) or 0)
        trend = [
            (month, sum(values) / len(values))
            for month, values in sorted(monthly.items())
            if values
        ]
        if len(trend) >= 2:
            start_month, start_value = trend[0]
            end_month, end_value = trend[-1]
            delta = end_value - start_value
            direction = "上升" if delta > 0 else "下降"
            findings.append(
                f"- 从 {start_month} 到 {end_month}，分组平均 `{metric}` {direction} {_format_value(abs(delta))}。"
            )

    if "applications" in top:
        findings.append(
            f"- 该分组申请量为 {top['applications']}，需要结合样本量判断波动是否稳定。"
        )
    elif "loans" in top:
        findings.append(
            f"- 该分组放款笔数为 {top['loans']}，建议优先关注样本量较大且风险升高的分组。"
        )

    return findings


def _pick_metric(metrics: list[str], rows: list[dict[str, Any]]) -> str | None:
    risk_priority = [
        metric
        for metric in metrics
        if ("m1" in metric.lower() or "m2" in metric.lower()) and metric in rows[0]
    ]
    if risk_priority:
        return risk_priority[0]
    for metric in metrics:
        if metric in rows[0]:
            return metric
    for key in rows[0]:
        if key.endswith("_rate") or key.endswith("_income"):
            return key
    return None


def _group_label(row: dict[str, Any]) -> str:
    dims = ["apply_month", "period", "channel", "risk_grade", "product_type"]
    values = [f"{dim}={row[dim]}" for dim in dims if dim in row]
    return "、".join(values) if values else "整体"


def _format_value(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.2%}" if abs(value) <= 1 else f"{value:,.2f}"
    return str(value)
