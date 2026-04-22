from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal
import datetime
from ..models import Transaction, Investment, MonthlyLimit, Subscription, UserProfile


def get_period_range(user, period='month', year=None, month=None, quarter=None):
    today = timezone.now().date()
    profile = getattr(user, 'profile', None)
    start_day = profile.month_start_day if profile else 1
    
    if period == 'month':
        if year and month:
            y, m = int(year), int(month)
        else:
            y, m = today.year, today.month
        try:
            start = datetime.date(y, m, start_day)
        except ValueError:
            start = datetime.date(y, m, 1)
        if m == 12:
            end = datetime.date(y + 1, 1, start_day) - datetime.timedelta(days=1)
        else:
            end = datetime.date(y, m + 1, start_day) - datetime.timedelta(days=1)
        return start, end
    
    elif period == 'quarter':
        q = int(quarter) if quarter else ((today.month - 1) // 3 + 1)
        y = int(year) if year else today.year
        month_start = (q - 1) * 3 + 1
        start = datetime.date(y, month_start, 1)
        end_month = month_start + 2
        if end_month > 12:
            end = datetime.date(y + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end = datetime.date(y, end_month + 1, 1) - datetime.timedelta(days=1) if end_month < 12 else datetime.date(y, 12, 31)
        return start, end
    
    elif period == 'year':
        y = int(year) if year else today.year
        return datetime.date(y, 1, 1), datetime.date(y, 12, 31)
    
    return today.replace(day=1), today


def get_summary_stats(user, start_date, end_date):
    txns = Transaction.objects.filter(user=user, date__gte=start_date, date__lte=end_date)
    income = txns.filter(type__in=['income', 'side_income']).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    expense = txns.filter(type='expense').aggregate(t=Sum('amount'))['t'] or Decimal('0')
    investment = txns.filter(type='investment').aggregate(t=Sum('amount'))['t'] or Decimal('0')
    savings = income - expense - investment
    return {
        'income': income,
        'expense': expense,
        'investment': investment,
        'savings': savings,
        'savings_rate': round(float(savings) / float(income) * 100, 1) if float(income) > 0 else 0,
    }


def check_limits(user, start_date, end_date):
    """Return limit alerts."""
    alerts = []
    limits = MonthlyLimit.objects.filter(user=user)
    txns = Transaction.objects.filter(user=user, date__gte=start_date, date__lte=end_date, type='expense')
    
    for limit in limits:
        if limit.category:
            spent = txns.filter(category=limit.category).aggregate(t=Sum('amount'))['t'] or Decimal('0')
        else:
            spent = txns.aggregate(t=Sum('amount'))['t'] or Decimal('0')
        
        pct = (float(spent) / float(limit.amount) * 100) if float(limit.amount) > 0 else 0
        label = limit.category.name if limit.category else 'Overall Budget'
        
        alerts.append({
            'label': label,
            'limit': limit.amount,
            'spent': spent,
            'pct': min(pct, 100),
            'over': pct > 100,
            'warning': 80 <= pct <= 100,
            'color': limit.category.color if limit.category else '#dc3545',
        })
    
    return alerts
