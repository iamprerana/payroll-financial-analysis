-- ============================================================================
-- Financial Analysis for Payroll — MySQL 8.0 Relational Schema
-- Analyzes employee compensation based on services rendered:
-- Base salary prorated by service hours, overtime pay, bonuses,
-- Tax Deducted at Source (TDS), and expense reimbursements.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS payroll_analytics;
USE payroll_analytics;

DROP TABLE IF EXISTS payroll_statements;
DROP TABLE IF EXISTS reimbursement_claims;
DROP TABLE IF EXISTS bonus_awards;
DROP TABLE IF EXISTS service_logs;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    department_id VARCHAR(16) NOT NULL,
    department_name VARCHAR(80) NOT NULL,
    cost_center_code VARCHAR(20) NOT NULL,
    annual_budget_usd DECIMAL(14, 2) NOT NULL,
    PRIMARY KEY (department_id)
);

CREATE TABLE employees (
    employee_id VARCHAR(16) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    department_id VARCHAR(16) NOT NULL,
    job_title VARCHAR(80) NOT NULL,
    job_level VARCHAR(8) NOT NULL,
    employment_type VARCHAR(24) NOT NULL,
    hire_date DATE NOT NULL,
    exit_date DATE NULL,
    employment_status VARCHAR(16) NOT NULL,
    tenure_months DECIMAL(6, 1) NOT NULL,
    annual_base_salary DECIMAL(12, 2) NOT NULL,
    standard_monthly_hours INT NOT NULL,
    tax_bracket_pct DECIMAL(5, 2) NOT NULL,
    received_bonus_flag TINYINT(1) NOT NULL,
    bonus_count INT NOT NULL,
    PRIMARY KEY (employee_id),
    CONSTRAINT fk_employees_department
        FOREIGN KEY (department_id) REFERENCES departments (department_id)
);

CREATE TABLE service_logs (
    service_log_id VARCHAR(24) NOT NULL,
    employee_id VARCHAR(16) NOT NULL,
    pay_period VARCHAR(7) NOT NULL,
    standard_hours INT NOT NULL,
    regular_hours_worked DECIMAL(6, 2) NOT NULL,
    billable_service_hours DECIMAL(6, 2) NOT NULL,
    overtime_hours DECIMAL(6, 2) NOT NULL,
    overtime_multiplier DECIMAL(4, 2) NOT NULL,
    service_quality_score DECIMAL(4, 2) NOT NULL,
    PRIMARY KEY (service_log_id),
    UNIQUE KEY uq_employee_period (employee_id, pay_period),
    CONSTRAINT fk_service_employee
        FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
);

CREATE TABLE bonus_awards (
    bonus_id VARCHAR(24) NOT NULL,
    employee_id VARCHAR(16) NOT NULL,
    pay_period VARCHAR(7) NOT NULL,
    bonus_type VARCHAR(40) NOT NULL,
    bonus_amount DECIMAL(12, 2) NOT NULL,
    performance_rating VARCHAR(24) NOT NULL,
    PRIMARY KEY (bonus_id),
    CONSTRAINT fk_bonus_employee
        FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
);

CREATE TABLE reimbursement_claims (
    claim_id VARCHAR(24) NOT NULL,
    employee_id VARCHAR(16) NOT NULL,
    pay_period VARCHAR(7) NOT NULL,
    expense_category VARCHAR(40) NOT NULL,
    submitted_amount DECIMAL(12, 2) NOT NULL,
    approved_amount DECIMAL(12, 2) NOT NULL,
    is_tax_exempt TINYINT(1) NOT NULL,
    PRIMARY KEY (claim_id),
    CONSTRAINT fk_reimbursement_employee
        FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
);

CREATE TABLE payroll_statements (
    statement_id VARCHAR(24) NOT NULL,
    employee_id VARCHAR(16) NOT NULL,
    department_id VARCHAR(16) NOT NULL,
    pay_period VARCHAR(7) NOT NULL,
    regular_hours_worked DECIMAL(6, 2) NOT NULL,
    billable_service_hours DECIMAL(6, 2) NOT NULL,
    overtime_hours DECIMAL(6, 2) NOT NULL,
    hourly_base_rate DECIMAL(10, 2) NOT NULL,
    base_service_pay DECIMAL(12, 2) NOT NULL,
    overtime_pay DECIMAL(12, 2) NOT NULL,
    bonus_pay DECIMAL(12, 2) NOT NULL,
    gross_taxable_pay DECIMAL(12, 2) NOT NULL,
    tds_rate_pct DECIMAL(5, 2) NOT NULL,
    tds_deducted DECIMAL(12, 2) NOT NULL,
    reimbursements_approved DECIMAL(12, 2) NOT NULL,
    net_pay DECIMAL(12, 2) NOT NULL,
    PRIMARY KEY (statement_id),
    UNIQUE KEY uq_statement_employee_period (employee_id, pay_period),
    CONSTRAINT fk_payroll_employee
        FOREIGN KEY (employee_id) REFERENCES employees (employee_id),
    CONSTRAINT fk_payroll_department
        FOREIGN KEY (department_id) REFERENCES departments (department_id)
);

CREATE INDEX idx_employees_dept ON employees (department_id);
CREATE INDEX idx_employees_bonus ON employees (received_bonus_flag, tenure_months);
CREATE INDEX idx_service_period ON service_logs (pay_period);
CREATE INDEX idx_payroll_period ON payroll_statements (pay_period);
CREATE INDEX idx_payroll_dept ON payroll_statements (department_id);
