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
    ('admin', 'admin123', True),
    ('demo', 'demo123', False),
]
created_users = []
for uname, pwd, is_super in users_data:
    if not User.objects.filter(username=uname).exists():
        if is_super:
            u = User.objects.create_superuser(uname, f'{uname}@budgetiq.app', pwd)
        else:
            u = User.objects.create_user(uname, f'{uname}@budgetiq.app', pwd)
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
    ('Food & Dining', '#FF6B35', 'any', 'bag-heart', False),
    ('Transport', '#4ECDC4', 'expense', 'car-front', False),
    ('Shopping', '#45B7D1', 'expense', 'cart3', False),
    ('Entertainment', '#96CEB4', 'expense', 'film', False),
    ('Utilities', '#FFEAA7', 'expense', 'lightning-charge', False),
    ('Health', '#DDA0DD', 'expense', 'heart-pulse', False),
    ('Education', '#98D8C8', 'expense', 'book', False),
    ('Travel', '#F7DC6F', 'expense', 'airplane', False),
    ('Groceries', '#82E0AA', 'expense', 'basket', False),
    ('Personal Care', '#F1948A', 'expense', 'person-heart', False),
    ('Salary', '#2ECC71', 'income', 'briefcase', False),
    ('Freelance', '#3498DB', 'income', 'laptop', False),
    ('Dividends', '#9B59B6', 'income', 'cash-stack', False),
    ('Investments', '#6f42c1', 'investment', 'graph-up-arrow', False),
    ('Streaming', '#E74C3C', 'expense', 'play-circle', True),
    ('Cloud Services', '#3498DB', 'expense', 'cloud', True),
    ('Personal Transfer', '#95A5A6', 'expense', 'person-lines-fill', False),
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

