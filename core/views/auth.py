from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from ..forms import SignupForm
from ..models import Category, InvestmentType

def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Initialize basic data for the new user
            initialize_user_data(user)
            
            login(request, user)
            messages.success(request, f"Welcome to Budget Tracker, {user.username}!")
            return redirect('dashboard')
    else:
        form = SignupForm()
    
    return render(request, 'core/signup.html', {'form': form})

def initialize_user_data(user):
    """Initializes basic categories and investment types for a new user."""
    
    # Basic Categories from setup_demo.py
    categories_data = [
        ('Food & Dining', '#f97316', 'any', 'bag-heart', False),
        ('Transport', '#06b6d4', 'expense', 'car-front', False),
        ('Shopping', '#ec4899', 'expense', 'cart3', False),
        ('Entertainment', '#8b5cf6', 'expense', 'film', False),
        ('Utilities', '#eab308', 'expense', 'lightning-charge', False),
        ('Health', '#f43f5e', 'expense', 'heart-pulse', False),
        ('Education', '#6366f1', 'expense', 'book', False),
        ('Travel', '#14b8a6', 'expense', 'airplane', False),
        ('Groceries', '#22c55e', 'expense', 'basket', False),
        ('Personal Care', '#d946ef', 'expense', 'person-heart', False),
        ('Salary', '#10b981', 'income', 'briefcase', False),
        ('Freelance', '#3b82f6', 'income', 'laptop', False),
        ('Dividends', '#a855f7', 'income', 'cash-stack', False),
        ('Investments', '#4f46e5', 'investment', 'graph-up-arrow', False),
        ('Streaming', '#be123c', 'expense', 'play-circle', True),
        ('Cloud Services', '#0284c7', 'expense', 'cloud', True),
        ('Personal Transfer', '#475569', 'expense', 'person-lines-fill', False),
    ]
    
    for name, color, ctype, icon, is_sub in categories_data:
        Category.objects.get_or_create(
            user=user, name=name,
            defaults={'color': color, 'type': ctype, 'icon': icon, 'is_subscription': is_sub}
        )
        
    # Basic Investment Types from setup_demo.py
    inv_types = [
        ('Mutual Fund (Equity)', False, False, 'bar-chart-line'),
        ('Mutual Fund (Debt)', False, False, 'bar-chart'),
        ('Fixed Deposit', True, True, 'bank'),
        ('Stocks', False, False, 'graph-up-arrow'),
        ('PPF', True, True, 'shield-check'),
        ('NPS', False, True, 'person-badge'),
        ('Gold ETF', False, False, 'gem'),
        ('Real Estate', False, False, 'house'),
        ('Crypto', False, False, 'currency-bitcoin'),
        ('US Stocks', False, False, 'globe'),
    ]
    
    for name, has_mat, has_rate, icon in inv_types:
        InvestmentType.objects.get_or_create(
            user=user, name=name,
            defaults={'has_maturity': has_mat, 'has_interest_rate': has_rate, 'icon': icon}
        )
