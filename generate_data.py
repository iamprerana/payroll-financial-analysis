"""Generate deterministic synthetic payroll, service-hour, tax, reimbursement, and tenure data."""

from __future__ import annotations

import argparse
import csv
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


DEFAULT_SEED = 20261020
PAY_PERIODS: Tuple[str, ...] = (
    "2026-01",
    "2026-02",
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
)

DEPARTMENTS: Tuple[Dict[str, object], ...] = (
    {
        "department_id": "DEPT-ENG",
        "department_name": "Platform Engineering",
        "cost_center_code": "CC-101",
        "annual_budget_usd": 4850000.00,
    },
    {
        "department_id": "DEPT-CDS",
        "department_name": "Clinical Data Sciences",
        "cost_center_code": "CC-204",
        "annual_budget_usd": 3900000.00,
    },
    {
        "department_id": "DEPT-PRD",
        "department_name": "Product & Decision Analytics",
        "cost_center_code": "CC-309",
        "annual_budget_usd": 3350000.00,
    },
    {
        "department_id": "DEPT-CLS",
        "department_name": "Client Delivery Services",
        "cost_center_code": "CC-412",
        "annual_budget_usd": 3100000.00,
    },
    {
        "department_id": "DEPT-FIN",
        "department_name": "Finance & Payroll Operations",
        "cost_center_code": "CC-518",
        "annual_budget_usd": 2250000.00,
    },
    {
        "department_id": "DEPT-POP",
        "department_name": "People & Talent Operations",
        "cost_center_code": "CC-622",
        "annual_budget_usd": 1850000.00,
    },
)

JOB_LEVEL_SPECS: Dict[str, Dict[str, object]] = {
    "L1": {
        "titles": (
            "Associate Analyst",
            "Junior Payroll Specialist",
            "Operations Coordinator",
            "Associate Data Programmer",
        ),
        "salary_range": (64000, 82000),
        "tax_bracket_pct": 12.0,
        "non_bonus_tenure_range": (11.0, 22.0),
        "bonus_uplift_factor": 1.61,
    },
    "L2": {
        "titles": (
            "Financial Data Analyst",
            "Statistical Programmer",
            "Client Implementation Specialist",
            "Software Engineer",
        ),
        "salary_range": (86000, 114000),
        "tax_bracket_pct": 18.0,
        "non_bonus_tenure_range": (16.0, 29.0),
        "bonus_uplift_factor": 1.63,
    },
    "L3": {
        "titles": (
            "Senior Compensation Analyst",
            "Senior Statistical Programmer",
            "Senior Product Analyst",
            "Senior Delivery Lead",
        ),
        "salary_range": (118000, 148000),
        "tax_bracket_pct": 24.0,
        "non_bonus_tenure_range": (21.0, 35.0),
        "bonus_uplift_factor": 1.62,
    },
    "L4": {
        "titles": (
            "Principal Analytics Lead",
            "Payroll Systems Manager",
            "Director of Service Delivery",
            "Lead Engineering Manager",
        ),
        "salary_range": (152000, 186000),
        "tax_bracket_pct": 28.0,
        "non_bonus_tenure_range": (25.0, 41.0),
        "bonus_uplift_factor": 1.60,
    },
}

FIRST_NAMES: Tuple[str, ...] = (
    "Aarav", "Maya", "Liam", "Sofia", "Noah", "Ananya", "Ethan", "Priya",
    "Lucas", "Zoe", "Rohan", "Elena", "Mason", "Nadia", "Logan", "Kavya",
    "Caleb", "Iris", "Owen", "Meera", "Nathan", "Clara", "Isaac", "Tara",
    "Julian", "Leah", "Devon", "Sana", "Adrian", "Nora",
)

LAST_NAMES: Tuple[str, ...] = (
    "Patel", "Chen", "Rivera", "Kim", "Sharma", "Nguyen", "Brooks", "Iyer",
    "Morgan", "kapoor", "Silva", "Mehta", "carter", "Desai", "reed", "Nair",
    "Foster", "Joshi", "Bennett", "Verma", "Hayes", "Rao", "Price", "Kulkarni",
)

EXPENSE_CATEGORIES: Tuple[Tuple[str, float, float, float], ...] = (
    ("Client Travel & Lodging", 180.0, 920.0, 0.94),
    ("Professional Certification & Training", 150.0, 680.0, 0.96),
    ("Home Office & Ergonomic Equipment", 95.0, 420.0, 0.91),
    ("Client Meals & Onsite Hospitality", 65.0, 310.0, 0.87),
    ("Telecom & Data Connectivity", 50.0, 145.0, 0.98),
)


def generate_dataset(
    employee_count: int = 180,
    seed: int = DEFAULT_SEED,
) -> Dict[str, List[Dict[str, object]]]:
    """Generate all relational tables for the payroll analytics project."""
    if employee_count < 24:
        raise ValueError("employee_count must be at least 24 for stratified cohorts")

    rng = random.Random(seed)
    reference_end_date = date(2026, 6, 30)

    departments: List[Dict[str, object]] = [dict(dept) for dept in DEPARTMENTS]
    employees: List[Dict[str, object]] = []
    service_logs: List[Dict[str, object]] = []
    bonus_awards: List[Dict[str, object]] = []
    reimbursement_claims: List[Dict[str, object]] = []
    payroll_statements: List[Dict[str, object]] = []

    level_cycle: Tuple[str, ...] = ("L1", "L1", "L2", "L2", "L2", "L3", "L3", "L4")

    for idx in range(1, employee_count + 1):
        emp_id = f"EMP-{idx:04d}"
        dept_idx = (idx - 1) % len(departments)
        within_dept_idx = (idx - 1) // len(departments)
        dept = departments[dept_idx]
        dept_id = str(dept["department_id"])
        level = level_cycle[(within_dept_idx + dept_idx) % len(level_cycle)]
        spec = JOB_LEVEL_SPECS[level]

        first_name = FIRST_NAMES[(idx * 7) % len(FIRST_NAMES)]
        last_name = LAST_NAMES[(idx * 11 + 3) % len(LAST_NAMES)].capitalize()
        full_name = f"{first_name} {last_name}"

        titles = spec["titles"]
        assert isinstance(titles, tuple)
        job_title = str(titles[(within_dept_idx + dept_idx) % len(titles)])

        salary_low, salary_high = spec["salary_range"]  # type: ignore[misc]
        dept_salary_multiplier = {
            "DEPT-ENG": 1.08,
            "DEPT-CDS": 1.05,
            "DEPT-PRD": 1.03,
            "DEPT-CLS": 0.98,
            "DEPT-FIN": 0.96,
            "DEPT-POP": 0.93,
        }[dept_id]
        raw_salary = rng.uniform(float(salary_low), float(salary_high)) * dept_salary_multiplier
        annual_base_salary = round(raw_salary / 500.0) * 500.0
        standard_monthly_hours = 160
        tax_bracket_pct = float(spec["tax_bracket_pct"])  # type: ignore[arg-type]

        # 60% of employees receive performance/retention bonuses across the evaluation window.
        received_bonus_flag = 1 if (within_dept_idx % 5 in (0, 1, 2)) else 0
        if received_bonus_flag == 1:
            bonus_count = rng.choices((1, 2, 3), weights=(42, 38, 20))[0]
        else:
            bonus_count = 0

        base_min, base_max = spec["non_bonus_tenure_range"]  # type: ignore[misc]
        baseline_tenure = rng.uniform(float(base_min), float(base_max))
        if received_bonus_flag == 1:
            tier_boost = 1.0 + (bonus_count - 1) * 0.085
            uplift = float(spec["bonus_uplift_factor"]) * tier_boost  # type: ignore[arg-type]
            tenure_months = round(baseline_tenure * uplift, 1)
            active_prob = 0.91
        else:
            tenure_months = round(baseline_tenure, 1)
            active_prob = 0.68

        is_active = rng.random() < active_prob
        employment_status = "Active" if is_active else "Separated"

        if is_active:
            exit_date_str = ""
            hire_date_val = reference_end_date - timedelta(days=int(round(tenure_months * 30.4375)))
            active_periods = list(PAY_PERIODS)
        else:
            # Separated employees exited in Q2 (after 3 to 5 paid months in 2026)
            active_month_count = rng.randint(3, 5)
            active_periods = list(PAY_PERIODS[:active_month_count])
            last_year, last_month = map(int, active_periods[-1].split("-"))
            exit_date_val = date(last_year, last_month, 28)
            exit_date_str = exit_date_val.isoformat()
            hire_date_val = exit_date_val - timedelta(days=int(round(tenure_months * 30.4375)))

        employees.append(
            {
                "employee_id": emp_id,
                "full_name": full_name,
                "department_id": dept_id,
                "job_title": job_title,
                "job_level": level,
                "employment_type": "Full-Time",
                "hire_date": hire_date_val.isoformat(),
                "exit_date": exit_date_str,
                "employment_status": employment_status,
                "tenure_months": tenure_months,
                "annual_base_salary": round(annual_base_salary, 2),
                "standard_monthly_hours": standard_monthly_hours,
                "tax_bracket_pct": tax_bracket_pct,
                "received_bonus_flag": received_bonus_flag,
                "bonus_count": bonus_count,
            }
        )

        # Schedule bonus awards across active pay periods for bonus recipients
        bonus_by_period: Dict[str, float] = {}
        if bonus_count > 0:
            candidate_periods = [p for p in ("2026-03", "2026-06", "2026-01", "2026-04") if p in active_periods]
            while len(candidate_periods) < bonus_count:
                candidate_periods.append(active_periods[-1])
            selected_periods = candidate_periods[:bonus_count]
            bonus_types = (
                "Quarterly Service Excellence Bonus",
                "Annual Performance & Retention Bonus",
                "Milestone Delivery Bonus",
            )
            ratings = ("Exceeds Expectations", "Outstanding Impact", "Meets Plus")
            for b_idx, period in enumerate(selected_periods):
                pct_of_annual = rng.uniform(0.032, 0.062)
                award_amount = round(annual_base_salary * pct_of_annual, 2)
                bonus_by_period[period] = round(bonus_by_period.get(period, 0.0) + award_amount, 2)
                bonus_awards.append(
                    {
                        "bonus_id": f"BON-{idx:04d}-{b_idx + 1:02d}",
                        "employee_id": emp_id,
                        "pay_period": period,
                        "bonus_type": bonus_types[b_idx % len(bonus_types)],
                        "bonus_amount": award_amount,
                        "performance_rating": ratings[b_idx % len(ratings)],
                    }
                )

        hourly_base_rate = round((annual_base_salary / 12.0) / standard_monthly_hours, 2)

        for p_idx, period in enumerate(active_periods):
            # Services rendered in the pay period
            regular_hours = round(rng.choices((160.0, 156.0, 152.0, 148.0), weights=(72, 14, 9, 5))[0], 2)
            utilization_ratio = rng.uniform(0.82, 0.96) if received_bonus_flag else rng.uniform(0.76, 0.91)
            billable_hours = round(regular_hours * utilization_ratio, 2)

            overtime_hours = (
                round(rng.uniform(2.0, 16.0), 2)
                if rng.random() < (0.64 if dept_id in ("DEPT-ENG", "DEPT-CDS", "DEPT-CLS") else 0.42)
                else 0.0
            )
            overtime_multiplier = 1.50 if overtime_hours <= 12.0 else 1.75
            quality_base = 4.25 if received_bonus_flag else 3.85
            service_quality_score = round(min(5.0, max(3.1, rng.gauss(quality_base, 0.24))), 2)

            service_logs.append(
                {
                    "service_log_id": f"SRV-{idx:04d}-{p_idx + 1:02d}",
                    "employee_id": emp_id,
                    "pay_period": period,
                    "standard_hours": standard_monthly_hours,
                    "regular_hours_worked": regular_hours,
                    "billable_service_hours": billable_hours,
                    "overtime_hours": overtime_hours,
                    "overtime_multiplier": overtime_multiplier,
                    "service_quality_score": service_quality_score,
                }
            )

            # Expense reimbursements in the pay period
            reimb_approved_total = 0.0
            if rng.random() < 0.45:
                cat_name, min_amt, max_amt, approval_ratio = rng.choice(EXPENSE_CATEGORIES)
                submitted = round(rng.uniform(min_amt, max_amt), 2)
                approved = round(submitted * rng.uniform(approval_ratio, 1.0), 2)
                reimb_approved_total = approved
                reimbursement_claims.append(
                    {
                        "claim_id": f"CLM-{idx:04d}-{p_idx + 1:02d}",
                        "employee_id": emp_id,
                        "pay_period": period,
                        "expense_category": cat_name,
                        "submitted_amount": submitted,
                        "approved_amount": approved,
                        "is_tax_exempt": 1,
                    }
                )

            base_service_pay = round(regular_hours * hourly_base_rate, 2)
            overtime_pay = round(overtime_hours * hourly_base_rate * overtime_multiplier, 2)
            bonus_pay = round(bonus_by_period.get(period, 0.0), 2)
            gross_taxable_pay = round(base_service_pay + overtime_pay + bonus_pay, 2)

            # Statutory TDS rate: base bracket + 2% supplemental withholding when bonus is paid
            tds_rate_pct = round(tax_bracket_pct + (2.0 if bonus_pay > 0 else 0.0), 2)
            tds_deducted = round(gross_taxable_pay * (tds_rate_pct / 100.0), 2)
            net_pay = round(gross_taxable_pay - tds_deducted + reimb_approved_total, 2)

            payroll_statements.append(
                {
                    "statement_id": f"PAY-{idx:04d}-{p_idx + 1:02d}",
                    "employee_id": emp_id,
                    "department_id": dept_id,
                    "pay_period": period,
                    "regular_hours_worked": regular_hours,
                    "billable_service_hours": billable_hours,
                    "overtime_hours": overtime_hours,
                    "hourly_base_rate": hourly_base_rate,
                    "base_service_pay": base_service_pay,
                    "overtime_pay": overtime_pay,
                    "bonus_pay": bonus_pay,
                    "gross_taxable_pay": gross_taxable_pay,
                    "tds_rate_pct": tds_rate_pct,
                    "tds_deducted": tds_deducted,
                    "reimbursements_approved": reimb_approved_total,
                    "net_pay": net_pay,
                }
            )

    return {
        "departments": departments,
        "employees": employees,
        "service_logs": service_logs,
        "bonus_awards": bonus_awards,
        "reimbursement_claims": reimbursement_claims,
        "payroll_statements": payroll_statements,
    }


def write_csv_table(rows: Sequence[Dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Cannot write empty table to {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def create_sqlite_database(
    dataset: Dict[str, List[Dict[str, object]]],
    db_path: Path,
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("PRAGMA foreign_keys = OFF;")
        for table in (
            "payroll_statements",
            "reimbursement_claims",
            "bonus_awards",
            "service_logs",
            "employees",
            "departments",
        ):
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.execute("PRAGMA foreign_keys = ON;")

        conn.executescript(
            """
            CREATE TABLE departments (
                department_id TEXT PRIMARY KEY,
                department_name TEXT NOT NULL,
                cost_center_code TEXT NOT NULL,
                annual_budget_usd REAL NOT NULL
            );

            CREATE TABLE employees (
                employee_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                department_id TEXT NOT NULL,
                job_title TEXT NOT NULL,
                job_level TEXT NOT NULL,
                employment_type TEXT NOT NULL,
                hire_date TEXT NOT NULL,
                exit_date TEXT,
                employment_status TEXT NOT NULL,
                tenure_months REAL NOT NULL,
                annual_base_salary REAL NOT NULL,
                standard_monthly_hours INTEGER NOT NULL,
                tax_bracket_pct REAL NOT NULL,
                received_bonus_flag INTEGER NOT NULL,
                bonus_count INTEGER NOT NULL,
                FOREIGN KEY (department_id) REFERENCES departments (department_id)
            );

            CREATE TABLE service_logs (
                service_log_id TEXT PRIMARY KEY,
                employee_id TEXT NOT NULL,
                pay_period TEXT NOT NULL,
                standard_hours INTEGER NOT NULL,
                regular_hours_worked REAL NOT NULL,
                billable_service_hours REAL NOT NULL,
                overtime_hours REAL NOT NULL,
                overtime_multiplier REAL NOT NULL,
                service_quality_score REAL NOT NULL,
                UNIQUE (employee_id, pay_period),
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
            );

            CREATE TABLE bonus_awards (
                bonus_id TEXT PRIMARY KEY,
                employee_id TEXT NOT NULL,
                pay_period TEXT NOT NULL,
                bonus_type TEXT NOT NULL,
                bonus_amount REAL NOT NULL,
                performance_rating TEXT NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
            );

            CREATE TABLE reimbursement_claims (
                claim_id TEXT PRIMARY KEY,
                employee_id TEXT NOT NULL,
                pay_period TEXT NOT NULL,
                expense_category TEXT NOT NULL,
                submitted_amount REAL NOT NULL,
                approved_amount REAL NOT NULL,
                is_tax_exempt INTEGER NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
            );

            CREATE TABLE payroll_statements (
                statement_id TEXT PRIMARY KEY,
                employee_id TEXT NOT NULL,
                department_id TEXT NOT NULL,
                pay_period TEXT NOT NULL,
                regular_hours_worked REAL NOT NULL,
                billable_service_hours REAL NOT NULL,
                overtime_hours REAL NOT NULL,
                hourly_base_rate REAL NOT NULL,
                base_service_pay REAL NOT NULL,
                overtime_pay REAL NOT NULL,
                bonus_pay REAL NOT NULL,
                gross_taxable_pay REAL NOT NULL,
                tds_rate_pct REAL NOT NULL,
                tds_deducted REAL NOT NULL,
                reimbursements_approved REAL NOT NULL,
                net_pay REAL NOT NULL,
                UNIQUE (employee_id, pay_period),
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id),
                FOREIGN KEY (department_id) REFERENCES departments (department_id)
            );

            CREATE INDEX idx_employees_dept ON employees (department_id);
            CREATE INDEX idx_employees_bonus ON employees (received_bonus_flag, tenure_months);
            CREATE INDEX idx_service_period ON service_logs (pay_period);
            CREATE INDEX idx_payroll_period ON payroll_statements (pay_period);
            CREATE INDEX idx_payroll_dept ON payroll_statements (department_id);
            """
        )

        for table_name, rows in dataset.items():
            cols = list(rows[0].keys())
            placeholders = ", ".join("?" for _ in cols)
            col_list = ", ".join(cols)
            conn.executemany(
                f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})",
                [[row[c] if row[c] != "" else None for c in cols] for row in rows],
            )
        conn.commit()


def _sql_literal(value: object) -> str:
    if value is None or value == "":
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def write_mysql_seed_file(
    dataset: Dict[str, List[Dict[str, object]]],
    sql_seed_path: Path,
) -> None:
    """Write a MySQL 8.0 compatible seed script (`INSERT INTO ... VALUES ...`)."""
    sql_seed_path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = [
        "-- ============================================================================",
        "-- Financial Analysis for Payroll — MySQL 8.0 Deterministic Seed Data",
        "-- Generated automatically by generate_data.py (seed = 20261020)",
        "-- ============================================================================",
        "USE payroll_analytics;",
        "SET FOREIGN_KEY_CHECKS = 0;",
        "TRUNCATE TABLE payroll_statements;",
        "TRUNCATE TABLE reimbursement_claims;",
        "TRUNCATE TABLE bonus_awards;",
        "TRUNCATE TABLE service_logs;",
        "TRUNCATE TABLE employees;",
        "TRUNCATE TABLE departments;",
        "SET FOREIGN_KEY_CHECKS = 1;",
        "",
    ]
    for table_name, rows in dataset.items():
        if not rows:
            continue
        cols = list(rows[0].keys())
        col_list = ", ".join(cols)
        lines.append(f"INSERT INTO {table_name} ({col_list}) VALUES")
        row_tuples: List[str] = []
        for row in rows:
            vals = ", ".join(_sql_literal(row[c]) for c in cols)
            row_tuples.append(f"  ({vals})")
        lines.append(",\n".join(row_tuples) + ";\n")

    sql_seed_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic payroll financial analysis data and database."
    )
    parser.add_argument("--employees", type=int, default=180)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "data",
    )
    parser.add_argument(
        "--sql-seed-path",
        type=Path,
        default=Path(__file__).resolve().parent / "sql" / "mysql_seed_data.sql",
    )
    args = parser.parse_args()

    dataset = generate_dataset(employee_count=args.employees, seed=args.seed)
    for table_name, rows in dataset.items():
        write_csv_table(rows, args.data_dir / f"{table_name}.csv")

    db_path = args.data_dir / "payroll_analytics.db"
    create_sqlite_database(dataset, db_path)
    write_mysql_seed_file(dataset, args.sql_seed_path)

    print(
        f"Generated {len(dataset['employees'])} employees, "
        f"{len(dataset['service_logs'])} service logs, "
        f"{len(dataset['bonus_awards'])} bonus awards, "
        f"{len(dataset['reimbursement_claims'])} reimbursement claims, and "
        f"{len(dataset['payroll_statements'])} payroll statements in {args.data_dir}"
    )


if __name__ == "__main__":
    main()
