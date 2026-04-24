from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal
import datetime, json
from ..models import Transaction, Investment, Subscription, MonthlyLimit, Category
from .helpers import get_summary_stats, check_limits, process_auto_deductions
from ..forms import TransactionForm


@login_required
def dashboard(request):
    user = request.user
    profile = user.profile
    today = timezone.now().date()

    # Process auto deductions is now handled by RecurringTransactionsMiddleware

    # Period handling from query parameters (same pattern as transactions view)
    try:
        view_month = int(request.GET.get('month', today.month))
    except (TypeError, ValueError):
        view_month = today.month
    try:
        view_year = int(request.GET.get('year', today.year))
    except (TypeError, ValueError):
        view_year = today.year

    if view_month < 1 or view_month > 12:
        view_month = today.month

    cycle_anchor_day = max(1, min(profile.month_start_day, 28))
    try:
        ref_date = datetime.date(view_year, view_month, cycle_anchor_day)
    except ValueError:
        ref_date = today.replace(day=1)
        view_month = ref_date.month
        view_year = ref_date.year

    # Dashboard period follows user's configured billing cycle start day.
    start, end = profile.get_current_month_range(reference_date=ref_date)
    today = timezone.now().date()
    
    stats = get_summary_stats(user, start, end)
    alerts = check_limits(user, start, end)
    
    # Limits vs actual for summary
    limits = MonthlyLimit.objects.filter(user=user).select_related('category')
    txns = Transaction.objects.filter(user=user, date__gte=start, date__lte=end, type='expense')
    
    limit_comparison = []
    for limit in limits:
        if limit.category:
            spent = txns.filter(category=limit.category).aggregate(t=Sum('amount'))['t'] or Decimal('0')
        else:
            spent = txns.aggregate(t=Sum('amount'))['t'] or Decimal('0')
        pct = (float(spent) / float(limit.amount) * 100) if float(limit.amount) > 0 else 0
        limit_comparison.append({
            'pk': limit.pk,
            'label': limit.category.name if limit.category else 'Overall Budget',
            'planned': limit.amount,
            'spent': spent,
            'remaining': limit.amount - spent,
            'pct': min(pct, 100),
            'over': pct > 100,
            'color': limit.category.color if limit.category else '#dc3545',
        })
    
    # Month-over-month for selected month and previous 2 months
    mom = []
    anchor_month = ref_date.replace(day=1)
    for i in range(2, -1, -1):
        d = anchor_month
        for _ in range(i):
            d = (d.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        if d.month == 12:
            m_end = datetime.date(d.year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            m_end = datetime.date(d.year, d.month + 1, 1) - datetime.timedelta(days=1)
        s = get_summary_stats(user, d, m_end)
        mom.append({'month': d.strftime('%b %Y'), **s})
    
    # Recent transactions should match the selected calendar month.
    cal_start = datetime.date(view_year, view_month, 1)
    if view_month == 12:
        cal_end = datetime.date(view_year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        cal_end = datetime.date(view_year, view_month + 1, 1) - datetime.timedelta(days=1)
    recent_txns = Transaction.objects.filter(
        user=user,
        date__gte=cal_start,
        date__lte=cal_end
    ).select_related('category').order_by('-date', '-created_at')[:5]
    
    # Subscriptions within the selected period
    upcoming_subs = Subscription.objects.filter(
        user=user, is_active=True,
        next_billing_date__gte=start,
        next_billing_date__lte=end
    )
    
    # Total investments
    portfolio_invested = Investment.objects.filter(user=user, is_active=True).aggregate(
        t=Sum('amount_invested'))['t'] or Decimal('0')
        
    portfolio_current_explicit = Investment.objects.filter(user=user, is_active=True, current_value__isnull=False).aggregate(
        t=Sum('current_value'))['t'] or Decimal('0')
    portfolio_current_implicit = Investment.objects.filter(user=user, is_active=True, current_value__isnull=True).aggregate(
        t=Sum('amount_invested'))['t'] or Decimal('0')
    portfolio_current = portfolio_current_explicit + portfolio_current_implicit

    # Include generic investment transactions (all-time, excluding subscriptions)
    txn_invested = Transaction.objects.filter(
        Q(type='investment') | Q(category__type='investment'),
        user=user,
        is_subscription=False
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    
    total_invested = portfolio_invested + txn_invested
    total_current = portfolio_current + txn_invested
    
    # Unlabeled count
    unlabeled = Transaction.objects.filter(
        user=user,
        category__isnull=True,
        from_pdf=True,
        date__gte=start,
        date__lte=end
    ).count()
    
    # Overbudget alerts count
    over_budget = [a for a in alerts if a['over']]
    
    # Prepare Quick Add form for Modal
    initial_date = today if start <= today <= end else start
    transaction_form = TransactionForm(user, initial={'date': initial_date})
    inv_cat = Category.objects.filter(user=user, name='Investments').first()
    investment_category_pk = inv_cat.pk if inv_cat else None
    years = range(today.year - 2, today.year + 2)
    months = [(i, datetime.date(2000, i, 1).strftime('%B')) for i in range(1, 13)]
    prev_ref = (ref_date.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
    if ref_date.month == 12:
        next_ref = datetime.date(ref_date.year + 1, 1, 1)
    else:
        next_ref = datetime.date(ref_date.year, ref_date.month + 1, 1)

    context = {
        'stats': stats,
        'alerts': alerts,
        'recent_txns': recent_txns,
        'upcoming_subs': upcoming_subs,
        'total_invested': total_invested,
        'total_current': total_current,
        'portfolio_gain': float(total_current) - float(total_invested) if total_current else 0,
        'unlabeled': unlabeled,
        'over_budget': over_budget,
        'period_start': start,
        'period_end': end,
        'view_month': view_month,
        'view_year': view_year,
        'months': months,
        'years': years,
        'prev_month': prev_ref.month,
        'prev_year': prev_ref.year,
        'next_month': next_ref.month,
        'next_year': next_ref.year,
        'transaction_form': transaction_form,
        'investment_category_pk': investment_category_pk,
        'limit_comparison': limit_comparison,
        'mom': mom,
        'mom_labels': json.dumps([m['month'] for m in mom]),
        'mom_main_income': json.dumps([float(m['main_income']) for m in mom]),
        'mom_side_income': json.dumps([float(m['side_income']) for m in mom]),
        'mom_expense': json.dumps([float(m['expense']) for m in mom]),
        'mom_savings': json.dumps([float(m['savings']) for m in mom]),
    }
    return render(request, 'core/dashboard.html', context)
