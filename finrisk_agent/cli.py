from __future__ import annotations

import argparse
import json

from finrisk_agent.agent import FinRiskAgent
from finrisk_agent.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the FinRisk Agent CN demo.")
    parser.add_argument("question", help="Natural language risk analysis question.")
    parser.add_argument("--config", default="config.yaml", help="Path to config yaml.")
    parser.add_argument("--show-sql", action="store_true", help="Print generated SQL.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    args = parser.parse_args()

    agent = FinRiskAgent(load_config(args.config))
    response = agent.run(args.question)

    if args.json:
        print(
            json.dumps(
                {
                    "question": response.question,
                    "plan": response.plan.__dict__,
                    "rows": response.result.rows,
                    "report": response.report,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.show_sql:
        print("SQL:")
        print(response.plan.sql.strip())
        print()
    print(response.report)


if __name__ == "__main__":
    main()
