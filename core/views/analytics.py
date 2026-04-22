from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
import datetime, json
from ..models import Transaction, Category, Investment
from .helpers import get_period_range, get_summary_stats


@login_required
def analytics(request):
    user = request.user
    today = timezone.now().date()
    period = request.GET.get('period', 'month')
    year = request.GET.get('year', today.year)
    month = request.GET.get('month', today.month)
    quarter = request.GET.get('quarter', (today.month - 1) // 3 + 1)
    
    start, end = get_period_range(user, period, year, month, quarter)
    stats = get_summary_stats(user, start, end)
    
    txns = Transaction.objects.filter(user=user, date__gte=start, date__lte=end)
    
    # Category breakdown for expenses
    expense_by_cat = {}
    expense_colors = {}
    for t in txns.filter(type='expense').select_related('category'):
        name = t.category.name if t.category else 'Unlabeled'
        color = t.category.color if t.category else '#adb5bd'
        expense_by_cat[name] = expense_by_cat.get(name, 0) + float(t.amount)
        expense_colors[name] = color
    
    # Income breakdown
    income_by_cat = {}
    income_colors = {}
    for t in txns.filter(type__in=['income', 'side_income']).select_related('category'):
        name = t.category.name if t.category else 'Unlabeled'
        color = t.category.color if t.category else '#adb5bd'
        income_by_cat[name] = income_by_cat.get(name, 0) + float(t.amount)
        income_colors[name] = color
    
    # Monthly trend (last 6 months or quarters)
    trend_labels = []
    trend_income = []
    trend_expense = []
    trend_savings = []
    
    if period in ['month', 'year']:
        months_back = 12 if period == 'year' else 6
        for i in range(months_back - 1, -1, -1):
            d = today.replace(day=1)
            for _ in range(i):
                d = (d.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
            m_start = d
            if d.month == 12:
                m_end = datetime.date(d.year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                m_end = datetime.date(d.year, d.month + 1, 1) - datetime.timedelta(days=1)
            
            m_txns = Transaction.objects.filter(user=user, date__gte=m_start, date__lte=m_end)
            inc = float(m_txns.filter(type__in=['income', 'side_income']).aggregate(t=Sum('amount'))['t'] or 0)
            exp = float(m_txns.filter(type='expense').aggregate(t=Sum('amount'))['t'] or 0)
            trend_labels.append(d.strftime('%b %Y'))
            trend_income.append(inc)
            trend_expense.append(exp)
            trend_savings.append(inc - exp)
    
    # Investment portfolio by type
    investments = Investment.objects.filter(user=user, is_active=True).select_related('investment_type')
    inv_by_type = {}
    inv_colors = ['#6f42c1', '#0d6efd', '#0dcaf0', '#198754', '#ffc107', '#fd7e14', '#dc3545']
    for idx, inv in enumerate(investments):
        t = inv.investment_type.name if inv.investment_type else 'Other'
        inv_by_type[t] = inv_by_type.get(t, 0) + float(inv.amount_invested)

    # Include transactions categorized as 'investment' in the portfolio breakdown
    investment_txns = Transaction.objects.filter(
        Q(type='investment') | Q(category__type='investment'),
        user=user
    ).select_related('category', 'investment_type')
    for txn in investment_txns:
        t = txn.investment_type.name if txn.investment_type else (txn.category.name if txn.category else 'Other Investment')
        inv_by_type[t] = inv_by_type.get(t, 0) + float(txn.amount)
    
    # Build years and months for selectors
    years = list(range(today.year - 3, today.year + 1))
    months = [(i, datetime.date(2000, i, 1).strftime('%B')) for i in range(1, 13)]
    
    context = {
        'period': period, 'year': int(year), 'month': int(month), 'quarter': int(quarter),
        'start': start, 'end': end, 'stats': stats,
        'expense_labels': json.dumps(list(expense_by_cat.keys())),
        'expense_data': json.dumps(list(expense_by_cat.values())),
        'expense_colors': json.dumps(list(expense_colors.values())),
        'income_labels': json.dumps(list(income_by_cat.keys())),
        'income_data': json.dumps(list(income_by_cat.values())),
        'income_colors': json.dumps(list(income_colors.values())),
        'trend_labels': json.dumps(trend_labels),
        'trend_income': json.dumps(trend_income),
        'trend_expense': json.dumps(trend_expense),
        'trend_savings': json.dumps(trend_savings),
        'inv_labels': json.dumps(list(inv_by_type.keys())),
        'inv_data': json.dumps(list(inv_by_type.values())),
        'inv_colors': json.dumps(inv_colors[:len(inv_by_type)]),
        'years': years, 'months': months,
    }
    return render(request, 'core/analytics/index.html', context)
