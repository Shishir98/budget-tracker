# Bugs Resolved

This file contains a comprehensive list of all bugs that have been identified **TILL NOW** and resolved in the application. This serves as context for future development to prevent regressions.

## 1. Transaction Deletion and Redirection
- **Issue:** Deleting a transaction failed on the transactions page. This was caused by nested HTML forms stemming from the bulk-categorization feature, which interfered with individual delete actions. Furthermore, after a deletion, the application didn't preserve the user's filters and pagination state.
- **Resolution:** Fixed the nested HTML form issues to allow individual delete actions. Ensured the application correctly redirects the user back to their previous page with the original filters and pagination state preserved.

## 2. Investment Calculation Discrepancies
- **Issue:** The "Invested" and "Current Value" calculations on the dashboard were inaccurate (e.g., reporting 54,000 instead of an expected ~30,000). This was due to aggregation logic errors causing transaction amounts to double-count or incorrectly include non-investment data.
- **Resolution:** Fixed the aggregation logic in the `dashboard.py` and `investments.py` views to accurately calculate and reflect the portfolio's total invested capital and current value.

## 3. Recurring Investment Synchronization
- **Issue:** Recurring investments were only being processed and refreshed locally on the dashboard rather than globally across the application. Additionally, the transactions automatically generated from these recurring investments were appearing unlabelled.
- **Resolution:** Updated the recurring investment logic to ensure global processing and refreshing. Fixed the generation logic so that auto-generated transactions are correctly labeled as "Investment" by default.

## 4. Recurring Transaction Schedule Creation
- **Issue:** The automatic deduction system for recurring investments and subscriptions was failing. A logic error prevented background schedules from being created when a user marked a new transaction as "Recurring", so the parent `Investment` or `Subscription` records weren't generated.
- **Resolution:** Resolved the logic error so that marking a transaction as "Recurring" properly creates the required parent records and schedules. This allows the `process_auto_deductions` function to effectively generate follow-up transactions on their scheduled dates.

## 5. Analytics Trend Calculation Anchor
- **Issue:** The financial trend charts on the Analytics page were hardcoded to show data relative to the current date (`today`), regardless of the user's selected month or year in the period selector.
- **Resolution:** Updated the trend logic in `analytics.py` to use the user's selected date (the end of the selected period) as the anchor for historical data calculation. Additionally, ensured the month selector is hidden in "Quarter" and "Year" modes to reduce UI clutter and improve clarity.

---
*Last Updated: 2026-04-26 (Analytics Trend Anchor Fix)*
