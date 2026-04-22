# BudgetIQ — Personal Finance Tracker

A full-featured Django budgeting app, mobile-first.

## Quick Start

```bash
pip install -r requirements.txt
python manage.py migrate
python setup_demo.py       # Creates demo users + seed data
python manage.py runserver
```

Open: http://127.0.0.1:8000

## Login Credentials
| Username | Password  | Role      |
|----------|-----------|-----------|
| admin    | admin123  | Superuser |
| demo     | demo123   | User      |

## Features
- 📊 Dashboard with real-time budget overview
- 💸 Transactions — income, expense, side income, investment
- 📈 Investments — MF, stocks, FD (maturity calc), PPF, Gold, Crypto + custom types
- 📉 Analytics — pie charts, bar charts, trend lines (monthly/quarterly/yearly)
- 🗂️ Categories — color-coded, icon-tagged, CRUD
- 🚦 Budget Limits — monthly limits with progress bars & alerts
- 🔁 Subscriptions — tracker with monthly/yearly cost summary
- 🐷 Savings — calculator, goal planner, purchase wishlist
- 📋 Summary — planned vs actual spending, month-over-month
- 📄 PDF Import — parses bank statements (ICICI, HDFC, SBI), auto-categorizes
- ⚙️ Settings — custom month start date, currency symbol, dark mode

## Adding New Users (Admin only)
```bash
python manage.py createsuperuser
# Or via /admin/ panel
```

## Tech Stack
- Django 4.2 + SQLite
- Bootstrap 5.3
- Chart.js 4.4
- Bootstrap Icons
- pdfplumber (PDF parsing)
