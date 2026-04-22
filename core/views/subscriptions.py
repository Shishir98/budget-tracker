from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
from ..models import Subscription, Transaction
from ..forms import SubscriptionForm


@login_required
def subscription_list(request):
    user = request.user
    subs = Subscription.objects.filter(user=user).select_related('category')
    
    # Calculate planned monthly costs from active subscription plans
    planned_monthly = sum(s.monthly_equivalent() for s in subs if s.is_active)

    # Calculate actual spending on transactions tagged as subscriptions for the current period
    start, end = user.profile.get_current_month_range()
    actual_monthly = Transaction.objects.filter(
        user=user,
        is_subscription=True,
        date__gte=start,
        date__lte=end
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    monthly_total = Decimal(str(planned_monthly)) + actual_monthly
    yearly_total = monthly_total * 12
    
    # Fetch actual payments marked as subscriptions to show in history
    payment_history = Transaction.objects.filter(user=user, is_subscription=True).select_related('category').order_by('-date')
    
    return render(request, 'core/subscriptions/list.html', {
        'subs': subs, 'monthly_total': monthly_total, 'yearly_total': yearly_total,
        'payment_history': payment_history
    })


@login_required
def subscription_add(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.user, request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, 'Subscription added.')
            return redirect('subscription_list')
    else:
        form = SubscriptionForm(request.user)
    return render(request, 'core/subscriptions/form.html', {'form': form, 'title': 'Add Subscription'})


@login_required
def subscription_edit(request, pk):
    obj = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method == 'POST':
        form = SubscriptionForm(request.user, request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subscription updated.')
            return redirect('subscription_list')
    else:
        form = SubscriptionForm(request.user, instance=obj)
    return render(request, 'core/subscriptions/form.html', {'form': form, 'title': 'Edit Subscription', 'obj': obj})


@login_required
def subscription_delete(request, pk):
    obj = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Subscription deleted.')
    return redirect('subscription_list')
