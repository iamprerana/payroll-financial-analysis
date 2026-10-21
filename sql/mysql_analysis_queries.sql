-- ============================================================================
-- Financial Analysis for Payroll — Analytical SQL Queries (MySQL 8.0 & SQLite)
-- Each query is tagged with `-- [QUERY: <name>]` so the automated pipeline and
-- test suite can execute and verify the exact SQL statements directly.
-- ============================================================================

-- [QUERY: employee_compensation_summary]
-- 1. Employee-level compensation reconciliation across FY 2026 based on
--    services rendered (regular hours, billable hours, overtime, bonuses,
--    Tax Deducted at Source [TDS], and approved expense reimbursements).
WITH employee_payroll_totals AS (
    SELECT
        p.employee_id,
        COUNT(DISTINCT p.pay_period) AS months_paid,
        ROUND(SUM(p.regular_hours_worked), 2) AS total_regular_hours,
        ROUND(SUM(p.billable_service_hours), 2) AS total_billable_hours,
        ROUND(SUM(p.overtime_hours), 2) AS total_overtime_hours,
        ROUND(SUM(p.base_service_pay), 2) AS total_base_service_pay,
        ROUND(SUM(p.overtime_pay), 2) AS total_overtime_pay,
        ROUND(SUM(p.bonus_pay), 2) AS total_bonus_pay,
        ROUND(SUM(p.gross_taxable_pay), 2) AS total_gross_taxable_pay,
        ROUND(SUM(p.tds_deducted), 2) AS total_tds_deducted,
        ROUND(SUM(p.reimbursements_approved), 2) AS total_reimbursements,
        ROUND(SUM(p.net_pay), 2) AS total_net_pay
    FROM payroll_statements p
    GROUP BY p.employee_id
)
SELECT
    e.employee_id,
    e.full_name,
    d.department_name,
    e.job_title,
    e.job_level,
    e.employment_status,
    e.tenure_months,
    t.months_paid,
    t.total_regular_hours,
    t.total_billable_hours,
    t.total_overtime_hours,
    t.total_base_service_pay,
    t.total_overtime_pay,
    t.total_bonus_pay,
    t.total_gross_taxable_pay,
    t.total_tds_deducted,
    ROUND(t.total_tds_deducted * 100.0 / NULLIF(t.total_gross_taxable_pay, 0), 2) AS effective_tds_rate_pct,
    t.total_reimbursements,
    t.total_net_pay,
    RANK() OVER (
        PARTITION BY e.department_id
        ORDER BY t.total_net_pay DESC
    ) AS dept_net_pay_rank
FROM employees e
INNER JOIN departments d
    ON e.department_id = d.department_id
INNER JOIN employee_payroll_totals t
    ON e.employee_id = t.employee_id
ORDER BY t.total_net_pay DESC, e.employee_id ASC;

-- [QUERY: department_payroll_breakdown]
-- 2. Department-level payroll financial analysis: base pay, overtime, bonuses,
--    TDS withheld, reimbursements, and total compensation cost per billable hour.
SELECT
    d.department_id,
    d.department_name,
    d.cost_center_code,
    COUNT(DISTINCT e.employee_id) AS headcount,
    ROUND(AVG(e.tenure_months), 2) AS avg_tenure_months,
    ROUND(SUM(p.regular_hours_worked), 2) AS regular_hours,
    ROUND(SUM(p.billable_service_hours), 2) AS billable_service_hours,
    ROUND(SUM(p.overtime_hours), 2) AS overtime_hours,
    ROUND(SUM(p.base_service_pay), 2) AS base_service_pay,
    ROUND(SUM(p.overtime_pay), 2) AS overtime_pay,
    ROUND(SUM(p.bonus_pay), 2) AS bonus_pay,
    ROUND(SUM(p.gross_taxable_pay), 2) AS gross_taxable_pay,
    ROUND(SUM(p.tds_deducted), 2) AS tds_deducted,
    ROUND(SUM(p.reimbursements_approved), 2) AS reimbursements_approved,
    ROUND(SUM(p.net_pay), 2) AS net_pay_disbursed,
    ROUND(
        (SUM(p.gross_taxable_pay) + SUM(p.reimbursements_approved))
        / NULLIF(SUM(p.billable_service_hours), 0),
        2
    ) AS total_cost_per_billable_hour
FROM departments d
INNER JOIN employees e
    ON d.department_id = e.department_id
INNER JOIN payroll_statements p
    ON e.employee_id = p.employee_id
GROUP BY d.department_id, d.department_name, d.cost_center_code
ORDER BY gross_taxable_pay DESC;

-- [QUERY: overtime_service_utilization]
-- 3. Monthly service utilization and overtime cost concentration across pay periods.
SELECT
    s.pay_period,
    COUNT(DISTINCT s.employee_id) AS active_employees_billed,
    SUM(s.standard_hours) AS scheduled_standard_hours,
    ROUND(SUM(s.regular_hours_worked), 2) AS regular_hours_worked,
    ROUND(SUM(s.billable_service_hours), 2) AS billable_service_hours,
    ROUND(
        SUM(s.billable_service_hours) * 100.0 / NULLIF(SUM(s.regular_hours_worked), 0),
        2
    ) AS billable_utilization_pct,
    ROUND(SUM(s.overtime_hours), 2) AS overtime_hours,
    ROUND(SUM(p.overtime_pay), 2) AS overtime_pay,
    ROUND(
        SUM(p.overtime_pay) * 100.0 / NULLIF(SUM(p.gross_taxable_pay), 0),
        2
    ) AS overtime_share_of_gross_pct,
    ROUND(AVG(s.service_quality_score), 2) AS avg_service_quality_score
FROM service_logs s
INNER JOIN payroll_statements p
    ON s.employee_id = p.employee_id
    AND s.pay_period = p.pay_period
GROUP BY s.pay_period
ORDER BY s.pay_period ASC;

-- [QUERY: tds_tax_bracket_summary]
-- 4. Tax Deducted at Source (TDS) audit across statutory withholding brackets.
SELECT
    CASE
        WHEN e.tax_bracket_pct <= 12.0 THEN '10%-12% Entry Slab'
        WHEN e.tax_bracket_pct <= 18.0 THEN '18% Mid Slab'
        WHEN e.tax_bracket_pct <= 24.0 THEN '24% Senior Slab'
        ELSE '28%+ Executive Slab'
    END AS tax_slab_group,
    e.tax_bracket_pct AS statutory_base_rate_pct,
    COUNT(DISTINCT e.employee_id) AS employee_count,
    ROUND(SUM(p.gross_taxable_pay), 2) AS total_gross_taxable_pay,
    ROUND(SUM(p.bonus_pay), 2) AS taxable_bonus_included,
    ROUND(SUM(p.tds_deducted), 2) AS total_tds_deducted,
    ROUND(
        SUM(p.tds_deducted) * 100.0 / NULLIF(SUM(p.gross_taxable_pay), 0),
        2
    ) AS realized_effective_tds_pct,
    ROUND(SUM(p.reimbursements_approved), 2) AS non_taxable_reimbursements,
    ROUND(SUM(p.net_pay), 2) AS total_net_pay
FROM employees e
INNER JOIN payroll_statements p
    ON e.employee_id = p.employee_id
GROUP BY tax_slab_group, e.tax_bracket_pct
ORDER BY e.tax_bracket_pct ASC;

-- [QUERY: reimbursement_category_summary]
-- 5. Expense reimbursement audit by category (submitted vs. approved amounts).
SELECT
    r.expense_category,
    COUNT(*) AS claim_count,
    COUNT(DISTINCT r.employee_id) AS distinct_claimants,
    ROUND(SUM(r.submitted_amount), 2) AS total_submitted_usd,
    ROUND(SUM(r.approved_amount), 2) AS total_approved_usd,
    ROUND(SUM(r.submitted_amount - r.approved_amount), 2) AS disallowed_variance_usd,
    ROUND(
        SUM(r.approved_amount) * 100.0 / NULLIF(SUM(r.submitted_amount), 0),
        2
    ) AS approval_rate_pct
FROM reimbursement_claims r
GROUP BY r.expense_category
ORDER BY total_approved_usd DESC;

-- [QUERY: bonus_tenure_comparison]
-- 6. Headline Retention Insight: Comparing duration of work (tenure in months)
--    and retention rates between bonus-receiving and non-bonus employees.
WITH cohort_stats AS (
    SELECT
        e.received_bonus_flag,
        CASE
            WHEN e.received_bonus_flag = 1 THEN 'Bonus Recipients'
            ELSE 'No Bonus Received'
        END AS bonus_cohort,
        COUNT(*) AS employee_count,
        ROUND(AVG(e.tenure_months), 2) AS avg_tenure_months,
        ROUND(MIN(e.tenure_months), 2) AS min_tenure_months,
        ROUND(MAX(e.tenure_months), 2) AS max_tenure_months,
        ROUND(
            SUM(CASE WHEN e.employment_status = 'Active' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
            2
        ) AS active_retention_rate_pct,
        ROUND(AVG(COALESCE(b.total_bonus_usd, 0)), 2) AS avg_bonus_per_employee_usd
    FROM employees e
    LEFT JOIN (
        SELECT
            employee_id,
            SUM(bonus_amount) AS total_bonus_usd
        FROM bonus_awards
        GROUP BY employee_id
    ) b
        ON e.employee_id = b.employee_id
    GROUP BY e.received_bonus_flag
),
baseline AS (
    SELECT avg_tenure_months AS non_bonus_avg_tenure
    FROM cohort_stats
    WHERE received_bonus_flag = 0
)
SELECT
    c.bonus_cohort,
    c.employee_count,
    c.avg_tenure_months,
    c.min_tenure_months,
    c.max_tenure_months,
    c.active_retention_rate_pct,
    c.avg_bonus_per_employee_usd,
    ROUND(
        (c.avg_tenure_months - b.non_bonus_avg_tenure) * 100.0
        / NULLIF(b.non_bonus_avg_tenure, 0),
        2
    ) AS tenure_uplift_vs_no_bonus_pct
FROM cohort_stats c
CROSS JOIN baseline b
ORDER BY c.received_bonus_flag DESC;

-- [QUERY: bonus_tier_tenure_breakdown]
-- 7. Granular bonus frequency/tier vs. tenure and service quality breakdown.
WITH employee_bonus_summary AS (
    SELECT
        e.employee_id,
        e.job_level,
        e.tenure_months,
        e.employment_status,
        e.bonus_count,
        COALESCE(SUM(b.bonus_amount), 0) AS total_bonus_usd
    FROM employees e
    LEFT JOIN bonus_awards b
        ON e.employee_id = b.employee_id
    GROUP BY
        e.employee_id,
        e.job_level,
        e.tenure_months,
        e.employment_status,
        e.bonus_count
),
employee_service_quality AS (
    SELECT
        employee_id,
        ROUND(AVG(service_quality_score), 2) AS avg_quality_score,
        ROUND(SUM(billable_service_hours), 2) AS total_billable_hours
    FROM service_logs
    GROUP BY employee_id
)
SELECT
    CASE
        WHEN ebs.bonus_count = 0 THEN '0_No_Bonus'
        WHEN ebs.bonus_count = 1 THEN '1_Single_Spot_or_Annual_Bonus'
        WHEN ebs.bonus_count = 2 THEN '2_Dual_Performance_Bonuses'
        ELSE '3+_Multi_Cycle_Retention_and_Performance'
    END AS bonus_frequency_tier,
    COUNT(*) AS employee_count,
    ROUND(AVG(ebs.total_bonus_usd), 2) AS avg_total_bonus_usd,
    ROUND(AVG(ebs.tenure_months), 2) AS avg_tenure_months,
    ROUND(
        SUM(CASE WHEN ebs.employment_status = 'Active' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS active_retention_rate_pct,
    ROUND(AVG(esq.avg_quality_score), 2) AS avg_service_quality_score,
    ROUND(AVG(esq.total_billable_hours), 2) AS avg_billable_hours
FROM employee_bonus_summary ebs
INNER JOIN employee_service_quality esq
    ON ebs.employee_id = esq.employee_id
GROUP BY bonus_frequency_tier
ORDER BY bonus_frequency_tier ASC;

-- [QUERY: level_controlled_tenure_check]
-- 8. Confounding Check: Tenure comparison by job level and bonus status
--    to verify that the bonus-tenure association holds within every seniority band.
SELECT
    e.job_level,
    ROUND(
        AVG(CASE WHEN e.received_bonus_flag = 1 THEN e.tenure_months END),
        2
    ) AS bonus_recipient_tenure_months,
    ROUND(
        AVG(CASE WHEN e.received_bonus_flag = 0 THEN e.tenure_months END),
        2
    ) AS non_bonus_tenure_months,
    ROUND(
        (
            AVG(CASE WHEN e.received_bonus_flag = 1 THEN e.tenure_months END)
            - AVG(CASE WHEN e.received_bonus_flag = 0 THEN e.tenure_months END)
        ) * 100.0
        / NULLIF(AVG(CASE WHEN e.received_bonus_flag = 0 THEN e.tenure_months END), 0),
        2
    ) AS within_level_tenure_uplift_pct,
    SUM(CASE WHEN e.received_bonus_flag = 1 THEN 1 ELSE 0 END) AS bonus_recipients_n,
    SUM(CASE WHEN e.received_bonus_flag = 0 THEN 1 ELSE 0 END) AS non_bonus_n
FROM employees e
GROUP BY e.job_level
ORDER BY e.job_level ASC;
