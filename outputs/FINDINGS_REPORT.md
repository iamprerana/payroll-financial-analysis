# Financial Analysis for Payroll — SQL Analytical Readout

> **Evidence & Data Note:** All figures in this report are computed by executing the SQL queries in [`sql/mysql_analysis_queries.sql`](../sql/mysql_analysis_queries.sql) against the deterministic synthetic payroll database (`seed = 20261020`, 180 employees, H1 2026 pay periods). No personal or employer payroll records are used. The bonus-to-tenure relationship represents an observational cohort association in the modeled data rather than a causal experiment.

## 1. Executive Summary & Payroll Reconciliation

- **Scope Analyzed:** **180 employees** across **6 departments** and **1,019 monthly payroll statements** (`2026-01` through `2026-06`).
- **Services Rendered:** **161,076.00 regular hours**, **139,726.96 billable client/project hours** (**86.75%** utilization), and **4,516.45 overtime hours**.
- **Gross Taxable Payroll:** **$10,739,234.81** = Base Service Pay (**$9,330,192.96**) + Overtime Pay (**$422,455.72**) + Performance & Retention Bonuses (**$986,586.13**).
- **Tax Deducted at Source (TDS) & Reimbursements:** **$2,278,391.77** withheld at an effective rate of **21.22%**, plus **$128,181.64** in non-taxable approved expense reimbursements, yielding **$8,589,024.68** in net take-home pay.
- **Reconciliation Integrity:** **0 gross-pay discrepancies** and **0 net-pay discrepancies** across all 1,019 statements.

## 2. Headline Retention & Tenure Insight (Bonus vs. Work Duration)

- **Bonus Recipients (108 employees):** Average work duration of **41.56 months** (active retention rate: **89.81%**, average bonus: **$9,135.06**).
- **Non-Bonus Cohort (72 employees):** Average work duration of **24.46 months** (active retention rate: **72.22%**).
- **Observed Uplift:** Employees receiving performance and milestone bonuses stayed **+69.91% longer** (~70% longer work duration) than employees without bonuses.

### Bonus Frequency Tier Breakdown

| Bonus Frequency Tier | Employees | Avg Bonus ($) | Avg Tenure (Months) | Active Retention (%) | Avg Service Quality | Avg Billable Hours |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0_No_Bonus | 72 | 0.00 | 24.46 | 72.22% | 3.85 | 717.5 |
| 1_Single_Spot_or_Annual_Bonus | 49 | 5,001.18 | 36.49 | 87.76% | 4.24 | 808.0 |
| 2_Dual_Performance_Bonuses | 43 | 10,683.98 | 44.23 | 93.02% | 4.24 | 825.8 |
| 3+_Multi_Cycle_Retention_and_Performance | 16 | 17,632.32 | 49.94 | 87.50% | 4.23 | 810.6 |

### Seniority-Controlled Check (Job Levels L1–L4)

To verify that the ~70% longer tenure is not merely an artifact of senior employees having both longer tenure and higher bonus eligibility, the SQL analysis stratifies by job level (`L1` through `L4`):

| Job Level | Bonus Recipient Tenure (Mo) | Non-Bonus Tenure (Mo) | Within-Level Tenure Uplift (%) | Bonus N | Non-Bonus N |
| --- | ---: | ---: | ---: | ---: | ---: |
| L1 | 27.18 | 17.88 | +52.00% | 25 | 19 |
| L2 | 40.70 | 23.19 | +75.50% | 42 | 25 |
| L3 | 48.38 | 28.03 | +72.62% | 28 | 19 |
| L4 | 57.34 | 34.31 | +67.11% | 13 | 9 |

## 3. Department Payroll & Cost per Billable Hour

| Department | Headcount | Avg Tenure (Mo) | Base Service Pay ($) | Overtime Pay ($) | Bonus Pay ($) | Gross Taxable ($) | TDS Withheld ($) | Reimbursements ($) | Net Disbursed ($) | Cost / Billable Hr ($) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Clinical Data Sciences | 30 | 34.5 | 1,620,540.64 | 89,273.26 | 166,129.97 | 1,875,943.87 | 391,315.72 | 20,818.96 | 1,505,447.11 | 81.18 |
| Platform Engineering | 30 | 33.9 | 1,555,863.40 | 89,055.77 | 184,898.12 | 1,829,817.29 | 372,150.06 | 19,197.55 | 1,476,864.78 | 81.97 |
| Client Delivery Services | 30 | 34.0 | 1,597,470.04 | 82,728.30 | 143,198.24 | 1,823,396.58 | 392,510.33 | 28,159.55 | 1,459,045.80 | 78.04 |
| Product & Decision Analytics | 30 | 36.7 | 1,586,128.88 | 49,173.93 | 148,316.51 | 1,783,619.32 | 381,503.96 | 20,320.95 | 1,422,436.31 | 77.65 |
| Finance & Payroll Operations | 30 | 34.1 | 1,555,432.00 | 58,035.31 | 154,806.80 | 1,768,274.11 | 379,611.16 | 19,450.74 | 1,408,113.69 | 73.54 |
| People & Talent Operations | 30 | 36.8 | 1,414,758.00 | 54,189.15 | 189,236.49 | 1,658,183.64 | 361,300.54 | 20,233.89 | 1,317,116.99 | 74.47 |

## 4. Tax Deducted at Source (TDS) Audit by Statutory Slab

| Tax Slab Group | Statutory Base Rate | Employees | Gross Taxable Pay ($) | Taxable Bonus ($) | TDS Deducted ($) | Effective TDS Rate (%) | Non-Taxable Reimbursements ($) | Net Pay ($) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10%-12% Entry Slab | 12.0% | 44 | 1,758,035.60 | 136,138.92 | 218,572.93 | 12.43% | 33,615.74 | 1,573,078.41 |
| 18% Mid Slab | 18.0% | 67 | 3,671,178.03 | 344,376.21 | 680,263.54 | 18.53% | 50,700.10 | 3,041,614.59 |
| 24% Senior Slab | 24.0% | 47 | 3,393,073.56 | 318,860.31 | 832,278.12 | 24.53% | 28,834.01 | 2,589,629.45 |
| 28%+ Executive Slab | 28.0% | 22 | 1,916,947.62 | 187,210.69 | 547,277.18 | 28.55% | 15,031.79 | 1,384,702.23 |

## 5. Expense Reimbursement Audit

| Expense Category | Claims | Claimants | Submitted ($) | Approved ($) | Disallowed Variance ($) | Approval Rate (%) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Client Travel & Lodging | 85 | 65 | 45,704.07 | 44,264.19 | 1,439.88 | 96.85% |
| Professional Certification & Training | 88 | 74 | 37,308.10 | 36,576.25 | 731.85 | 98.04% |
| Home Office & Ergonomic Equipment | 92 | 69 | 25,743.29 | 24,542.55 | 1,200.74 | 95.34% |
| Client Meals & Onsite Hospitality | 82 | 69 | 14,048.25 | 13,079.74 | 968.51 | 93.11% |
| Telecom & Data Connectivity | 103 | 79 | 9,820.64 | 9,718.91 | 101.73 | 98.96% |

