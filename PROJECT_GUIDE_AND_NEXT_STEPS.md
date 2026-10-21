# Payroll Financial Analysis — Complete Project Guide, Architecture & Future Suggestions

## 1. Is the Project Fully Complete?

**Yes.** Every component of the **Financial Analysis for Payroll (SQL)** project is implemented, executed, and verified with automated tests inside `payroll-financial-analysis/`:

| Component | Status | File(s) | What It Does |
| --- | --- | --- | --- |
| **MySQL 8.0 Database Schema** | Complete | [`sql/mysql_schema.sql`](./sql/mysql_schema.sql) | Defines 6 normalized relational tables (`departments`, `employees`, `service_logs`, `bonus_awards`, `reimbursement_claims`, `payroll_statements`) with primary/foreign keys, `DECIMAL` financial types, and composite indexes. |
| **MySQL 8.0 Seed Script** | Complete | [`sql/mysql_seed_data.sql`](./sql/mysql_seed_data.sql) | Self-contained `INSERT INTO ... VALUES` script (309 KB) loading all 180 employees, 1,019 service logs, 183 bonus awards, 450 reimbursement claims, and 1,019 payroll statements directly into MySQL 8. |
| **8 Production SQL Analysis Queries** | Complete | [`sql/mysql_analysis_queries.sql`](./sql/mysql_analysis_queries.sql) | ANSI SQL compatible with **both MySQL 8.0 and SQLite 3**, using CTEs (`WITH`), window functions (`RANK() OVER`), `CASE` expressions, `NULLIF` zero-division guards, and multi-table `INNER`/`LEFT`/`CROSS` joins. |
| **Deterministic Data & DB Generator** | Complete | [`generate_data.py`](./generate_data.py) | Uses `seed = 20261020` (Python standard library only) to generate raw CSVs in [`data/`](./data), build the local SQLite database [`data/payroll_analytics.db`](./data/payroll_analytics.db), and write [`sql/mysql_seed_data.sql`](./sql/mysql_seed_data.sql). |
| **SQL Analytics & Reconciliation Engine** | Complete | [`analytics.py`](./analytics.py) | Parses each `-- [QUERY: <name>]` block from [`sql/mysql_analysis_queries.sql`](./sql/mysql_analysis_queries.sql), executes them against the database, audits every payroll row for cent-exact gross/TDS/reimbursement/net reconciliation, and writes 9 CSV tables + [`outputs/FINDINGS_REPORT.md`](./outputs/FINDINGS_REPORT.md). |
| **Interactive Learning & Architecture Guide** | Complete | [`interactive_project_guide.html`](./interactive_project_guide.html) | Browser-based interactive learning app showing how all technologies bind together, an interactive ER diagram, SQL query stepper, live Gross-to-Net & TDS calculator, Bonus-vs-Tenure explorer, and self-test quiz. |
| **Automated Unit & SQL Test Suite** | Complete | [`tests/test_payroll_analytics.py`](./tests/test_payroll_analytics.py) | Verifies deterministic generation, cent-exact accounting identities across all 1,019 statements, execution of all 8 SQL queries, and the ~70% (+69.91%) bonus-tenure insight. |

---

## 2. Full Instructions on How to Run

### Option A: Zero-Setup Local Run (Recommended — Uses Built-in Python 3 & SQLite)

No third-party packages or database servers are needed. Run these commands from your terminal:

```bash
cd payroll-financial-analysis

# Step 1: Generate all CSVs, SQLite database (data/payroll_analytics.db), and MySQL seed file
python3 generate_data.py

# Step 2: Execute all 8 SQL queries, run reconciliation checks, and generate outputs/FINDINGS_REPORT.md
python3 analytics.py

# Step 3: Run the automated unit test suite
python3 -m unittest discover -s tests -v
```

### Option B: Running Directly in MySQL 8.0 (CLI, MySQL Workbench, or Docker)

If you have a local MySQL 8.0 server or Docker container:

```bash
cd payroll-financial-analysis

# 1. Create the payroll_analytics database and 6 tables
mysql -u root -p < sql/mysql_schema.sql

# 2. Load the deterministic synthetic records into MySQL
mysql -u root -p payroll_analytics < sql/mysql_seed_data.sql

# 3. Run the 8 analytical SQL queries
mysql -u root -p payroll_analytics < sql/mysql_analysis_queries.sql
```

### Option C: Interactive SQL Exploration via Command-Line `sqlite3`

You can also run ad-hoc SQL queries directly in your terminal using macOS's built-in `sqlite3` CLI:

```bash
cd payroll-financial-analysis
sqlite3 -header -column data/payroll_analytics.db < sql/mysql_analysis_queries.sql
```

### Option D: Open the Interactive HTML Learning Guide

Open [`interactive_project_guide.html`](./interactive_project_guide.html) in any browser:

```bash
open interactive_project_guide.html
```

---

## 3. How the Technologies Are Bound Together

This project uses a **Single-Source-of-Truth SQL Architecture** so that the SQL files are never "dead documentation"—the Python pipeline actually parses and executes the exact `.sql` file:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. DATA GENERATION LAYER (generate_data.py, seed = 20261020)            │
│    • Simulates 6 departments, 180 employees (L1–L4), and H1 2026 logs   │
│    • Computes hourly_base_rate, base_service_pay, overtime_pay,         │
│      bonus_pay, gross_taxable_pay, tds_deducted, reimbursements, net    │
└───────────────┬──────────────────────────┬──────────────────────────────┘
                │                          │
                ▼                          ▼
┌──────────────────────────────┐  ┌───────────────────────────────────────┐
│ 2A. LOCAL SQLITE & CSV STORE │  │ 2B. MYSQL 8.0 ARTIFACTS               │
│ • data/payroll_analytics.db  │  │ • sql/mysql_schema.sql (DDL)          │
│ • data/*.csv (6 raw tables)  │  │ • sql/mysql_seed_data.sql (INSERTs)   │
└───────────────┬──────────────┘  └───────────────────┬───────────────────┘
                │                                     │
                └──────────────────┬──────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. SHARED SQL ANALYTICAL LAYER (sql/mysql_analysis_queries.sql)         │
│    • 8 tagged queries (`-- [QUERY: <name>]`) written in portable SQL    │
│    • Uses CTEs, RANK() OVER window functions, CASE slabs, NULLIF guards │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. EXECUTION, AUDIT & REPORTING LAYER (analytics.py)                    │
│    • Parses `-- [QUERY: <name>]` blocks from mysql_analysis_queries.sql │
│    • Runs audit_payroll_reconciliation() to verify 0 cent-level drift   │
│    • Exports 9 CSVs + outputs/FINDINGS_REPORT.md                        │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. AUTOMATED VERIFICATION LAYER (tests/test_payroll_analytics.py)       │
│    • Re-runs generator & SQL queries in an isolated temp directory      │
│    • Asserts 0 accounting errors and verifies +69.91% (~70%) uplift     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Walkthrough of the Payroll Math & SQL Logic

### A. Gross-to-Net Payroll Formulas (Per Employee, Per Pay Period)

1. **Hourly Base Rate from Annual Salary:**
   $$\text{Hourly Base Rate} = \text{ROUND}\left(\frac{\text{Annual Base Salary} / 12}{\text{Standard Monthly Hours (160)}},\ 2\right)$$
2. **Base Service Pay (Prorated by Regular Hours Rendered):**
   $$\text{Base Service Pay} = \text{ROUND}(\text{Regular Hours Worked} \times \text{Hourly Base Rate},\ 2)$$
3. **Overtime Pay (Tiered Multiplier: `1.50x` up to 12 hrs, `1.75x` above 12 hrs):**
   $$\text{Overtime Pay} = \text{ROUND}(\text{Overtime Hours} \times \text{Hourly Base Rate} \times \text{Overtime Multiplier},\ 2)$$
4. **Gross Taxable Pay:**
   $$\text{Gross Taxable Pay} = \text{Base Service Pay} + \text{Overtime Pay} + \text{Bonus Pay}$$
5. **Tax Deducted at Source (TDS):**
   - Base statutory brackets by job level/income: **12.0%** (`L1`), **18.0%** (`L2`), **24.0%** (`L3`), **28.0%** (`L4`).
   - When a bonus is disbursed in a pay period, a **+2.0% supplemental withholding rate** applies to that period's gross taxable pay.
   $$\text{TDS Deducted} = \text{ROUND}\left(\text{Gross Taxable Pay} \times \frac{\text{TDS Rate \%}}{100},\ 2\right)$$
6. **Net Take-Home Pay (Including Non-Taxable Approved Reimbursements):**
   $$\text{Net Pay} = \text{Gross Taxable Pay} - \text{TDS Deducted} + \text{Approved Reimbursements}$$

### B. How the 8 SQL Queries Work (`sql/mysql_analysis_queries.sql`)

1. **`employee_compensation_summary`**: Uses a CTE (`WITH employee_payroll_totals AS (...)`) to aggregate each employee's H1 2026 hours, base pay, overtime, bonuses, gross taxable pay, TDS, reimbursements, and net pay, then joins `employees` and `departments` and applies `RANK() OVER (PARTITION BY e.department_id ORDER BY t.total_net_pay DESC)` to rank earners within each department.
2. **`department_payroll_breakdown`**: Aggregates compensation components by department and computes **Total Cost per Billable Service Hour**:
   $$\frac{\sum \text{Gross Taxable Pay} + \sum \text{Approved Reimbursements}}{\sum \text{Billable Service Hours}}$$
3. **`overtime_service_utilization`**: Tracks monthly billable utilization ($\text{Billable Hours} / \text{Regular Hours}$) and overtime cost share ($\text{Overtime Pay} / \text{Gross Taxable Pay}$) across `2026-01` through `2026-06`.
4. **`tds_tax_bracket_summary`**: Uses a `CASE` expression to group employees into statutory tax slabs (`10%-12% Entry Slab`, `18% Mid Slab`, `24% Senior Slab`, `28%+ Executive Slab`) and compares statutory base rates against realized effective TDS rates (which are ~0.43 to 0.55 percentage points higher due to supplemental bonus withholding).
5. **`reimbursement_category_summary`**: Audits submitted vs. approved expense claims across 5 categories (`Client Travel & Lodging`, `Professional Certification & Training`, `Home Office & Ergonomic Equipment`, `Client Meals & Onsite Hospitality`, `Telecom & Data Connectivity`) to quantify policy disallowances.
6. **`bonus_tenure_comparison`**: Joins `employees` with aggregated `bonus_awards` in a `cohort_stats` CTE and `CROSS JOIN`s a `baseline` CTE (`WHERE received_bonus_flag = 0`) to calculate the exact percentage uplift in work duration:
   $$\frac{41.56 - 24.46}{24.46} \times 100 = +69.91\% \approx +70\%$$
7. **`bonus_tier_tenure_breakdown`**: Segments employees into 4 bonus frequency tiers (`0_No_Bonus`, `1_Single_Spot_or_Annual_Bonus`, `2_Dual_Performance_Bonuses`, `3+_Multi_Cycle_Retention_and_Performance`) and joins average service quality scores and billable hours.
8. **`level_controlled_tenure_check`**: Uses conditional aggregation (`AVG(CASE WHEN e.received_bonus_flag = 1 THEN e.tenure_months END)`) grouped by `job_level` (`L1`–`L4`) to prove that the bonus-tenure uplift holds within every seniority band (`+52.00%` in `L1`, `+75.50%` in `L2`, `+72.62%` in `L3`, `+67.11%` in `L4`), ruling out simple seniority confounding.

---

## 5. Suggestions & Roadmap for Future Extensions

If you want to expand this project further for advanced Data Science, Analytics Engineering, or BI interviews, here are 5 high-impact extensions you can build next:

### Suggestion 1: Survival Analysis & Censored Tenure Modeling (Python `lifelines`)
- **Why:** In real HR/People Analytics datasets, active employees have *right-censored* tenure (we know their tenure *so far*, not when they will eventually leave).
- **What to add:**
  - Fit a **Kaplan-Meier survival curve** comparing `received_bonus_flag = 1` vs. `0` using `tenure_months` as duration and `employment_status == 'Separated'` as the event indicator.
  - Fit a **Cox Proportional Hazards model** controlling for `job_level`, `department_id`, `annual_base_salary`, and `overtime_hours` to estimate the hazard ratio of receiving bonuses on attrition risk.

### Suggestion 2: Interactive Streamlit or React Executive Dashboard
- **Why:** Complements the SQL backend with a self-serve UI for Finance and HR business partners.
- **What to add:**
  - Filters for `Pay Period`, `Department`, and `Job Level`.
  - A **Gross-to-Net Waterfall Chart** (`Base Pay -> +Overtime -> +Bonus -> -TDS -> +Reimbursements -> =Net Pay`).
  - An **Overtime vs. Attrition Scatter Plot** highlighting burnout risk when monthly overtime exceeds 12 hours without bonus recognition.

### Suggestion 3: Temporal Causal Ordering & Lagged Panel Analysis
- **Why:** In observational compensation data, longer tenure also gives employees more time to receive bonuses (*reverse causality*).
- **What to add:**
  - Track **first-year bonus receipt** (whether an employee received a bonus within their first 12 months of hire) and measure **subsequent 24-month retention** to separate the effect of early bonus recognition from time-at-risk.

### Suggestion 4: Payroll Anomaly Detection & Audit Flags SQL View
- **Why:** Payroll operations teams run pre-disbursement audit checks before releasing bank wires.
- **What to add:**
  - Create a SQL view `vw_payroll_audit_exceptions` flagging:
    1. Employees with `overtime_hours > 14` in consecutive months
    2. Reimbursement claims where `submitted_amount - approved_amount > $50`
    3. Statements where effective TDS deviates from statutory bracket by more than `2.5%`.

### Suggestion 5: Slowly Changing Dimensions (SCD Type 2) for Promotions & Salary Revisions
- **Why:** Demonstrates data warehousing / Analytics Engineering maturity (`dbt` style).
- **What to add:**
  - Add an `employee_compensation_history` table with `effective_start_date`, `effective_end_date`, and `is_current` so mid-year promotions from `L1 -> L2` automatically prorate salary and tax brackets across pay periods.
