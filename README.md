# risk-skills

> 面向消费金融、互联网小额信贷、联合贷和营销前筛场景的离线风控分析工具包。

`risk-skills` 的目标是沉淀一套可在封闭环境运行、低依赖、可复用、可验证的 Python 风控 Skill 基础设施。它不是依赖大模型完成计算的 Agent，也不是只能跑一次的 Notebook 脚本；核心计算会以独立 Python package 的方式提供，并通过统一配置和统一结果对象输出可追溯报告。

当前仓库同时保留了早期 `finrisk_agent` SQLite 演示项目，用于展示自然语言到只读 SQL 的封闭环境工作流。新开发的工具包位于 [src/risk_skills](/Users/chao/Documents/risk/src/risk_skills)。

## 核心能力

当前提供一个简洁离线 MVP，包含三个可直接 import 的 Skill：

| Skill | 目标 |
| --- | --- |
| `VariableAnalysisSkill` | 数据质量、变量画像、分箱、IV/KS/AUC/Lift、PSI、方向、评级、Excel/Markdown 报告 |
| `RuleMiningSkill` | 单变量阈值规则、分类规则、缺失规则、双变量 AND、分月验证、Train/Test 验证、Python/SQL 导出 |
| `ModelEvaluationSkill` | 已有模型分数评估、AUC/KS/Lift、分数分箱、分月/分群/分集合评估、PSI、校准和稳定性报告 |

当前已完成核心指标、分箱、Excel/Markdown 导出和三个业务 Skill 的基础闭环。实现重点是封闭环境可用、代码简洁、对宽表友好：可通过 `features.include` 精确指定变量，也可通过 `analysis.max_features` / `mining.max_features` 限制自动扫描规模，避免上百变量场景下候选规则或输出文件失控。

## 安装

开发安装：

```bash
python3 -m pip install -e .
```

核心计算依赖安装：

```bash
python3 -m pip install -r requirements-core.txt
```

开发测试依赖安装：

```bash
python3 -m pip install -r requirements-dev.txt
```

可选依赖安装：

```bash
python3 -m pip install -r requirements-optional.txt
```

## 快速开始

验证包导入、测试和离线 demo：

```bash
python3 -c "import risk_skills; print(risk_skills.__version__)"
python3 -m pytest -q

python3 examples/generate_demo_data.py
python3 examples/run_variable_analysis.py
python3 examples/run_rule_mining.py
python3 examples/run_model_evaluation.py
```

自定义 Skill 可继承 `BaseRiskSkill`：

```python
from risk_skills.core import BaseRiskSkill, SkillResult


class DummySkill(BaseRiskSkill):
    skill_name = "dummy"
    skill_version = "0.1.0"

    def validate_input(self, data):
        if data is None:
            raise ValueError("data is required")

    def run_analysis(self, data):
        return SkillResult(status="success", summary={"rows": len(data)})


result = DummySkill(config={"output": {"enabled": False}}).run([1, 2, 3])
print(result.summary)
```

## 三个 Skill 示例

三个 Skill 都已经可以在本地 DataFrame 上运行：

```python
from risk_skills.skills import (
    VariableAnalysisSkill,
    RuleMiningSkill,
    ModelEvaluationSkill,
)
```

变量分析用法：

```python
skill = VariableAnalysisSkill(config={
    "data": {"id_col": "cust_id", "time_col": "loan_month"},
    "targets": [{"name": "fpd7", "target_col": "fpd7", "observe_col": "can_7"}],
    "features": {"include": ["query_count_30d", "credit_score", "device_risk"]},
    "output": {"enabled": True, "directory": "output/variable_analysis"},
})
result = skill.run(df)
```

规则挖掘用法：

```python
skill = RuleMiningSkill(config={
    "data": {"time_col": "loan_month", "split_col": "split"},
    "targets": [{"name": "fpd7", "target_col": "fpd7", "observe_col": "can_7"}],
    "features": {"include": ["query_count_30d", "credit_score", "device_risk"]},
    "mining": {"min_hit_rate": 0.01, "max_hit_rate": 0.30, "min_lift": 1.30},
    "output": {"enabled": True, "directory": "output/rule_mining"},
})
result = skill.run(df)
```

模型评分评估用法：

```python
skill = ModelEvaluationSkill(config={
    "data": {"time_col": "loan_month", "segment_cols": ["channel"], "split_col": "split"},
    "target": {"name": "fpd7", "target_col": "fpd7", "observe_col": "can_7"},
    "score": {"score_col": "model_score", "higher_score_higher_risk": True, "bins": 10},
    "output": {"enabled": True, "directory": "output/model_evaluation"},
})
result = skill.run(df)
```

## 配置说明

配置支持三种形式：

- Python `dict`
- JSON 文件
- YAML 文件，安装 `PyYAML` 后启用

优先级：

```text
显式函数参数 > config dict > JSON/YAML 配置 > 默认值
```

业务字段、标签口径、变量列表、特殊值、输出路径和随机种子都应通过配置传入，不在底层函数中硬编码。

## 输出说明

所有 Skill 最终都应返回 `SkillResult`：

```text
status
summary
details
charts
exports
warnings
recommendations
metadata
error
```

运行元数据会包含包版本、Skill 名称、运行 ID、开始/结束时间、耗时、Python 版本、样本行列数、配置摘要和随机种子。报告模块只消费结构化结果，不在 Excel/Markdown 导出阶段重新计算指标。

## 兼容性

目标 Python 版本：

```text
Python 3.8 - 3.11
```

核心依赖目标范围：

```text
pandas >= 1.3
numpy >= 1.20
scipy >= 1.6
scikit-learn >= 0.24
matplotlib >= 3.3
openpyxl >= 3.0
```

`xgboost`、`lightgbm`、`shap`、`optuna`、`PyYAML` 都是可选依赖。缺失可选依赖时，核心 package 仍应可导入。

## 离线环境安装

在可联网机器上下载 wheels：

```bash
python3 -m pip download -r requirements-core.txt -d wheels/
python3 -m pip download . -d wheels/
```

在离线环境中安装：

```bash
python3 -m pip install --no-index --find-links=wheels/ -r requirements-core.txt
python3 -m pip install --no-index --find-links=wheels/ .
```

## 测试

```bash
python3 -m pytest -q
```

当前测试覆盖：

- `risk_skills` 包导入与版本
- 配置加载、深度合并、目标和特征规格构建
- `BaseRiskSkill` 生命周期、metadata、export 开关和错误阶段定位
- AUC、KS、IV/WOE、Lift、PSI、Wilson 区间等原子指标
- 数值/分类分箱 transformer 不丢样本
- 变量分析、规则挖掘、模型评分评估在宽表样本上的最小闭环
- 早期 `finrisk_agent` 只读 SQL guard 回归测试

## 项目结构

```text
.
├── src/risk_skills/
│   ├── core/              # BaseRiskSkill、SkillResult、配置、异常、注册表
│   ├── data/              # 宽表变量推断、类型识别和质量画像
│   ├── metrics/           # AUC、KS、IV、Lift、PSI、Brier、Wilson 区间
│   ├── binning/           # 数值/分类分箱和 BinTransformer
│   ├── variable/          # 变量分析底层模块
│   ├── strategy/          # 规则对象、导出和受控规则挖掘
│   ├── model/             # 已有模型评分评估
│   ├── report/            # Excel、Markdown 导出
│   ├── skills/            # VariableAnalysisSkill、RuleMiningSkill、ModelEvaluationSkill
│   └── utils/             # 日志、时间、序列化、可选依赖工具
├── tests/test_core/       # Phase 0 单元测试
├── tests/test_metrics/    # 指标测试
├── tests/test_binning/    # 分箱测试
├── tests/test_skills/     # 三个 Skill 的宽表闭环测试
├── examples/              # 可复现 demo 数据和运行脚本
├── finrisk_agent/         # 早期 SQL 演示 Agent，保留兼容
├── scripts/               # 早期演示数据脚本
├── docs/                  # 早期演示文档
└── output/                # Skill 输出目录
```

## 旧演示项目

早期演示项目仍可按原方式运行：

```bash
python3 scripts/generate_demo_data.py
streamlit run app.py
python3 -m finrisk_agent.cli "挖掘高风险风控规则，按风险提升倍数排序并给出候选规则" --show-sql
```

这部分代码用于展示本地 SQLite、只读 SQL 校验和封闭环境分析报告；它不会作为新 `risk_skills` 核心计算层的依赖。

## 路线图

开发顺序按阶段推进：

1. 已完成：项目骨架、核心对象、原子指标、分箱、三个 Skill 的离线 MVP、demo 数据和基础报告。
2. 下一步：增强分月/分群稳定性、Train/Test/OOT 衰减、规则去重、更多报告字段和图表。
3. 后续：监控、策略模拟、利润测算、模型开发和可选 LLM 报告润色。

后续可扩展 `StrategySimulationSkill`、`ModelDevelopmentSkill`、`MonitoringSkill`、`ProfitSimulationSkill` 和可选 LLM Adapter。LLM 只用于结构化结果解释和报告润色，不参与底层指标计算。

## 免责声明

本项目用于风控分析、研究和辅助决策，不应在缺少人工审查、合规评估和业务验证的情况下直接用于自动化信贷决策。仓库中的演示数据均为合成数据，不包含真实客户信息、内部策略或生产模型。
