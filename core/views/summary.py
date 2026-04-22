from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
import datetime, json
from ..models import Transaction, MonthlyLimit, Category
from .helpers import get_summary_stats


@login_required
def summary(request):
    user = request.user
    profile = user.profile
    today = timezone.now().date()
    start, end = profile.get_current_month_range()
    stats = get_summary_stats(user, start, end)
    
    # Limits vs actual
    limits = MonthlyLimit.objects.filter(user=user).select_related('category')
    txns = Transaction.objects.filter(user=user, date__gte=start, date__lte=end, type='expense')
    
    limit_comparison = []
    total_planned = Decimal('0')
    total_spent = Decimal('0')
    
    for limit in limits:
        if limit.category:
            spent = txns.filter(category=limit.category).aggregate(t=Sum('amount'))['t'] or Decimal('0')
        else:
            spent = txns.aggregate(t=Sum('amount'))['t'] or Decimal('0')
        pct = (float(spent) / float(limit.amount) * 100) if float(limit.amount) > 0 else 0
        limit_comparison.append({
            'label': limit.category.name if limit.category else 'Overall Budget',
            'planned': limit.amount,
            'spent': spent,
            'remaining': limit.amount - spent,
            'pct': min(pct, 100),
            'over': pct > 100,
            'color': limit.category.color if limit.category else '#dc3545',
        })
        if limit.category:
            total_planned += limit.amount
            total_spent += spent
    
    # Month-over-month for last 3 months
    mom = []
    for i in range(2, -1, -1):
        d = today.replace(day=1)
        for _ in range(i):
            d = (d.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        if d.month == 12:
            m_end = datetime.date(d.year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            m_end = datetime.date(d.year, d.month + 1, 1) - datetime.timedelta(days=1)
        s = get_summary_stats(user, d, m_end)
        mom.append({'month': d.strftime('%b %Y'), **s})
    
    return render(request, 'core/summary/index.html', {
        'stats': stats, 'limit_comparison': limit_comparison,
        'total_planned': total_planned, 'total_spent': total_spent,
        'mom': mom, 'period_start': start, 'period_end': end,
        'mom_labels': json.dumps([m['month'] for m in mom]),
        'mom_income': json.dumps([float(m['income']) for m in mom]),
        'mom_expense': json.dumps([float(m['expense']) for m in mom]),
        'mom_savings': json.dumps([float(m['savings']) for m in mom]),
    })
