from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from ..models import PurchasePlan, Transaction, Subscription
from ..forms import PurchasePlanForm
from .helpers import get_summary_stats
import datetime


@login_required
def savings_dashboard(request):
    user = request.user
    today = timezone.now().date()

    profile = user.profile
    cycle_anchor_day = max(1, min(profile.month_start_day, 28))

    # Get month/year from query parameters, default to current
    try:
        view_month = int(request.GET.get('month', today.month))
        view_year = int(request.GET.get('year', today.year))
        ref_date = datetime.date(view_year, view_month, cycle_anchor_day)
    except (ValueError, TypeError):
        view_month, view_year = today.month, today.year
        ref_date = today

    # Savings period follows user's configured billing cycle start day.
    start, end = profile.get_current_month_range(reference_date=ref_date)
    stats = get_summary_stats(user, start, end)
    
    plans = PurchasePlan.objects.filter(user=user)
    active_plans = plans.filter(is_purchased=False)
    
    # Monthly subscriptions cost
    subs = Subscription.objects.filter(user=user, is_active=True)
    monthly_subs = sum(s.monthly_equivalent() for s in subs)
    
    # Savings calculator data
    monthly_savings = float(stats['savings'])
    
    # Calculate months to afford each purchase plan
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
    years = range(today.year - 2, today.year + 2)
    months = [(i, datetime.date(2000, i, 1).strftime('%B')) for i in range(1, 13)]

    return render(request, 'core/savings/dashboard.html', {
        'stats': stats, 'active_plans': active_plans,
        'purchased_plans': plans.filter(is_purchased=True),
        'monthly_subs': monthly_subs, 'form': form,
        'period_start': start, 'period_end': end,
        'view_month': view_month, 'view_year': view_year,
        'years': years, 'months': months,
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
