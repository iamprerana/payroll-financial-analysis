"""Automated unit tests for the Payroll Financial Analysis SQL project."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analytics import (  # noqa: E402
    audit_payroll_reconciliation,
    execute_named_query,
    load_named_queries,
    run_analytics,
)
from generate_data import (  # noqa: E402
    create_sqlite_database,
    generate_dataset,
    write_mysql_seed_file,
)


class PayrollFinancialAnalysisTests(unittest.TestCase):
    def test_generator_is_deterministic_and_stratified(self) -> None:
        first = generate_dataset(employee_count=60, seed=42)
        second = generate_dataset(employee_count=60, seed=42)
        self.assertEqual(first, second)
        self.assertEqual(len(first["departments"]), 6)
        self.assertEqual(len(first["employees"]), 60)
        self.assertGreater(len(first["service_logs"]), 300)
        self.assertGreater(len(first["bonus_awards"]), 30)
        self.assertGreater(len(first["reimbursement_claims"]), 80)
        self.assertEqual(
            len(first["service_logs"]),
            len(first["payroll_statements"]),
        )

    def test_every_statement_reconciles_gross_tds_reimbursements_and_net(self) -> None:
        dataset = generate_dataset(employee_count=180)
        for row in dataset["payroll_statements"]:
            base_pay = float(row["base_service_pay"])
            overtime_pay = float(row["overtime_pay"])
            bonus_pay = float(row["bonus_pay"])
            gross_pay = float(row["gross_taxable_pay"])
            tds_rate = float(row["tds_rate_pct"])
            tds_deducted = float(row["tds_deducted"])
            reimb = float(row["reimbursements_approved"])
            net_pay = float(row["net_pay"])

            self.assertAlmostEqual(
                gross_pay,
                round(base_pay + overtime_pay + bonus_pay, 2),
                places=2,
            )
            self.assertAlmostEqual(
                tds_deducted,
                round(gross_pay * (tds_rate / 100.0), 2),
                places=2,
            )
            self.assertAlmostEqual(
                net_pay,
                round(gross_pay - tds_deducted + reimb, 2),
                places=2,
            )

    def test_all_sql_queries_execute_and_confirm_70_percent_bonus_tenure_insight(self) -> None:
        queries = load_named_queries()
        expected_queries = {
            "employee_compensation_summary",
            "department_payroll_breakdown",
            "overtime_service_utilization",
            "tds_tax_bracket_summary",
            "reimbursement_category_summary",
            "bonus_tenure_comparison",
            "bonus_tier_tenure_breakdown",
            "level_controlled_tenure_check",
        }
        self.assertEqual(set(queries.keys()), expected_queries)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "payroll_analytics.db"
            out_dir = root / "outputs"
            dataset = generate_dataset(employee_count=180)
            create_sqlite_database(dataset, db_path)

            kpis = run_analytics(db_path=db_path, output_dir=out_dir)
            self.assertEqual(int(kpis["gross_reconciliation_errors"]), 0)
            self.assertEqual(int(kpis["net_reconciliation_errors"]), 0)
            # Verify the ~70% longer tenure insight for bonus recipients
            self.assertAlmostEqual(kpis["bonus_tenure_uplift_pct"], 69.91, delta=1.5)

            with sqlite3.connect(str(db_path)) as conn:
                reconciliation = audit_payroll_reconciliation(conn)
                self.assertEqual(int(reconciliation["employee_count"]), 180)
                level_rows = execute_named_query(
                    conn, queries["level_controlled_tenure_check"]
                )
                self.assertEqual(len(level_rows), 4)
                for lv in level_rows:
                    self.assertGreater(float(lv["within_level_tenure_uplift_pct"]), 45.0)

            for query_name in expected_queries:
                self.assertTrue((out_dir / f"{query_name}.csv").exists())
            self.assertTrue((out_dir / "executive_kpis.csv").exists())
            self.assertTrue((out_dir / "FINDINGS_REPORT.md").exists())

            seed_path = root / "mysql_seed_data.sql"
            write_mysql_seed_file(dataset, seed_path)
            self.assertTrue(seed_path.exists())
            seed_text = seed_path.read_text(encoding="utf-8")
            self.assertIn("INSERT INTO payroll_statements", seed_text)
            self.assertIn("INSERT INTO employees", seed_text)

    def test_project_guides_and_interactive_html_exist(self) -> None:
        guide_md = PROJECT_ROOT / "PROJECT_GUIDE_AND_NEXT_STEPS.md"
        interactive_html = PROJECT_ROOT / "interactive_project_guide.html"
        self.assertTrue(guide_md.exists())
        self.assertTrue(interactive_html.exists())
        html_text = interactive_html.read_text(encoding="utf-8")
        self.assertIn("Gross-to-Net Payroll Simulator", html_text)
        self.assertIn("bonus_tenure_comparison", html_text)


if __name__ == "__main__":
    unittest.main()
