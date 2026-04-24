from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
import datetime
from ..models import MonthlyLimit, Transaction
from ..forms import MonthlyLimitForm
from .helpers import check_limits


@login_required
def limit_list(request):
    user = request.user
    profile = user.profile
    cycle_anchor_day = max(1, min(profile.month_start_day, 28))
    today = timezone.now().date()
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

    try:
        ref_date = datetime.date(view_year, view_month, cycle_anchor_day)
    except ValueError:
        view_month = today.month
        view_year = today.year
        ref_date = datetime.date(view_year, view_month, cycle_anchor_day)

    start, end = profile.get_current_month_range(reference_date=ref_date)
    
    alerts = check_limits(user, start, end)
    
    form = MonthlyLimitForm(user)
    if request.method == 'POST':
        form = MonthlyLimitForm(user, request.POST)
        if form.is_valid():
            cat = form.cleaned_data.get('category')
            amount = form.cleaned_data['amount']
            obj, created = MonthlyLimit.objects.update_or_create(
                user=user, category=cat,
                defaults={'amount': amount}
            )
            msg = 'Limit set.' if created else 'Limit updated.'
            messages.success(request, msg)
            return redirect(f'/limits/?month={view_month}&year={view_year}')

    years = range(today.year - 2, today.year + 2)
    months = [(i, datetime.date(2000, i, 1).strftime('%B')) for i in range(1, 13)]
    
    return render(request, 'core/limits/list.html', {
        'alerts': alerts, 'form': form,
        'period_start': start, 'period_end': end,
        'view_month': view_month, 'view_year': view_year,
        'months': months, 'years': years,
    })


@login_required
def limit_delete(request, pk):
    obj = get_object_or_404(MonthlyLimit, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Limit removed.')
    return redirect('limit_list')


@login_required
def limit_edit(request, pk):
    obj = get_object_or_404(MonthlyLimit, pk=pk, user=request.user)
    if request.method == 'POST':
        form = MonthlyLimitForm(request.user, request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Limit updated.')
            return redirect('limit_list')
    else:
        form = MonthlyLimitForm(request.user, instance=obj)
    
    return render(request, 'core/limits/edit.html', {'form': form, 'limit': obj})
