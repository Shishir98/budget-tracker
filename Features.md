# Budget Tracker Features

This document outlines the core features and capabilities of the Budget Tracker application as identified from the codebase.

## 1. Dashboard & Overview
*   **Financial Summary**: Real-time overview of total income, expenses, investments, and net savings for the current period.
*   **Quick Access**: Fast-entry modal buttons for adding transactions from any page.
*   **Mobile Optimized**: Responsive design that adapts the layout for mobile devices (e.g., hiding non-essential panels to save space).
*   **Background Automation**: Recurring transactions and auto-deductions are processed automatically in the background via middleware.
*   **Transaction Calendar**: A full monthly calendar rendered at the bottom of the dashboard. Each date cell shows colored dot indicators for that day's transaction types (green = Income, red = Expense, purple = Investment). Today's date is highlighted with a filled circle. 
    *   **Interactive Details**: Clicking a date shows a minimalist popover listing that day's transactions (notes and amounts). 
    *   **Quick Navigation**: Clicking the same date again or clicking the "View All" link in the popover navigates to the transactions page pre-filtered for that specific date.

## 2. Transaction Management
*   **Multi-type Tracking**: Support for Income, Expenses, Side Income, and Investments.
*   **Advanced Filtering & Search**: Filter transactions by keyword (notes/raw description), date ranges, categories, transaction types, 'unlabeled' status, and 'subscription' status. Stable pagination is included for large datasets.
*   **Smart Categorization**: Custom categories with unique colors and icons. Categories can automatically flag transactions as subscriptions.
*   **Bulk Actions**: Capability to select and categorize multiple unlabeled transactions at once.
*   **Smart PDF Import**: Upload and parse bank statements or transaction PDFs (Currently supports ICICI and HDFC banks). The system uses heuristics to automatically guess transaction categories and types based on descriptions, providing a preview interface before importing.

## 3. Investment Portfolio
*   **Asset Management**: Track different types of investments (Fixed Deposits, Stocks, Mutual Funds, etc.).
*   **Custom Investment Types**: Create custom investment buckets and define whether they feature maturity dates or interest rates.
*   **Performance Metrics**: 
    *   Calculation of Profit/Loss and ROI (Return on Investment) percentage.
    *   Expected value at maturity based on interest rates.
    *   Days remaining until maturity.
*   **Hybrid Portfolio Tracking**: Consolidates explicitly tracked active investments and ad-hoc/unlinked investment transactions into a unified net worth and allocation view.
*   **Recurring Investments**: Automate tracking for monthly/quarterly investment contributions.

## 4. Budgeting & Limits
*   **Monthly Limits**: Set spending targets for specific categories (e.g., "Dining Out", "Shopping") or an overall global limit.
*   **Utilization Alerts**: Automatically calculates the percentage of the budget consumed and flags categories that are over budget.
*   **Custom Cycles**: Define a "Month Start Day" (e.g., the 5th of every month) to align with salary cycles.

## 5. Analytics & Insights
*   **Financial Trends**: Stacked bar and line charts showing 6-12 month trends for income vs. expenses vs. investments.
*   **Burn Rate & Runway**: 
    *   **Burn Rate**: Calculation of average monthly spending based on recent history.
    *   **Runway**: Estimation of how many months current cash reserves will last based on the burn rate.
*   **MoM Comparison**: Month-over-month analysis identifying significant changes in spending behavior.
*   **Distribution Charts**: Doughnut charts for Expense, Income, and Investment portfolio allocation.
*   **Periodic Filtering**: View analytics by Month, Quarter, or Year. Includes specialized month/year selectors and navigation buttons (consistent with the Dashboard) to easily explore historical data.

## 6. Subscription Tracking
*   **Recurring Bills**: Manage Netflix, Gym, Rent, and other subscriptions in one place.
*   **Billing Cycles**: Support for Monthly, Quarterly, and Yearly billing.
*   **Payment History**: Automatically links and tracks actual payment transactions against planned subscriptions.
*   **Upcoming Alerts**: Track days until the next billing date.
*   **Monthly Equivalent**: Normalizes all subscriptions (e.g., yearly bills) to a monthly cost for better budgeting.

## 7. Savings Management
*   **Periodic Savings Analysis**: View savings performance across different timeframes (Monthly, Quarterly, Yearly).
*   **Savings Rate**: Calculates savings as a percentage of your total income (`savings_rate`).
*   **Net Flow Tracking**: Monitor the difference between total inflows and outflows over time.

## 8. Purchase Planner (Wishlist)
*   **Goal Tracking**: Plan for major future purchases (e.g., "New Laptop", "Vacation").
*   **Priority Levels**: Assign High, Medium, or Low priority to planned items.
*   **Affordability Calculator**: Automatically estimates how many months it will take to afford each planned item based on your current actual savings rate.

## 9. Category Management
*   **Custom Categories**: Create, edit, and delete granular categories.
*   **Behavioral Flags**: Categories can be flagged as "Is Subscription", ensuring any transaction assigned to it automatically triggers subscription management workflows.

## 10. Personalization & Settings
*   **Theme Support**: Toggle between Light and Dark modes.
*   **Currency Customization**: Support for different currency symbols (default: ₹).
*   **Profile Customization**: Manage account settings and preferences.

---

## 11. User Authentication & Signup
*   **Secure Signup**: New users can create accounts with a unique username, email, and password.
    *   **Password Security**: Enhanced constraints requiring minimum 8 characters, at least one uppercase letter, one lowercase letter, one digit, and one special character.
    *   **Standard Validation**: Uses Django's built-in `AUTH_PASSWORD_VALIDATORS` for checking similarity, common passwords, and numeric patterns.
*   **Automatic Data Seeding**: Upon registration, accounts are automatically initialized with a set of default categories and investment types (based on `setup_demo.py`) to help users get started immediately.
*   **Secure Login**: Built-in authentication system with secure session management.
*   **Aesthetic UI**: Premium signup and login pages with modern design, gradients, and micro-animations.
*   **User Settings & Security**:
    *   **Profile Management**: Update currency, theme, and month start day.
    *   **Change Password**: Securely update account password directly from settings, enforcing the same high-security standards as signup.

---

## 12. Project Architecture & File Structure

The application is built with **Django** and follows a modular structure for better maintainability.

### Root Directory
*   `manage.py`: Django's command-line utility for administrative tasks.
*   `requirements.txt`: List of Python dependencies.
*   `db.sqlite3`: The application database.
*   `Features.md`: This document, outlining features and structure.
*   `README.md`: Basic project setup and overview.

### `/budget_project` (Project Configuration)
*   `settings.py`: Core Django settings, including database configuration, app registration, and custom settings (like `MONTH_START_DAY`).
*   `urls.py`: Root URL configuration, routing to the `core` app.
*   `wsgi.py` / `asgi.py`: Entry points for WSGI/ASGI-compatible web servers.

### `/core` (Main Application Logic)
*   **`models.py`**: Contains the data layer, including models for `Transaction`, `Category`, `Investment`, `BudgetLimit`, `Subscription`, and `PurchaseGoal`.
*   **`forms.py`**: Django forms used for creating and editing all entities (transactions, investments, etc.).
*   **`views/`**: Modularized view logic:
    *   `dashboard.py`: Main dashboard summary and quick actions.
    *   `transactions.py`: Transaction listing, filtering, and bulk actions.
    *   `investments.py`: Portfolio tracking and performance metrics.
    *   `analytics.py`: Data aggregation for charts and trends.
    *   `pdf_upload.py`: Handling of bank statement imports.
    *   `savings.py`: Net flow and savings rate analysis.
    *   `auth.py`: User registration and initial data setup logic.
*   **`templates/core/`**: HTML templates organized by feature (e.g., `analytics/`, `investments/`, `transactions/`, `signup.html`, `login.html`).
*   **`pdf_parser.py`**: Specialized logic for extracting transaction data from PDF bank statements.
*   **`middleware.py`**: Custom middleware to handle recurring transactions and automated updates on each request.
*   **`context_processors.py`**: Provides global variables (like total balance or current month) to all templates.

### `/static` (Frontend Assets)
*   `css/`: Stylesheets (Vanilla CSS).
*   `js/`: Frontend logic and chart initializations (using Chart.js).
*   `icons/`: SVG icons for categories and UI elements.
*   `manifest.json` / `sw.js`: PWA support for mobile installs and offline capabilities.

### `/media` (User Uploads)
*   Storage for uploaded PDF statements and other media assets.

---
---
*Last Updated: 2026-04-26 (Added Transaction Calendar to Dashboard)*
