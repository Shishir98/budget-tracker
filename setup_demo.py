#!/usr/bin/env python3
"""Creates demo users and seed data."""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budget_project.settings')
sys.path.insert(0, '/home/claude/budget_app')
django.setup()

from django.contrib.auth.models import User
from core.models import (UserProfile, InvestmentType, Category, Transaction,
                         Investment, MonthlyLimit, Subscription, PurchasePlan)
from decimal import Decimal
import datetime

# --- Create users ---
users_data = [
    ('Shishir', 'admin123', True),
    ('Kritka', 'admin123', True),
]
created_users = []
for uname, pwd, is_super in users_data:
    if not User.objects.filter(username=uname).exists():
        if is_super:
            u = User.objects.create_superuser(uname, f'{uname}@budgettracker.app', pwd)
        else:
            u = User.objects.create_user(uname, f'{uname}@budgettracker.app', pwd)
        print(f'Created user: {uname} / {pwd}')
    else:
        u = User.objects.get(username=uname)
        print(f'User exists: {uname}')
    created_users.append(u)

# Seed demo user
user = created_users[-1]  # demo user
profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'month_start_day': 1})

# --- Investment Types ---
inv_types = [
    ('Mutual Fund (Equity)', False, False, 'bar-chart-line'),
    ('Mutual Fund (Debt)', False, False, 'bar-chart'),
    ('Fixed Deposit', True, True, 'bank'),
    ('Stocks', False, False, 'graph-up-arrow'),
    ('PPF', True, True, 'shield-check'),
    ('NPS', False, True, 'person-badge'),
    ('Gold ETF', False, False, 'gem'),
    ('Real Estate', False, False, 'house'),
    ('Crypto', False, False, 'currency-bitcoin'),
    ('US Stocks', False, False, 'globe'),
]
created_types = {}
for name, has_mat, has_rate, icon in inv_types:
    t, _ = InvestmentType.objects.get_or_create(
        user=user, name=name,
        defaults={'has_maturity': has_mat, 'has_interest_rate': has_rate, 'icon': icon}
    )
    created_types[name] = t

# --- Categories ---
categories_data = [
    ('Food & Dining', '#f97316', 'any', 'bag-heart', False),     # Orange-500
    ('Transport', '#06b6d4', 'expense', 'car-front', False),     # Cyan-500
    ('Shopping', '#ec4899', 'expense', 'cart3', False),         # Pink-500
    ('Entertainment', '#8b5cf6', 'expense', 'film', False),     # Violet-500
    ('Utilities', '#eab308', 'expense', 'lightning-charge', False), # Amber-500
    ('Health', '#f43f5e', 'expense', 'heart-pulse', False),     # Rose-500
    ('Education', '#6366f1', 'expense', 'book', False),         # Indigo-500
    ('Travel', '#14b8a6', 'expense', 'airplane', False),        # Teal-500
    ('Groceries', '#22c55e', 'expense', 'basket', False),       # Emerald-500
    ('Personal Care', '#d946ef', 'expense', 'person-heart', False), # Fuchsia-500
    ('Salary', '#10b981', 'income', 'briefcase', False),        # Emerald-500
    ('Freelance', '#3b82f6', 'income', 'laptop', False),        # Blue-500
    ('Dividends', '#a855f7', 'income', 'cash-stack', False),    # Purple-500
    ('Investments', '#4f46e5', 'investment', 'graph-up-arrow', False), # Indigo-600
    ('Streaming', '#be123c', 'expense', 'play-circle', True),   # Rose-700
    ('Cloud Services', '#0284c7', 'expense', 'cloud', True),    # Sky-700
    ('Personal Transfer', '#475569', 'expense', 'person-lines-fill', False), # Slate-600
]
created_cats = {}
for name, color, ctype, icon, is_sub in categories_data:
    cat, _ = Category.objects.get_or_create(
        user=user, name=name,
        defaults={'color': color, 'type': ctype, 'icon': icon, 'is_subscription': is_sub}
    )
    created_cats[name] = cat

# Also create for admin user
admin_user = created_users[0]
for name, color, ctype, icon, is_sub in categories_data:
    Category.objects.get_or_create(
        user=admin_user, name=name,
        defaults={'color': color, 'type': ctype, 'icon': icon, 'is_subscription': is_sub}
    )
for name, has_mat, has_rate, icon in inv_types:
    InvestmentType.objects.get_or_create(
        user=admin_user, name=name,
        defaults={'has_maturity': has_mat, 'has_interest_rate': has_rate, 'icon': icon}
    )
