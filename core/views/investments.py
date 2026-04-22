import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from decimal import Decimal
from ..models import Investment, InvestmentType, Transaction
from ..forms import InvestmentForm, InvestmentTypeForm


@login_required
def investment_list(request):
    investments = Investment.objects.filter(user=request.user).select_related('investment_type')
    inv_types = InvestmentType.objects.filter(user=request.user)
    
    # Filter by type
    type_filter = request.GET.get('type', '')
    active_filter = request.GET.get('active', '')
    if type_filter:
        investments = investments.filter(investment_type_id=type_filter)
    if active_filter == '1':
        investments = investments.filter(is_active=True)
    elif active_filter == '0':
        investments = investments.filter(is_active=False)
    
    # Calculate totals from the tracked Investment portfolio
    portfolio_invested = investments.aggregate(t=Sum('amount_invested'))['t'] or Decimal('0')
    portfolio_current = investments.exclude(current_value__isnull=True).aggregate(t=Sum('current_value'))['t'] or Decimal('0')

    # Fetch investment transactions to display unlinked activity
    unlinked_txns = Transaction.objects.filter(
        Q(type='investment') | Q(category__type='investment'),
        user=request.user
    ).select_related('category', 'investment_type').order_by('-date')

    # Include transaction amounts in the total figures
    unlinked_total = unlinked_txns.aggregate(t=Sum('amount'))['t'] or Decimal('0')
    
    total_invested = portfolio_invested + unlinked_total
    current_vals = portfolio_current + unlinked_total

    # Group by type for pie chart
    by_type = {}
    for inv in investments:
        t = inv.investment_type.name if inv.investment_type else 'Other'
        by_type[t] = by_type.get(t, 0) + float(inv.amount_invested)

    for txn in unlinked_txns:
        t = txn.investment_type.name if txn.investment_type else (txn.category.name if txn.category else 'Unlinked')
        by_type[t] = by_type.get(t, 0) + float(txn.amount)

    return render(request, 'core/investments/list.html', {
        'investments': investments,
        'inv_types': inv_types,
        'total_invested': total_invested,
        'current_vals': current_vals,
        'portfolio_gain': float(current_vals) - float(total_invested),
        'by_type_labels': json.dumps(list(by_type.keys())),
        'by_type_data': json.dumps(list(by_type.values())),
        'filters': {'type': type_filter, 'active': active_filter},
        'unlinked_txns': unlinked_txns,
    })


@login_required
def investment_add(request):
    if request.method == 'POST':
        form = InvestmentForm(request.user, request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, 'Investment added.')
            return redirect('investment_list')
    else:
        form = InvestmentForm(request.user)
    inv_types = InvestmentType.objects.filter(user=request.user)
    return render(request, 'core/investments/form.html', {
        'form': form, 'title': 'Add Investment', 'inv_types_json': list(inv_types.values())
    })


@login_required
def investment_edit(request, pk):
    obj = get_object_or_404(Investment, pk=pk, user=request.user)
    if request.method == 'POST':
        form = InvestmentForm(request.user, request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Investment updated.')
            return redirect('investment_list')
    else:
        form = InvestmentForm(request.user, instance=obj)
    inv_types = InvestmentType.objects.filter(user=request.user)
    return render(request, 'core/investments/form.html', {
        'form': form, 'title': 'Edit Investment', 'obj': obj, 'inv_types_json': list(inv_types.values())
    })


@login_required
def investment_delete(request, pk):
    obj = get_object_or_404(Investment, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Investment deleted.')
    return redirect('investment_list')


@login_required
def investment_type_list(request):
    types = InvestmentType.objects.filter(user=request.user)
    form = InvestmentTypeForm()
    if request.method == 'POST':
        form = InvestmentTypeForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, 'Investment type added.')
            return redirect('investment_type_list')
    return render(request, 'core/investments/types.html', {'types': types, 'form': form})


@login_required
def investment_type_delete(request, pk):
    obj = get_object_or_404(InvestmentType, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Investment type deleted.')
    return redirect('investment_type_list')
