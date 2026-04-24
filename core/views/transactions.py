from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from ..models import Transaction, Category, InvestmentType
from ..forms import TransactionForm
from django.utils import timezone
import datetime
from .helpers import get_period_range, ensure_subscription_plan


@login_required
def transaction_list(request):
    today = timezone.now().date()
    
    # Period handling
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
        start, end = get_period_range(request.user, 'month', view_year, view_month)
    except ValueError:
        view_month = today.month
        view_year = today.year
        start, end = get_period_range(request.user, 'month', view_year, view_month)

    # We explicitly order by id in addition to the model's default meta ordering.
    # This prevents "unstable" pagination where items might shift between pages 
    # if they share the exact same timestamp (common with bulk imports).
    qs = Transaction.objects.filter(user=request.user).select_related('category')
    
    # Filters
    q = request.GET.get('q', '')
    cat_id = request.GET.get('category', '')
    tx_type = request.GET.get('type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    unlabeled = request.GET.get('unlabeled', '')
    is_sub = request.GET.get('subscription', '')
    
    if q:
        qs = qs.filter(Q(notes__icontains=q) | Q(raw_description__icontains=q))
    if cat_id:
        qs = qs.filter(category_id=cat_id)
    if tx_type:
        if tx_type == 'income':
            qs = qs.filter(Q(type='income') | Q(type='side_income'))
        else:
            qs = qs.filter(type=tx_type)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    if unlabeled:
        qs = qs.filter(category__isnull=True)
    if is_sub:
        qs = qs.filter(is_subscription=True)
        
    # If no specific date range or search is provided, default to the selected period
    if not (date_from or date_to or q):
        qs = qs.filter(date__gte=start, date__lte=end)

    qs = qs.order_by('-date', '-created_at', '-id')
    
    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))
    
    categories = Category.objects.filter(user=request.user)
    years = range(today.year - 2, today.year + 2)
    months = [(i, datetime.date(2000, i, 1).strftime('%B')) for i in range(1, 13)]

    # Prepare query parameters for pagination links, excluding the 'page' key
    params = request.GET.copy()
    params.pop('page', None)
    
    return render(request, 'core/transactions/list.html', {
        'page_obj': page, 'categories': categories,
        'filters': {'q': q, 'cat': cat_id, 'type': tx_type,
                    'from': date_from, 'to': date_to, 'unlabeled': unlabeled, 'sub': is_sub},
        'tx_types': Transaction._meta.get_field('type').choices,
        'total_count': qs.count(),
        'query_params': params.urlencode(),
        'view_month': view_month, 'view_year': view_year,
        'months': months, 'years': years,
    })


@login_required
def transaction_add(request):
    if request.method == 'POST':
        form = TransactionForm(request.user, request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            # Auto-tag as subscription if the category is a subscription category
            if obj.category and obj.category.is_subscription:
                obj.is_subscription = True
            obj.user = request.user
            obj.save()
            
            # If marked as recurring/subscription, ensure the parent entity exists for auto-deduction
            if obj.is_subscription:
                ensure_subscription_plan(obj)
            
            messages.success(request, 'Transaction added.')
            return redirect('transaction_list')
    else:
        form = TransactionForm(request.user, initial={'date': datetime.date.today()})
    
    investment_category_pk = Category.objects.filter(user=request.user, name='Investments').values_list('pk', flat=True).first()
    return render(request, 'core/transactions/form.html', {
        'form': form,
        'title': 'Add Transaction',
        'investment_category_pk': investment_category_pk,
    })


@login_required
def transaction_edit(request, pk):
    obj = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.user, request.POST, instance=obj)
        if form.is_valid():
            updated_obj = form.save(commit=False)
            if updated_obj.category and updated_obj.category.is_subscription:
                updated_obj.is_subscription = True
            updated_obj.save()
            if updated_obj.is_subscription:
                ensure_subscription_plan(updated_obj)
            messages.success(request, 'Transaction updated.')
            url = reverse('transaction_list')
            if request.GET:
                url += '?' + request.GET.urlencode()
            return redirect(url)
    else:
        form = TransactionForm(request.user, instance=obj)
    
    investment_category_pk = Category.objects.filter(user=request.user, name='Investments').values_list('pk', flat=True).first()
    return render(request, 'core/transactions/form.html', {
        'form': form,
        'title': 'Edit Transaction',
        'obj': obj,
        'investment_category_pk': investment_category_pk,
    })


@login_required
def transaction_delete(request, pk):
    obj = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Transaction deleted.')
    url = reverse('transaction_list')
    if request.GET:
        url += '?' + request.GET.urlencode()
    return redirect(url)


@login_required
def bulk_categorize(request):
    """Assign category to multiple unlabeled transactions."""
    if request.method == 'POST':
        tx_ids = request.POST.getlist('tx_ids')
        cat_id = request.POST.get('category')
        if tx_ids and cat_id:
            cat = get_object_or_404(Category, pk=cat_id, user=request.user)
            Transaction.objects.filter(pk__in=tx_ids, user=request.user).update(category=cat, is_subscription=cat.is_subscription)
            if cat.is_subscription:
                for tx in Transaction.objects.filter(pk__in=tx_ids, user=request.user):
                    ensure_subscription_plan(tx)
            messages.success(request, f'Updated {len(tx_ids)} transactions.')
    url = reverse('transaction_list')
    if request.GET:
        url += '?' + request.GET.urlencode()
    return redirect(url)
