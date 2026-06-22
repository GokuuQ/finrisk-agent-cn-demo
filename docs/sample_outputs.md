# Sample Outputs

The following examples are generated from synthetic demo data. They are included so reviewers can understand the expected output shape before running the app.

## Scenario 1: Delinquency Trend

Question:

```text
分析近6个月M1/M2逾期率变化，并定位主要风险上升客群
```

Generated SQL:

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

Report excerpt:

```text
核心发现
- 本次分析返回 67 个分组结果，重点指标为 mob3_m1_rate。
- 最高风险分组为 apply_month=2025-10、channel=partner、risk_grade=C、product_type=installment，mob3_m1_rate=32.00%。
- 从 2025-06 到 2025-11，分组平均 mob3_m1_rate 下降 0.78%。
- 该分组放款笔数为 25，建议优先关注样本量较大且风险升高的分组。
```

## Scenario 2: Strategy Impact

Question:

```text
评估2025年7月额度策略调整前后的通过率、M1逾期率和收益变化
```

Generated SQL:

```sql
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
```

Report excerpt:

```text
核心发现
- 本次分析返回 2 个分组结果，重点指标为 mob3_m1_rate。
- 最高风险分组为 period=after_policy，mob3_m1_rate=10.05%。
- 该分组申请量为 3794，需要结合样本量判断波动是否稳定。
```

## Scenario 3: Risk Daily Report

Question:

```text
生成最近一个月风险日报，说明核心指标、异常波动和建议动作
```

Generated SQL:

```sql
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
```

Report excerpt:

```text
核心发现
- 本次分析返回 15 个分组结果，重点指标为 mob1_m1_rate。
- 最高风险分组为 apply_month=2025-11、channel=partner、risk_grade=D，mob1_m1_rate=15.79%。
- 该分组申请量为 54，需要结合样本量判断波动是否稳定。
```
