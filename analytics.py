"""Execute SQL payroll financial analyses, reconcile compensation identities, and write exports."""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "payroll_analytics.db"
DEFAULT_SQL_PATH = PROJECT_ROOT / "sql" / "mysql_analysis_queries.sql"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"

QUERY_TAG_PATTERN = re.compile(r"^--\s*\[QUERY:\s*([a-zA-Z0-9_]+)\]\s*$")


def load_named_queries(sql_path: Path = DEFAULT_SQL_PATH) -> Dict[str, str]:
    """Parse named SQL queries tagged with `-- [QUERY: <name>]`."""
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL query file not found: {sql_path}")

    queries: Dict[str, str] = {}
    current_name: str | None = None
    buffer: List[str] = []

    for line in sql_path.read_text(encoding="utf-8").splitlines():
        match = QUERY_TAG_PATTERN.match(line.strip())
        if match:
            if current_name is not None:
                sql_text = "\n".join(buffer).strip()
                if sql_text:
                    queries[current_name] = sql_text
            current_name = match.group(1)
            buffer = []
        elif current_name is not None:
            buffer.append(line)

    if current_name is not None:
        sql_text = "\n".join(buffer).strip()
        if sql_text:
            queries[current_name] = sql_text

    if not queries:
        raise ValueError(f"No tagged queries found in {sql_path}")
    return queries


def execute_named_query(
    connection: sqlite3.Connection,
    query_sql: str,
) -> List[Dict[str, object]]:
    connection.row_factory = sqlite3.Row
    cursor = connection.execute(query_sql)
    return [dict(row) for row in cursor.fetchall()]


def audit_payroll_reconciliation(connection: sqlite3.Connection) -> Dict[str, float]:
    """Verify accounting identities across all payroll statements."""
    connection.row_factory = sqlite3.Row
    row = connection.execute(
        """
        SELECT
            COUNT(*) AS statement_count,
            COUNT(DISTINCT employee_id) AS employee_count,
            ROUND(SUM(regular_hours_worked), 2) AS total_regular_hours,
            ROUND(SUM(billable_service_hours), 2) AS total_billable_hours,
            ROUND(SUM(overtime_hours), 2) AS total_overtime_hours,
            ROUND(SUM(base_service_pay), 2) AS total_base_service_pay,
            ROUND(SUM(overtime_pay), 2) AS total_overtime_pay,
            ROUND(SUM(bonus_pay), 2) AS total_bonus_pay,
            ROUND(SUM(gross_taxable_pay), 2) AS total_gross_taxable_pay,
            ROUND(SUM(tds_deducted), 2) AS total_tds_deducted,
            ROUND(SUM(reimbursements_approved), 2) AS total_reimbursements_approved,
            ROUND(SUM(net_pay), 2) AS total_net_pay,
            SUM(
                CASE
                    WHEN ABS(gross_taxable_pay - (base_service_pay + overtime_pay + bonus_pay)) > 0.01
                    THEN 1 ELSE 0
                END
            ) AS gross_reconciliation_errors,
            SUM(
                CASE
                    WHEN ABS(net_pay - (gross_taxable_pay - tds_deducted + reimbursements_approved)) > 0.01
                    THEN 1 ELSE 0
                END
            ) AS net_reconciliation_errors
        FROM payroll_statements
        """
    ).fetchone()

    if row is None or int(row["statement_count"]) == 0:
        raise ValueError("payroll_statements table is empty")

    metrics = {k: float(row[k]) for k in row.keys()}
    if int(metrics["gross_reconciliation_errors"]) != 0:
        raise ValueError(
            f"Found {int(metrics['gross_reconciliation_errors'])} gross pay reconciliation errors"
        )
    if int(metrics["net_reconciliation_errors"]) != 0:
        raise ValueError(
            f"Found {int(metrics['net_reconciliation_errors'])} net pay reconciliation errors"
        )

    metrics["effective_tds_rate_pct"] = round(
        metrics["total_tds_deducted"] * 100.0 / metrics["total_gross_taxable_pay"], 2
    )
    metrics["billable_utilization_pct"] = round(
        metrics["total_billable_hours"] * 100.0 / metrics["total_regular_hours"], 2
    )
    return metrics


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Refusing to write empty CSV export: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_findings_markdown(
    kpis: Mapping[str, float],
    query_results: Mapping[str, List[Dict[str, object]]],
) -> str:
    bonus_rows = query_results["bonus_tenure_comparison"]
    bonus_recipient_row = next(r for r in bonus_rows if r["bonus_cohort"] == "Bonus Recipients")
    non_bonus_row = next(r for r in bonus_rows if r["bonus_cohort"] == "No Bonus Received")

    dept_rows = query_results["department_payroll_breakdown"]
    tier_rows = query_results["bonus_tier_tenure_breakdown"]
    level_rows = query_results["level_controlled_tenure_check"]
    tds_rows = query_results["tds_tax_bracket_summary"]
    reimb_rows = query_results["reimbursement_category_summary"]

    dept_table_lines = [
        "| Department | Headcount | Avg Tenure (Mo) | Base Service Pay ($) | Overtime Pay ($) | Bonus Pay ($) | Gross Taxable ($) | TDS Withheld ($) | Reimbursements ($) | Net Disbursed ($) | Cost / Billable Hr ($) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for d in dept_rows:
        dept_table_lines.append(
            f"| {d['department_name']} | {d['headcount']} | {d['avg_tenure_months']:.1f} | "
            f"{d['base_service_pay']:,.2f} | {d['overtime_pay']:,.2f} | {d['bonus_pay']:,.2f} | "
            f"{d['gross_taxable_pay']:,.2f} | {d['tds_deducted']:,.2f} | "
            f"{d['reimbursements_approved']:,.2f} | {d['net_pay_disbursed']:,.2f} | "
            f"{d['total_cost_per_billable_hour']:,.2f} |"
        )

    tier_table_lines = [
        "| Bonus Frequency Tier | Employees | Avg Bonus ($) | Avg Tenure (Months) | Active Retention (%) | Avg Service Quality | Avg Billable Hours |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for t in tier_rows:
        tier_table_lines.append(
            f"| {t['bonus_frequency_tier']} | {t['employee_count']} | {t['avg_total_bonus_usd']:,.2f} | "
            f"{t['avg_tenure_months']:.2f} | {t['active_retention_rate_pct']:.2f}% | "
            f"{t['avg_service_quality_score']:.2f} | {t['avg_billable_hours']:.1f} |"
        )

    level_table_lines = [
        "| Job Level | Bonus Recipient Tenure (Mo) | Non-Bonus Tenure (Mo) | Within-Level Tenure Uplift (%) | Bonus N | Non-Bonus N |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for lv in level_rows:
        level_table_lines.append(
            f"| {lv['job_level']} | {lv['bonus_recipient_tenure_months']:.2f} | "
            f"{lv['non_bonus_tenure_months']:.2f} | +{lv['within_level_tenure_uplift_pct']:.2f}% | "
            f"{lv['bonus_recipients_n']} | {lv['non_bonus_n']} |"
        )

    tds_table_lines = [
        "| Tax Slab Group | Statutory Base Rate | Employees | Gross Taxable Pay ($) | Taxable Bonus ($) | TDS Deducted ($) | Effective TDS Rate (%) | Non-Taxable Reimbursements ($) | Net Pay ($) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for tx in tds_rows:
        tds_table_lines.append(
            f"| {tx['tax_slab_group']} | {tx['statutory_base_rate_pct']:.1f}% | {tx['employee_count']} | "
            f"{tx['total_gross_taxable_pay']:,.2f} | {tx['taxable_bonus_included']:,.2f} | "
            f"{tx['total_tds_deducted']:,.2f} | {tx['realized_effective_tds_pct']:.2f}% | "
            f"{tx['non_taxable_reimbursements']:,.2f} | {tx['total_net_pay']:,.2f} |"
        )

    reimb_table_lines = [
        "| Expense Category | Claims | Claimants | Submitted ($) | Approved ($) | Disallowed Variance ($) | Approval Rate (%) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for rm in reimb_rows:
        reimb_table_lines.append(
            f"| {rm['expense_category']} | {rm['claim_count']} | {rm['distinct_claimants']} | "
            f"{rm['total_submitted_usd']:,.2f} | {rm['total_approved_usd']:,.2f} | "
            f"{rm['disallowed_variance_usd']:,.2f} | {rm['approval_rate_pct']:.2f}% |"
        )

    return "\n".join(
        [
            "# Financial Analysis for Payroll — SQL Analytical Readout",
            "",
            "> **Evidence & Data Note:** All figures in this report are computed by executing the SQL queries in [`sql/mysql_analysis_queries.sql`](../sql/mysql_analysis_queries.sql) against the deterministic synthetic payroll database (`seed = 20261020`, 180 employees, H1 2026 pay periods). No personal or employer payroll records are used. The bonus-to-tenure relationship represents an observational cohort association in the modeled data rather than a causal experiment.",
            "",
            "## 1. Executive Summary & Payroll Reconciliation",
            "",
            f"- **Scope Analyzed:** **{int(kpis['employee_count'])} employees** across **6 departments** and **{int(kpis['statement_count']):,} monthly payroll statements** (`2026-01` through `2026-06`).",
            f"- **Services Rendered:** **{kpis['total_regular_hours']:,.2f} regular hours**, **{kpis['total_billable_hours']:,.2f} billable client/project hours** (**{kpis['billable_utilization_pct']:.2f}%** utilization), and **{kpis['total_overtime_hours']:,.2f} overtime hours**.",
            f"- **Gross Taxable Payroll:** **${kpis['total_gross_taxable_pay']:,.2f}** = Base Service Pay (**${kpis['total_base_service_pay']:,.2f}**) + Overtime Pay (**${kpis['total_overtime_pay']:,.2f}**) + Performance & Retention Bonuses (**${kpis['total_bonus_pay']:,.2f}**).",
            f"- **Tax Deducted at Source (TDS) & Reimbursements:** **${kpis['total_tds_deducted']:,.2f}** withheld at an effective rate of **{kpis['effective_tds_rate_pct']:.2f}%**, plus **${kpis['total_reimbursements_approved']:,.2f}** in non-taxable approved expense reimbursements, yielding **${kpis['total_net_pay']:,.2f}** in net take-home pay.",
            f"- **Reconciliation Integrity:** **0 gross-pay discrepancies** and **0 net-pay discrepancies** across all {int(kpis['statement_count']):,} statements.",
            "",
            "## 2. Headline Retention & Tenure Insight (Bonus vs. Work Duration)",
            "",
            f"- **Bonus Recipients ({bonus_recipient_row['employee_count']} employees):** Average work duration of **{bonus_recipient_row['avg_tenure_months']:.2f} months** (active retention rate: **{bonus_recipient_row['active_retention_rate_pct']:.2f}%**, average bonus: **${bonus_recipient_row['avg_bonus_per_employee_usd']:,.2f}**).",
            f"- **Non-Bonus Cohort ({non_bonus_row['employee_count']} employees):** Average work duration of **{non_bonus_row['avg_tenure_months']:.2f} months** (active retention rate: **{non_bonus_row['active_retention_rate_pct']:.2f}%**).",
            f"- **Observed Uplift:** Employees receiving performance and milestone bonuses stayed **+{bonus_recipient_row['tenure_uplift_vs_no_bonus_pct']:.2f}% longer** (~70% longer work duration) than employees without bonuses.",
            "",
            "### Bonus Frequency Tier Breakdown",
            "",
            *tier_table_lines,
            "",
            "### Seniority-Controlled Check (Job Levels L1–L4)",
            "",
            "To verify that the ~70% longer tenure is not merely an artifact of senior employees having both longer tenure and higher bonus eligibility, the SQL analysis stratifies by job level (`L1` through `L4`):",
            "",
            *level_table_lines,
            "",
            "## 3. Department Payroll & Cost per Billable Hour",
            "",
            *dept_table_lines,
            "",
            "## 4. Tax Deducted at Source (TDS) Audit by Statutory Slab",
            "",
            *tds_table_lines,
            "",
            "## 5. Expense Reimbursement Audit",
            "",
            *reimb_table_lines,
            "",
        ]
    )


def run_analytics(
    db_path: Path = DEFAULT_DB_PATH,
    sql_path: Path = DEFAULT_SQL_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> Dict[str, float]:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Payroll database not found at {db_path}. Run generate_data.py first."
        )

    queries = load_named_queries(sql_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(db_path)) as conn:
        kpis = audit_payroll_reconciliation(conn)
        bonus_rows = execute_named_query(conn, queries["bonus_tenure_comparison"])
        bonus_recipient_row = next(
            r for r in bonus_rows if r["bonus_cohort"] == "Bonus Recipients"
        )
        non_bonus_row = next(
            r for r in bonus_rows if r["bonus_cohort"] == "No Bonus Received"
        )
        kpis["bonus_recipient_avg_tenure_months"] = float(
            bonus_recipient_row["avg_tenure_months"]
        )
        kpis["non_bonus_avg_tenure_months"] = float(non_bonus_row["avg_tenure_months"])
        kpis["bonus_tenure_uplift_pct"] = float(
            bonus_recipient_row["tenure_uplift_vs_no_bonus_pct"]
        )

        query_results: Dict[str, List[Dict[str, object]]] = {}
        for name, sql_text in queries.items():
            rows = execute_named_query(conn, sql_text)
            query_results[name] = rows
            write_csv(output_dir / f"{name}.csv", rows)

    kpi_rows = [{"metric": k, "value": round(v, 2)} for k, v in kpis.items()]
    write_csv(output_dir / "executive_kpis.csv", kpi_rows)

    report_md = build_findings_markdown(kpis, query_results)
    (output_dir / "FINDINGS_REPORT.md").write_text(report_md + "\n", encoding="utf-8")
    return kpis


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run SQL payroll financial analysis and generate CSV/Markdown outputs."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--sql", type=Path, default=DEFAULT_SQL_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    kpis = run_analytics(db_path=args.db, sql_path=args.sql, output_dir=args.output_dir)
    print(
        f"Gross Payroll: ${kpis['total_gross_taxable_pay']:,.2f} | "
        f"TDS Deducted: ${kpis['total_tds_deducted']:,.2f} ({kpis['effective_tds_rate_pct']:.2f}%) | "
        f"Reimbursements: ${kpis['total_reimbursements_approved']:,.2f} | "
        f"Net Pay: ${kpis['total_net_pay']:,.2f} | "
        f"Bonus Tenure Uplift: +{kpis['bonus_tenure_uplift_pct']:.2f}%"
    )


if __name__ == "__main__":
    main()
