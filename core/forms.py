from django import forms
from .models import (Transaction, Investment, InvestmentType, Category,
                     MonthlyLimit, PurchasePlan, Subscription, UserProfile)
from django.contrib.auth.models import User


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['month_start_day', 'currency_symbol', 'theme']
        widgets = {
            'month_start_day': forms.NumberInput(attrs={'min': 1, 'max': 28, 'class': 'form-control'}),
            'currency_symbol': forms.TextInput(attrs={'class': 'form-control'}),
            'theme': forms.Select(attrs={'class': 'form-select'}),
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'amount', 'type', 'category', 'investment_type', 'notes', 'is_subscription']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'investment_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_subscription': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)
        self.fields['category'].empty_label = '— Select Category —'
        self.fields['category'].required = False
        self.fields['investment_type'].queryset = InvestmentType.objects.filter(user=user)
        self.fields['investment_type'].empty_label = '— Specific Investment Type —'
        self.fields['investment_type'].required = False


class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = ['name', 'investment_type', 'amount_invested', 'current_value',
                  'purchase_date', 'maturity_date', 'interest_rate', 'notes', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'investment_type': forms.Select(attrs={'class': 'form-select'}),
            'amount_invested': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'purchase_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'maturity_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': '% per annum'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['investment_type'].queryset = InvestmentType.objects.filter(user=user)
        self.fields['maturity_date'].required = False
        self.fields['interest_rate'].required = False
        self.fields['current_value'].required = False


class InvestmentTypeForm(forms.ModelForm):
    class Meta:
        model = InvestmentType
        fields = ['name', 'has_maturity', 'has_interest_rate', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control icon-picker-input', 'placeholder': 'Bootstrap icon name'}),
            'has_maturity': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_interest_rate': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'color', 'type', 'icon', 'is_subscription']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'icon': forms.TextInput(attrs={'class': 'form-control icon-picker-input', 'placeholder': 'e.g. cart, phone, heart'}),
            'is_subscription': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MonthlyLimitForm(forms.ModelForm):
    class Meta:
        model = MonthlyLimit
        fields = ['category', 'amount']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user, type__in=['expense', 'any'])
        self.fields['category'].empty_label = '— Overall Budget —'
        self.fields['category'].required = False


class PurchasePlanForm(forms.ModelForm):
    class Meta:
        model = PurchasePlan
        fields = ['name', 'estimated_cost', 'target_date', 'priority', 'notes', 'is_purchased']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_purchased': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['name', 'amount', 'billing_cycle', 'next_billing_date', 'category', 'is_active', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'billing_cycle': forms.Select(attrs={'class': 'form-select'}),
            'next_billing_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)
        self.fields['category'].empty_label = '— No Category —'
        self.fields['category'].required = False


class PDFUploadForm(forms.Form):
    pdf_file = forms.FileField(
        label='Bank Statement PDF',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'})
    )
    bank_name = forms.ChoiceField(
        choices=[('icici', 'ICICI Bank'), ('hdfc', 'HDFC Bank'), ('sbi', 'SBI'), ('other', 'Other / Auto-detect')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
