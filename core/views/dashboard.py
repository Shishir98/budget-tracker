from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal
from ..models import Transaction, Investment, Subscription, MonthlyLimit, Category
from .helpers import get_summary_stats, check_limits
from ..forms import TransactionForm


@login_required
def dashboard(request):
    user = request.user
    profile = user.profile
    start, end = profile.get_current_month_range()
    today = timezone.now().date()
    
    stats = get_summary_stats(user, start, end)
    alerts = check_limits(user, start, end)
    
    recent_txns = Transaction.objects.filter(user=user).select_related('category')[:10]
    
    # Upcoming subscriptions (next 7 days)
    upcoming_subs = Subscription.objects.filter(
        user=user, is_active=True,
        next_billing_date__gte=today,
        next_billing_date__lte=today + timezone.timedelta(days=7)
    )
    
    # Total investments
    portfolio_invested = Investment.objects.filter(user=user, is_active=True).aggregate(
        t=Sum('amount_invested'))['t'] or Decimal('0')
    portfolio_current = Investment.objects.filter(user=user, is_active=True).aggregate(
        t=Sum('current_value'))['t'] or Decimal('0')

    # Include generic investment transactions
    txn_invested = Transaction.objects.filter(
        Q(type='investment') | Q(category__type='investment'),
        user=user
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    
    total_invested = portfolio_invested + txn_invested
    total_current = portfolio_current + txn_invested
    
    # Unlabeled count
    unlabeled = Transaction.objects.filter(user=user, category__isnull=True, from_pdf=True).count()
    
    # Overbudget alerts count
    over_budget = [a for a in alerts if a['over']]
    
    # Prepare Quick Add form for Modal
    transaction_form = TransactionForm(user, initial={'date': today})
    inv_cat = Category.objects.filter(user=user, name='Investments').first()
    investment_category_pk = inv_cat.pk if inv_cat else None

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
        'transaction_form': transaction_form,
        'investment_category_pk': investment_category_pk,
    }
    return render(request, 'core/dashboard.html', context)
