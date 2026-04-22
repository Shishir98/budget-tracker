from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
from ..models import MonthlyLimit, Transaction
from ..forms import MonthlyLimitForm
from .helpers import check_limits


@login_required
def limit_list(request):
    user = request.user
    profile = user.profile
    start, end = profile.get_current_month_range()
    
    limits = MonthlyLimit.objects.filter(user=user).select_related('category')
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
            return redirect('limit_list')
    
    return render(request, 'core/limits/list.html', {
        'limits': limits, 'alerts': alerts, 'form': form,
        'period_start': start, 'period_end': end,
    })


@login_required
def limit_delete(request, pk):
    obj = get_object_or_404(MonthlyLimit, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Limit removed.')
    return redirect('limit_list')
