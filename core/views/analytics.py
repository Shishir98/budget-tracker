from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
import datetime
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

    # Burn rate and runway (estimated from recent spend + all-time net cashflow)
    def month_bounds(y, m):
        start_date = datetime.date(y, m, 1)
        if m == 12:
            end_date = datetime.date(y + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_date = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)
        return start_date, end_date

    current_month_start = end.replace(day=1)
    burn_months = []
    for i in range(3):
        anchor = current_month_start - datetime.timedelta(days=32 * i)
        m_start = anchor.replace(day=1)
        if m_start.month == 12:
            m_end = datetime.date(m_start.year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            m_end = datetime.date(m_start.year, m_start.month + 1, 1) - datetime.timedelta(days=1)
        burn_months.append((m_start, m_end))

    burn_samples = []
    for m_start, m_end in burn_months:
        month_outgoing = Transaction.objects.filter(
            user=user,
            date__gte=m_start,
            date__lte=m_end
        ).filter(
            Q(type='expense') | Q(type='investment') | Q(category__type='investment')
        ).aggregate(t=Sum('amount'))['t'] or Decimal('0')
        burn_samples.append(float(month_outgoing))

    burn_rate = (sum(burn_samples) / len(burn_samples)) if burn_samples else 0.0

    all_txns = Transaction.objects.filter(user=user)
    all_income = all_txns.filter(type__in=['income', 'side_income']).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    all_outgoing = all_txns.filter(
        Q(type='expense') | Q(type='investment') | Q(category__type='investment')
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    estimated_cash = float(all_income - all_outgoing)
    runway_months = (estimated_cash / burn_rate) if burn_rate > 0 and estimated_cash > 0 else 0.0

    # Top spending changes (MoM) by category/investment type
    anchor_start = end.replace(day=1)
    current_start, current_end = month_bounds(anchor_start.year, anchor_start.month)
    if anchor_start.month == 1:
        prev_year, prev_month = anchor_start.year - 1, 12
    else:
        prev_year, prev_month = anchor_start.year, anchor_start.month - 1
    prev_start, prev_end = month_bounds(prev_year, prev_month)

    def spending_map(start_date, end_date):
        result = {}
        q = Transaction.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).filter(
            Q(type='expense') | Q(type='investment') | Q(category__type='investment')
        ).select_related('category', 'investment_type')

        for t in q:
            is_investment = t.type == 'investment' or (t.category and t.category.type == 'investment')
            if is_investment:
                label = t.investment_type.name if t.investment_type else (t.category.name if t.category else 'Investments')
            else:
                label = t.category.name if t.category else 'Unlabeled'
            result[label] = result.get(label, 0.0) + float(t.amount)
        return result

    current_spend = spending_map(current_start, current_end)
    prev_spend = spending_map(prev_start, prev_end)
    all_labels = set(current_spend.keys()) | set(prev_spend.keys())

    spending_changes = []
    for label in all_labels:
        curr = current_spend.get(label, 0.0)
        prev = prev_spend.get(label, 0.0)
        change = curr - prev
        pct = ((change / prev) * 100.0) if prev > 0 else (100.0 if curr > 0 else 0.0)
        spending_changes.append({
            'label': label,
            'current': curr,
            'previous': prev,
            'change': change,
            'change_pct': pct,
        })

    spending_changes.sort(key=lambda x: abs(x['change']), reverse=True)
    
    # Category breakdown for outgoing money (expenses + investments)
    expense_by_cat = {}
    for t in txns.filter(
        Q(type='expense') | Q(type='investment') | Q(category__type='investment')
    ).select_related('category', 'investment_type'):
        is_investment = t.type == 'investment' or (t.category and t.category.type == 'investment')
        if is_investment:
            # Keep all investments in one bucket for cleaner analytics.
            name = 'Investments'
        else:
            name = t.category.name if t.category else 'Unlabeled'
        expense_by_cat[name] = expense_by_cat.get(name, 0) + float(t.amount)

    # Build a high-contrast color set for the expense doughnut chart.
    # Keep investments fixed so users can quickly recognize the slice.
    expense_items = sorted(expense_by_cat.items(), key=lambda x: x[1], reverse=True)
    expense_labels_list = [k for k, _ in expense_items]
    expense_data_list = [v for _, v in expense_items]

    expense_palette = [
        '#2563eb',  # blue
        '#ef4444',  # red
        '#10b981',  # emerald
        '#f59e0b',  # amber
        '#06b6d4',  # cyan
        '#ec4899',  # pink
        '#84cc16',  # lime
        '#f97316',  # orange
        '#14b8a6',  # teal
        '#6366f1',  # indigo
    ]
    expense_color_map = {'Investments': '#7c3aed'}
    palette_idx = 0
    for label in expense_labels_list:
        if label not in expense_color_map:
            expense_color_map[label] = expense_palette[palette_idx % len(expense_palette)]
            palette_idx += 1
    expense_colors_list = [expense_color_map[label] for label in expense_labels_list]
    
    # Income breakdown
    income_by_cat = {}
    income_colors = {}
    for t in txns.filter(type__in=['income', 'side_income']).select_related('category'):
        name = t.category.name if t.category else 'Unlabeled'
        color = t.category.color if t.category else '#94a3b8'
        income_by_cat[name] = income_by_cat.get(name, 0) + float(t.amount)
        income_colors[name] = color
    
    # Monthly trend (last 6 months or quarters)
    trend_labels = []
    trend_income = []
    trend_expense = []
    trend_investment = []
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
            inv = float(
                m_txns.filter(Q(type='investment') | Q(category__type='investment')).aggregate(t=Sum('amount'))['t'] or 0
            )
            trend_labels.append(d.strftime('%b %Y'))
            trend_income.append(inc)
            trend_expense.append(exp)
            trend_investment.append(inv)
            trend_savings.append(inc - exp - inv)
    
    # Investment portfolio by type
    investments = Investment.objects.filter(user=user, is_active=True).select_related('investment_type')
    inv_by_type = {}
    # Modern sleek palette: Indigo, Emerald, Amber, Blue, Violet, Cyan, Rose
    inv_colors = ['#6366f1', '#10b981', '#f59e0b', '#3b82f6', '#8b5cf6', '#06b6d4', '#f43f5e']
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
        'burn_rate': round(burn_rate, 2),
        'estimated_cash': round(estimated_cash, 2),
        'runway_months': round(runway_months, 1),
        'burn_window_months': len(burn_samples),
        'spending_changes': spending_changes[:6],
        'mom_current_label': current_start.strftime('%b %Y'),
        'mom_prev_label': prev_start.strftime('%b %Y'),
        'expense_labels': expense_labels_list,
        'expense_data': expense_data_list,
        'expense_colors': expense_colors_list,
        'income_labels': list(income_by_cat.keys()),
        'income_data': list(income_by_cat.values()),
        'income_colors': list(income_colors.values()),
        'trend_labels': trend_labels,
        'trend_income': trend_income,
        'trend_expense': trend_expense,
        'trend_investment': trend_investment,
        'trend_savings': trend_savings,
        'inv_labels': list(inv_by_type.keys()),
        'inv_data': list(inv_by_type.values()),
        'inv_colors': inv_colors[:len(inv_by_type)],
        'years': years, 'months': months,
    }
    return render(request, 'core/analytics/index.html', context)
