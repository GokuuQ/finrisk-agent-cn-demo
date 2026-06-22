# 样例输出

以下内容由合成演示数据生成，用于说明项目的输出形态。实际运行时，结果会随数据生成逻辑和配置略有变化。

## 场景一：风险趋势分析

问题：

```text
分析近6个月M1/M2逾期率变化，并定位主要风险上升客群
```

生成 SQL：

```sql
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
```

报告片段：

```text
核心发现
- 本次分析返回 67 个分组结果，重点指标为 mob3_m1_rate。
- 最高风险分组为 apply_month=2025-10、channel=partner、risk_grade=C、product_type=installment，mob3_m1_rate=32.00%。
- 从 2025-06 到 2025-11，分组平均 mob3_m1_rate 下降 0.78%。
- 该分组放款笔数为 25，建议优先关注样本量较大且风险升高的分组。
```

## 场景二：风控规则挖掘

问题：

```text
挖掘高风险风控规则，按风险提升倍数排序并给出候选规则
```

输出字段：

| 字段 | 含义 |
| --- | --- |
| `candidate_rule` | 候选规则描述 |
| `applications` / `loans` | 命中申请量和放款量 |
| `mob3_m1_rate` / `mob3_m2_rate` | 规则命中样本的 MOB3 逾期表现 |
| `mob3_balance` | 规则命中样本的 MOB3 余额 |
| `risk_lift` | 相对整体 M1 逾期率的风险提升倍数 |

报告片段：

```text
核心发现
- 本次挖掘返回若干条候选风控规则，排序依据为风险提升倍数和 MOB3 M1 逾期率。
- 排名最高的规则包含渠道、风险等级、产品、城市等级和收入带组合。
- 候选规则不直接等同于生产策略，仍需结合样本稳定性、收益、通过率影响和合规要求进行复核。
```

## 场景三：策略开发

问题：

```text
基于近期表现开发准入与额度策略候选方案，输出命中量、风险和建议动作
```

候选策略类型：

| 策略 | 条件 | 建议动作 |
| --- | --- | --- |
| 高风险渠道 D/E 收紧准入 | `channel IN (partner, ad_network) AND risk_grade IN (D, E)` | 拒绝或转人工复核 |
| 大额低收入客群额度下调 | `income_band=low AND requested_amount>=20000` | 额度上限下调至 12000 |
| 广告渠道分期产品复核 | `channel=ad_network AND product_type=installment` | 增加二次校验或降低通过阈值 |

报告片段：

```text
核心发现
- 本次生成若干条候选策略，覆盖准入收紧、额度下调和人工复核等动作。
- 每条策略输出命中申请量、当前通过率、MOB3 M1/M2、余额、净收入和已批核敞口。
- 上线前应做拒绝推断、收益测算和 A/B 或灰度验证。
```

## 场景四：策略效果评估

问题：

```text
评估2025年7月额度策略调整前后的通过率、M1逾期率和收益变化
```

报告片段：

```text
核心发现
- 本次分析返回 2 个分组结果，重点指标为 mob3_m1_rate。
- 最高风险分组为 period=after_policy，mob3_m1_rate=10.05%。
- 该分组申请量为 3794，需要结合样本量判断波动是否稳定。
```

## 场景五：风险日报

问题：

```text
生成最近一个月风险日报，说明核心指标、异常波动和建议动作
```

报告片段：

```text
核心发现
- 本次分析返回 15 个分组结果，重点指标为 mob1_m1_rate。
- 最高风险分组为 apply_month=2025-11、channel=partner、risk_grade=D，mob1_m1_rate=15.79%。
- 该分组申请量为 54，需要结合样本量判断波动是否稳定。
```
