from __future__ import annotations

from collections import defaultdict
from typing import Any

from finrisk_agent.planner import AnalysisPlan
from finrisk_agent.sql_tools import SQLResult


TASK_TYPE_LABELS = {
    "risk_rule_mining": "风控规则挖掘",
    "strategy_development": "策略开发",
    "strategy_impact": "策略效果评估",
    "risk_daily_report": "风险日报",
    "delinquency_trend": "逾期趋势分析",
}


def render_report(question: str, plan: AnalysisPlan, result: SQLResult) -> str:
    lines = [
        f"# {plan.title}",
        "",
        f"**用户问题**：{question}",
        "",
        f"**任务类型**：{TASK_TYPE_LABELS.get(plan.task_type, plan.task_type)}",
        f"**分析口径**：{plan.explanation}",
        "",
        "## 核心发现",
    ]

    if not result.rows:
        lines.append("- 未查询到符合条件的数据，请检查时间窗口或筛选条件。")
        return "\n".join(lines)

    if plan.task_type == "risk_rule_mining":
        lines.extend(_rule_mining_findings(result.rows))
    elif plan.task_type == "strategy_development":
        lines.extend(_strategy_findings(result.rows))
    else:
        lines.extend(_findings(plan, result.rows))
    lines.extend(
        [
            "",
            "## 建议动作",
            *_recommendations(plan.task_type),
            "",
            "## 演示说明",
            "本报告基于合成数据生成，仅用于展示封闭环境金融数据分析智能体的工作流。",
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


def _rule_mining_findings(rows: list[dict[str, Any]]) -> list[str]:
    top = sorted(rows, key=lambda row: (row.get("risk_lift") or 0, row.get("mob3_m1_rate") or 0), reverse=True)[0]
    return [
        f"- 本次挖掘返回 {len(rows)} 条候选风控规则，排序依据为风险提升倍数和 MOB3 M1 逾期率。",
        f"- 排名最高的规则为 `{top.get('candidate_rule')}`，风险提升倍数为 `{_format_value(top.get('risk_lift'))}`，MOB3 M1 逾期率为 `{_format_value(top.get('mob3_m1_rate'))}`。",
        f"- 该规则覆盖放款笔数 {top.get('loans')}，MOB3 余额 {_format_value(top.get('mob3_balance'))}，具备进一步策略评估价值。",
        "- 候选规则不直接等同于生产策略，仍需结合样本稳定性、收益、通过率影响和合规要求进行复核。",
    ]


def _strategy_findings(rows: list[dict[str, Any]]) -> list[str]:
    top = sorted(rows, key=lambda row: (row.get("mob3_m1_rate") or 0, row.get("approved_amount_exposure") or 0), reverse=True)[0]
    return [
        f"- 本次生成 {len(rows)} 条候选策略，覆盖准入收紧、额度下调和人工复核等动作。",
        f"- 优先级最高的策略为 `{top.get('rule_id')} {top.get('rule_name')}`，命中申请量 {top.get('hit_applications')}，当前通过率 `{_format_value(top.get('current_approval_rate'))}`。",
        f"- 该策略命中样本的 MOB3 M1 逾期率为 `{_format_value(top.get('mob3_m1_rate'))}`，已批核敞口为 {_format_value(top.get('approved_amount_exposure'))}。",
        f"- 建议动作：{top.get('suggested_action')}。上线前应做拒绝推断、收益测算和 A/B 或灰度验证。",
    ]


def _recommendations(task_type: str) -> list[str]:
    if task_type == "risk_rule_mining":
        return [
            "- 将风险提升倍数高且样本量充足的规则进入策略沙盘，评估拒绝率、风险下降和收入损失。",
            "- 对规则命中的渠道、风险等级和产品组合做稳定性回看，避免单月噪声驱动策略。",
            "- 将候选规则转化为可审计条件，补充例外策略和人工复核路径。",
        ]
    if task_type == "strategy_development":
        return [
            "- 优先对高逾期、高敞口策略进行离线回测，比较风险下降与通过率损失。",
            "- 对额度下调类策略单独评估收益影响，避免只降低风险但损害优质客群体验。",
            "- 上线前设置灰度实验、监控阈值和回滚条件，形成策略生命周期闭环。",
        ]
    return [
        "- 对高 M1/M2 风险且余额占比较高的客群进行准入、额度或定价复核。",
        "- 将渠道、风险等级、产品类型作为优先监控维度，建立周度异常波动看板。",
        "- 对策略调整前后的通过率、资产质量和净收入进行联合评估，避免单指标优化。",
    ]


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
    dims = ["apply_month", "period", "channel", "risk_grade", "product_type", "city_tier", "income_band"]
    values = [f"{dim}={row[dim]}" for dim in dims if dim in row]
    return "、".join(values) if values else "整体"


def _format_value(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.2%}" if abs(value) <= 1 else f"{value:,.2f}"
    return str(value)
