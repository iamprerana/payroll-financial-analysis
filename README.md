# Financial Analysis for Payroll (SQL Compensation & Retention Project)

A portfolio-ready SQL and Python financial analytics project analyzing employee compensation based on services rendered—covering base salary prorated by service hours, overtime pay, performance and retention bonuses, Tax Deducted at Source (TDS), and non-taxable expense reimbursements—alongside a cohort retention analysis examining the relationship between bonus compensation and employee work duration.

> **Data & Evidence Boundary:** All tables in this repository are generated deterministically from `generate_data.py` (`seed = 20261020`) and contain **explicitly synthetic payroll data** (no personal or employer compensation records). The headline finding—that employees receiving bonuses have **+69.91% (~70%) longer average work duration** than non-bonus peers—is an observational cohort association in the modeled data, not a causal field experiment.

---

## Business Problem

Finance, Payroll Operations, and People Analytics teams need a single, auditable SQL data model to answer two core questions:
1. **Gross-to-Net Payroll Accuracy:** How do billable/regular service hours, overtime multipliers, bonus awards, progressive Tax Deducted at Source (TDS) slabs, and expense reimbursements reconcile into net employee disbursements across departments and cost centers?
2. **Compensation & Retention Effectiveness:** How strongly do performance and milestone bonus awards correlate with employee tenure (duration of work in the company) and active retention rates—and does that relationship hold within individual job levels (`L1`–`L4`) rather than simply reflecting seniority?

---

## Project Architecture & Files

```text
payroll-financial-analysis/
├── README.md                          # Project overview, schema, SQL guide, and resume bullets
├── PROJECT_GUIDE_AND_NEXT_STEPS.md    # Complete run instructions, math walkthrough & future roadmap
├── interactive_project_guide.html     # Interactive browser learning app (architecture, SQL, simulator)
├── generate_data.py                   # Deterministic synthetic data, SQLite DB & MySQL seed generator
├── analytics.py                       # SQL query runner, reconciliation audit, and report builder
├── sql/
│   ├── mysql_schema.sql               # MySQL 8.0 DDL (6 normalized tables, FKs, indexes)
│   ├── mysql_seed_data.sql            # MySQL 8.0 INSERT seed script (all 180 employees & statements)
│   └── mysql_analysis_queries.sql     # 8 production SQL queries (CTEs, window functions, joins)
├── data/
│   ├── payroll_analytics.db           # Local SQLite database populated from the same schema
│   ├── departments.csv                # 6 departments & cost centers
│   ├── employees.csv                  # 180 employees (L1–L4, tenure, salary, tax slab, status)
│   ├── service_logs.csv               # 1,019 monthly service-hour & overtime logs (H1 2026)
│   ├── bonus_awards.csv               # 183 performance, milestone, and retention bonus awards
│   ├── reimbursement_claims.csv       # 450 submitted vs. approved expense reimbursement claims
│   └── payroll_statements.csv         # 1,019 gross-to-net monthly payroll statements
├── outputs/
│   ├── FINDINGS_REPORT.md             # Full SQL-derived analytical readout
│   ├── executive_kpis.csv             # Top-level payroll & retention KPIs
│   ├── employee_compensation_summary.csv
│   ├── department_payroll_breakdown.csv
│   ├── overtime_service_utilization.csv
│   ├── tds_tax_bracket_summary.csv
│   ├── reimbursement_category_summary.csv
│   ├── bonus_tenure_comparison.csv
│   ├── bonus_tier_tenure_breakdown.csv
│   └── level_controlled_tenure_check.csv
└── tests/
    └── test_payroll_analytics.py      # Automated unit tests for data, SQL queries, & accounting
```

---

## Relational Schema (`sql/mysql_schema.sql`)

| Table | Primary Key | Key Columns & Business Logic |
| --- | --- | --- |
| `departments` | `department_id` | Cost center code and annual departmental budget |
| `employees` | `employee_id` | Department FK, job level (`L1`–`L4`), hire/exit dates, `tenure_months`, `annual_base_salary`, statutory `tax_bracket_pct`, `received_bonus_flag` |
| `service_logs` | `service_log_id` | Monthly `regular_hours_worked`, `billable_service_hours`, `overtime_hours`, `overtime_multiplier` (`1.50x` or `1.75x`), `service_quality_score` |
| `bonus_awards` | `bonus_id` | Quarterly service excellence, milestone delivery, and annual retention bonuses |
| `reimbursement_claims` | `claim_id` | Submitted vs. approved expense claims across 5 categories (`is_tax_exempt = 1`) |
| `payroll_statements` | `statement_id` | Monthly register reconciling `base_service_pay + overtime_pay + bonus_pay = gross_taxable_pay` and `gross_taxable_pay - tds_deducted + reimbursements_approved = net_pay` |

---

## Key Analytical Findings (from [`outputs/FINDINGS_REPORT.md`](outputs/FINDINGS_REPORT.md))

1. **Full Gross-to-Net Payroll Reconciliation (180 Employees, 1,019 Monthly Statements):**
   - **Services Rendered:** **161,076.00 regular hours**, **139,726.96 billable hours** (**86.75%** utilization), and **4,516.45 overtime hours**.
   - **Gross Taxable Payroll:** **$10,739,234.81** = Base Service Pay (**$9,330,192.96**) + Overtime Pay (**$422,455.72**) + Bonuses (**$986,586.13**).
   - **TDS & Reimbursements:** **$2,278,391.77** withheld in Tax Deducted at Source (**21.22%** effective rate across `12%`, `18%`, `24%`, and `28%` statutory slabs, plus `2%` supplemental bonus withholding) and **$128,181.64** in approved non-taxable reimbursements (**96.65%** overall approval rate), resulting in **$8,589,024.68** net pay with **0 reconciliation errors**.
2. **Bonus vs. Work Duration Insight (~70% Longer Tenure):**
   - **Bonus Recipients ($n = 108$):** Average tenure of **41.56 months** and **89.81%** active retention rate (average total bonus **$9,135.06**).
   - **Non-Bonus Cohort ($n = 72$):** Average tenure of **24.46 months** and **72.22%** active retention rate.
   - **Relative Tenure Uplift:** Employees receiving performance/retention bonuses worked **+69.91% (~70%) longer** at the company than non-bonus peers, with a monotonic progression from **24.46 months** (`0 bonuses`) to **36.49 months** (`1 bonus`), **44.23 months** (`2 bonuses`), and **49.94 months** (`3+ bonuses`).
   - **Seniority Confounding Check:** Stratifying by job level (`L1` through `L4`) confirms positive within-level tenure uplift in every band (`L1: +52.00%`, `L2: +75.50%`, `L3: +72.62%`, `L4: +67.11%`).

---

## How to Run Locally

No external packages or database servers are required to run and test the project locally (uses Python 3 standard library `sqlite3`, `csv`, and `unittest`). The SQL files in `sql/` are also compatible with **MySQL 8.0**.

```bash
git clone https://github.com/iamprerana/payroll-financial-analysis.git
cd payroll-financial-analysis

# 1. Generate synthetic CSVs and SQLite database
python3 generate_data.py

# 2. Execute all 8 SQL analytical queries and build outputs/FINDINGS_REPORT.md
python3 analytics.py

# 3. Run automated unit and SQL reconciliation tests
python3 -m unittest discover -s tests -v
```
