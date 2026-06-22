from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path


DB_PATH = Path("data/finrisk_demo.sqlite")
RANDOM_SEED = 20250627


def main() -> None:
    random.seed(RANDOM_SEED)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as conn:
        create_schema(conn)
        customers = generate_customers(5000)
        conn.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?)",
            customers,
        )
        applications, loans, performance = generate_credit_flow(customers)
        conn.executemany(
            "INSERT INTO applications VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            applications,
        )
        conn.executemany(
            "INSERT INTO loans VALUES (?, ?, ?, ?, ?, ?)",
            loans,
        )
        conn.executemany(
            "INSERT INTO monthly_performance VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            performance,
        )
        conn.executemany(
            "INSERT INTO strategy_events VALUES (?, ?, ?, ?)",
            [
                (
                    "EVT-202507-LIMIT",
                    "2025-07-01",
                    "额度策略调整",
                    "提高A/B客群额度上限，收紧D/E客群通过阈值。",
                )
            ],
        )
    print(f"Generated demo database at {DB_PATH}")


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
CREATE TABLE customers (
  customer_id TEXT PRIMARY KEY,
  age_band TEXT,
  city_tier TEXT,
  risk_grade TEXT,
  income_band TEXT
);

CREATE TABLE applications (
  app_id TEXT PRIMARY KEY,
  customer_id TEXT,
  apply_date TEXT,
  channel TEXT,
  product_type TEXT,
  requested_amount REAL,
  approved INTEGER,
  approved_amount REAL,
  apr REAL
);

CREATE TABLE loans (
  loan_id TEXT PRIMARY KEY,
  app_id TEXT,
  booked_date TEXT,
  principal REAL,
  tenor INTEGER,
  rate REAL
);

CREATE TABLE monthly_performance (
  loan_id TEXT,
  mob INTEGER,
  observe_month TEXT,
  balance REAL,
  m1_flag INTEGER,
  m2_flag INTEGER,
  interest_income REAL,
  credit_loss REAL
);

CREATE TABLE strategy_events (
  event_id TEXT PRIMARY KEY,
  event_date TEXT,
  event_name TEXT,
  description TEXT
);
"""
    )


def generate_customers(n: int) -> list[tuple[str, str, str, str, str]]:
    age_bands = ["18-24", "25-34", "35-44", "45-54", "55+"]
    city_tiers = ["T1", "T2", "T3", "T4+"]
    risk_grades = ["A", "B", "C", "D", "E"]
    income_bands = ["low", "mid", "high"]
    weights = [0.12, 0.26, 0.34, 0.2, 0.08]

    customers = []
    for idx in range(1, n + 1):
        customers.append(
            (
                f"C{idx:06d}",
                random.choices(age_bands, weights=[0.16, 0.38, 0.28, 0.13, 0.05])[0],
                random.choices(city_tiers, weights=[0.18, 0.32, 0.34, 0.16])[0],
                random.choices(risk_grades, weights=weights)[0],
                random.choices(income_bands, weights=[0.36, 0.46, 0.18])[0],
            )
        )
    return customers


def generate_credit_flow(customers: list[tuple[str, str, str, str, str]]):
    start = date(2025, 1, 1)
    applications = []
    loans = []
    performance = []
    app_id = 1
    loan_id = 1
    channels = ["app", "partner", "offline", "ad_network"]
    products = ["cash_loan", "installment", "credit_line"]
    risk_score = {"A": 0.04, "B": 0.07, "C": 0.11, "D": 0.18, "E": 0.28}

    for day_offset in range(334):
        apply_day = start + timedelta(days=day_offset)
        daily_count = random.randint(25, 55)
        for _ in range(daily_count):
            customer = random.choice(customers)
            customer_id, _, _, grade, income_band = customer
            channel = random.choices(channels, weights=[0.44, 0.28, 0.12, 0.16])[0]
            product = random.choices(products, weights=[0.45, 0.35, 0.20])[0]
            requested = random.choice([3000, 5000, 8000, 12000, 20000, 30000])
            base_approval = {"A": 0.88, "B": 0.78, "C": 0.62, "D": 0.38, "E": 0.18}[grade]

            if apply_day >= date(2025, 7, 1):
                if grade in {"A", "B"}:
                    base_approval += 0.04
                if grade in {"D", "E"}:
                    base_approval -= 0.05
                if channel == "ad_network":
                    base_approval += 0.03

            approved = int(random.random() < base_approval)
            amount_factor = {"low": 0.6, "mid": 0.85, "high": 1.1}[income_band]
            approved_amount = round(requested * amount_factor * random.uniform(0.75, 1.05), 2) if approved else 0
            apr = round({"A": 0.108, "B": 0.13, "C": 0.158, "D": 0.188, "E": 0.218}[grade], 4)

            current_app = f"A{app_id:07d}"
            applications.append(
                (
                    current_app,
                    customer_id,
                    apply_day.isoformat(),
                    channel,
                    product,
                    requested,
                    approved,
                    approved_amount,
                    apr,
                )
            )

            if approved and random.random() < 0.86:
                current_loan = f"L{loan_id:07d}"
                tenor = random.choice([6, 9, 12])
                loans.append(
                    (
                        current_loan,
                        current_app,
                        (apply_day + timedelta(days=random.randint(0, 3))).isoformat(),
                        approved_amount,
                        tenor,
                        apr,
                    )
                )
                performance.extend(
                    generate_performance(
                        current_loan,
                        apply_day,
                        approved_amount,
                        apr,
                        grade,
                        channel,
                    )
                )
                loan_id += 1
            app_id += 1

    return applications, loans, performance


def generate_performance(
    loan_id: str,
    booked_date: date,
    principal: float,
    apr: float,
    grade: str,
    channel: str,
) -> list[tuple[str, int, str, float, int, int, float, float]]:
    risk_base = {"A": 0.025, "B": 0.045, "C": 0.075, "D": 0.12, "E": 0.18}[grade]
    channel_lift = {"app": 0.0, "partner": 0.012, "offline": -0.006, "ad_network": 0.035}[channel]
    policy_lift = 0.018 if booked_date >= date(2025, 8, 1) and channel == "ad_network" else 0.0
    rows = []
    for mob in range(1, 7):
        observe_month = add_months(booked_date, mob).strftime("%Y-%m")
        balance = max(principal * (1 - (mob - 1) / 7), 0)
        m1_prob = min(max(risk_base + channel_lift + policy_lift + mob * 0.006, 0.005), 0.45)
        m1_flag = int(random.random() < m1_prob)
        m2_flag = int(m1_flag and random.random() < min(0.58, m1_prob * 2.1))
        interest_income = balance * apr / 12
        credit_loss = balance * (0.36 if m2_flag else 0.12 if m1_flag else 0.006)
        rows.append(
            (
                loan_id,
                mob,
                observe_month,
                round(balance, 2),
                m1_flag,
                m2_flag,
                round(interest_income, 2),
                round(credit_loss, 2),
            )
        )
    return rows


def add_months(input_date: date, months: int) -> date:
    month = input_date.month - 1 + months
    year = input_date.year + month // 12
    month = month % 12 + 1
    day = min(input_date.day, 28)
    return date(year, month, day)


if __name__ == "__main__":
    main()
