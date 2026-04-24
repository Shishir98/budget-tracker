from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal
import datetime
from ..models import Transaction, Investment, MonthlyLimit, Subscription, UserProfile, Category


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
        next_y, next_m = (y + 1, 1) if m == 12 else (y, m + 1)
        try:
            next_start = datetime.date(next_y, next_m, start_day)
        except ValueError:
            # Clamp to first day of the following month when start_day is invalid there.
            next_start = datetime.date(next_y, next_m, 1)
        end = next_start - datetime.timedelta(days=1)
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
    main_income = txns.filter(type='income').aggregate(t=Sum('amount'))['t'] or Decimal('0')
    side_income = txns.filter(type='side_income').aggregate(t=Sum('amount'))['t'] or Decimal('0')
    income = main_income + side_income
    expense = txns.filter(type='expense').aggregate(t=Sum('amount'))['t'] or Decimal('0')
    investment = txns.filter(type='investment').aggregate(t=Sum('amount'))['t'] or Decimal('0')
    savings = income - expense - investment
    return {
        'income': income,
        'main_income': main_income,
        'side_income': side_income,
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
            'pk': limit.pk,
            'label': label,
            'limit': limit.amount,
            'spent': spent,
            'pct': min(pct, 100),
            'over': pct > 100,
            'warning': 80 <= pct <= 100,
            'color': limit.category.color if limit.category else '#dc3545',
        })
    return alerts

def advance_billing_date(d, cycle):
    import calendar
    month = d.month
    year = d.year
    if cycle == 'monthly':
        month += 1
    elif cycle == 'quarterly':
        month += 3
    elif cycle == 'yearly':
        year += 1
    
    if month > 12:
        year += month // 12
        month = month % 12
        if month == 0:
            month = 12
            year -= 1
            
    day = d.day
    max_day = calendar.monthrange(year, month)[1]
    if day > max_day:
        day = max_day
    
    return datetime.date(year, month, day)

def process_auto_deductions(user):
    if not user.is_authenticated:
        return
        
    today = timezone.now().date()
    
    # Process subscriptions
    subs = Subscription.objects.filter(user=user, is_active=True, auto_deduct=True, next_billing_date__lte=today)
    for sub in subs:
        while sub.next_billing_date <= today:
            # Create transaction
            Transaction.objects.create(
                user=user,
                date=sub.next_billing_date,
                amount=sub.amount,
                type='expense',
                category=sub.category,
                notes=f"Auto-deducted subscription: {sub.name}",
                is_subscription=True
            )
            # Advance billing date
            sub.next_billing_date = advance_billing_date(sub.next_billing_date, sub.billing_cycle)
        sub.save()
        
    # Process recurring investments
    investments = Investment.objects.filter(user=user, is_active=True, is_recurring=True, auto_deduct=True, next_deduction_date__lte=today)
    
    # Cache the investment category to avoid repeated lookups
    investment_category = Category.objects.filter(user=user, name__iexact='Investments').first()
    if not investment_category:
        investment_category = Category.objects.filter(user=user, type='investment').first()

    for inv in investments:
        while inv.next_deduction_date and inv.next_deduction_date <= today:
            if not inv.recurring_amount:
                break
            # Create transaction
            Transaction.objects.create(
                user=user,
                date=inv.next_deduction_date,
                amount=inv.recurring_amount,
                type='investment',
                category=investment_category,
                investment_type=inv.investment_type,
                notes=f"Auto-deducted investment: {inv.name}",
                is_subscription=True
            )
            # Add to amount invested
            inv.amount_invested = Decimal(str(inv.amount_invested)) + Decimal(str(inv.recurring_amount))
            # Advance deduction date (assuming monthly for now)
            inv.next_deduction_date = advance_billing_date(inv.next_deduction_date, 'monthly')
        inv.save()


def ensure_subscription_plan(transaction):
    """
    Ensures that a Transaction marked as a subscription/recurring has a 
    corresponding Subscription or Investment plan record for auto-deduction.
    """
    if not transaction.is_subscription:
        return
        
    user = transaction.user
    next_date = advance_billing_date(transaction.date, 'monthly')
    
    if transaction.type == 'investment':
        # Check if an active recurring investment already exists with this name/type
        name = transaction.notes if transaction.notes else f"Recurring Investment ({transaction.investment_type.name if transaction.investment_type else 'Uncategorized'})"
        exists = Investment.objects.filter(
            user=user, 
            investment_type=transaction.investment_type,
            is_active=True,
            is_recurring=True
        ).exists()
        
        if not exists:
            Investment.objects.create(
                user=user,
                name=name[:200],
                investment_type=transaction.investment_type,
                amount_invested=transaction.amount,
                purchase_date=transaction.date,
                is_active=True,
                is_recurring=True,
                recurring_amount=transaction.amount,
                auto_deduct=True,
                next_deduction_date=next_date
            )
    else:
        # Check if an active subscription already exists for this category
        name = transaction.notes if transaction.notes else f"Subscription ({transaction.category.name if transaction.category else 'Uncategorized'})"
        exists = Subscription.objects.filter(
            user=user,
            category=transaction.category,
            is_active=True
        ).exists()
        
        if not exists:
            Subscription.objects.create(
                user=user,
                name=name[:200],
                amount=transaction.amount,
                billing_cycle='monthly',
                next_billing_date=next_date,
                category=transaction.category,
                is_active=True,
                auto_deduct=True
            )
