from __future__ import annotations

from dataclasses import dataclass

from finrisk_agent.config import AppConfig
from finrisk_agent.llm import LocalLLMClient
from finrisk_agent.planner import AnalysisPlan, make_plan
from finrisk_agent.reporting import render_report
from finrisk_agent.sql_tools import SQLResult, SQLTools


@dataclass
class AgentResponse:
    question: str
    plan: AnalysisPlan
    result: SQLResult
    report: str


class FinRiskAgent:
    def __init__(self, config: AppConfig):
        self.config = config
        self.sql_tools = SQLTools(config.database.path, max_rows=config.agent.max_rows)
        self.llm = LocalLLMClient(config.llm) if config.llm.enabled else None

    def run(self, question: str) -> AgentResponse:
        schema = self.sql_tools.schema_summary()
        plan = make_plan(question, schema, self.llm)
        result = self.sql_tools.execute(plan.sql)
        report = render_report(question, plan, result)
        return AgentResponse(question=question, plan=plan, result=result, report=report)
