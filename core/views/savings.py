from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum
from ..models import PurchasePlan, Transaction, Subscription
from ..forms import PurchasePlanForm
from .helpers import get_summary_stats, get_period_range
import datetime


@login_required
def savings_dashboard(request):
    user = request.user
    today = timezone.now().date()

    profile = user.profile

    # Period selector (same pattern as analytics)
    period = request.GET.get('period', 'month')
    year   = int(request.GET.get('year',    today.year))
    month  = int(request.GET.get('month',   today.month))
    quarter = int(request.GET.get('quarter', (today.month - 1) // 3 + 1))

    # Resolve the selected period date range
    start, end = get_period_range(user, period, year, month, quarter)
    stats = get_summary_stats(user, start, end)

    # --- Quarterly stats (always computed for the current/selected quarter tile) ---
    q_start, q_end = get_period_range(user, 'quarter', year, quarter=quarter)
    q_stats = get_summary_stats(user, q_start, q_end)

    # --- Yearly stats ---
    y_start, y_end = get_period_range(user, 'year', year)
    y_stats = get_summary_stats(user, y_start, y_end)

    # Per-quarter savings rate breakdown for the Year tab
    quarterly_breakdown = []
    for q_num in range(1, 5):
        qs, qe = get_period_range(user, 'quarter', year, quarter=q_num)
        qs_stats = get_summary_stats(user, qs, qe)
        quarterly_breakdown.append((f'Q{q_num}', qs_stats['savings_rate']))

    # Monthly subscriptions cost (planned + actual in selected period)
    subs = Subscription.objects.filter(user=user, is_active=True)
    planned_monthly = sum(s.monthly_equivalent() for s in subs)

    actual_monthly = Transaction.objects.filter(
        user=user,
        is_subscription=True,
        date__gte=start,
        date__lte=end
    ).exclude(type='investment').aggregate(total=Sum('amount'))['total'] or Decimal('0')

    monthly_subs = Decimal(str(planned_monthly)) + actual_monthly

    # Purchase plans
    plans = PurchasePlan.objects.filter(user=user)
    active_plans = plans.filter(is_purchased=False)

    # Calculate months to afford each purchase plan (based on selected period savings)
    monthly_savings = float(stats['savings']) if period == 'month' else (
        float(stats['savings']) / 3 if period == 'quarter' else float(stats['savings']) / 12
    )

    for plan in active_plans:
        if monthly_savings > 0:
            plan.months_needed = max(0, round(float(plan.estimated_cost) / monthly_savings, 1))
        else:
            plan.months_needed = None

    form = PurchasePlanForm()
    if request.method == 'POST':
        form = PurchasePlanForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, 'Purchase plan added.')
            return redirect('savings_dashboard')

    # Generate year/month lists for the selector
    years = list(range(today.year - 2, today.year + 2))
    months = [(i, datetime.date(2000, i, 1).strftime('%B')) for i in range(1, 13)]

    return render(request, 'core/savings/dashboard.html', {
        'stats': stats,
        'q_stats': q_stats,
        'y_stats': y_stats,
        'active_plans': active_plans,
        'purchased_plans': plans.filter(is_purchased=True),
        'monthly_subs': monthly_subs,
        'form': form,
        'period_start': start,
        'period_end': end,
        'q_start': q_start, 'q_end': q_end,
        'y_start': y_start, 'y_end': y_end,
        'period': period,
        'view_month': month,
        'view_year': year,
        'quarter': quarter,
        'quarterly_breakdown': quarterly_breakdown,
        'years': years,
        'months': months,
    })


@login_required
def plan_edit(request, pk):
    obj = get_object_or_404(PurchasePlan, pk=pk, user=request.user)
    form = PurchasePlanForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Plan updated.')
        return redirect('savings_dashboard')
    return render(request, 'core/savings/plan_form.html', {'form': form, 'obj': obj})


@login_required
def plan_delete(request, pk):
    obj = get_object_or_404(PurchasePlan, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Plan deleted.')
    return redirect('savings_dashboard')


@login_required
def plan_toggle(request, pk):
    obj = get_object_or_404(PurchasePlan, pk=pk, user=request.user)
    obj.is_purchased = not obj.is_purchased
    obj.save()
    return redirect('savings_dashboard')
