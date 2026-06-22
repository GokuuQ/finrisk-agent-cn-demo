from __future__ import annotations

import argparse
import json

from finrisk_agent.agent import FinRiskAgent
from finrisk_agent.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="运行消费金融风控分析智能体演示项目。")
    parser.add_argument("question", help="自然语言风控分析问题。")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径。")
    parser.add_argument("--show-sql", action="store_true", help="打印生成的 SQL。")
    parser.add_argument("--json", action="store_true", help="打印 JSON 格式结果。")
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
