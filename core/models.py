from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    month_start_day = models.IntegerField(default=1)
    currency_symbol = models.CharField(max_length=5, default='₹')

    def get_current_month_range(self):
        today = timezone.now().date()
        day = self.month_start_day
        if today.day >= day:
            start = today.replace(day=day)
        else:
            first = today.replace(day=1)
            prev_month = first - datetime.timedelta(days=1)
            try:
                start = prev_month.replace(day=day)
            except ValueError:
                start = prev_month.replace(day=prev_month.day)
        if start.month == 12:
            end_start = start.replace(year=start.year + 1, month=1)
        else:
            end_start = start.replace(month=start.month + 1)
        end = end_start - datetime.timedelta(days=1)
        return start, end


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


class InvestmentType(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    has_maturity = models.BooleanField(default=False)
    has_interest_rate = models.BooleanField(default=False)
    description = models.CharField(max_length=255, blank=True)
    icon = models.CharField(max_length=50, default='graph-up-arrow')

    class Meta:
        unique_together = ['user', 'name']
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    TYPE_CHOICES = [
        ('income', 'Income'), ('expense', 'Expense'),
        ('investment', 'Investment'), ('any', 'Any'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#6c757d')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='any')
    icon = models.CharField(max_length=50, default='tag')
    is_subscription = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'name']
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


TRANSACTION_TYPES = [
    ('income', 'Income'), ('expense', 'Expense'),
    ('side_income', 'Side Income'), ('investment', 'Investment'),
]


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    investment_type = models.ForeignKey(InvestmentType, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    raw_description = models.TextField(blank=True)
    is_subscription = models.BooleanField(default=False)
    from_pdf = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.date} - {self.amount}"

    @property
    def type_color(self):
        return {'income': '#198754', 'expense': '#dc3545',
                'side_income': '#0d6efd', 'investment': '#6f42c1'}.get(self.type, '#6c757d')

    @property
    def type_icon(self):
        return {'income': 'arrow-down-circle-fill', 'expense': 'arrow-up-circle-fill',
                'side_income': 'cash-stack', 'investment': 'graph-up'}.get(self.type, 'circle')


class Investment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    investment_type = models.ForeignKey(InvestmentType, on_delete=models.SET_NULL, null=True)
    amount_invested = models.DecimalField(max_digits=12, decimal_places=2)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    purchase_date = models.DateField()
    maturity_date = models.DateField(null=True, blank=True)
    interest_rate = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-purchase_date']

    def __str__(self):
        return self.name

    def days_to_maturity(self):
        if self.maturity_date:
            return (self.maturity_date - timezone.now().date()).days
        return None

    def expected_value_at_maturity(self):
        if self.interest_rate and self.maturity_date and self.purchase_date:
            years = (self.maturity_date - self.purchase_date).days / 365.0
            return float(self.amount_invested) * (1 + float(self.interest_rate) / 100) ** years
        return None

    def returns_percent(self):
        if self.current_value and float(self.amount_invested) > 0:
            return ((float(self.current_value) - float(self.amount_invested)) / float(self.amount_invested)) * 100
        return None

    def profit_loss(self):
        if self.current_value:
            return float(self.current_value) - float(self.amount_invested)
        return None


class MonthlyLimit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ['user', 'category']

    def __str__(self):
        return f"{self.category.name if self.category else 'Overall'}: {self.amount}"


class PurchasePlan(models.Model):
    PRIORITY_CHOICES = [('high', 'High'), ('medium', 'Medium'), ('low', 'Low')]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2)
    target_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    notes = models.TextField(blank=True)
    is_purchased = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_purchased', '-priority', 'target_date']

    def __str__(self):
        return self.name

    @property
    def priority_color(self):
        return {'high': 'danger', 'medium': 'warning', 'low': 'success'}.get(self.priority, 'secondary')


class Subscription(models.Model):
    CYCLE_CHOICES = [('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    billing_cycle = models.CharField(max_length=20, choices=CYCLE_CHOICES, default='monthly')
    next_billing_date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['next_billing_date']

    def __str__(self):
        return self.name

    def monthly_equivalent(self):
        return {'monthly': 1, 'quarterly': 1/3, 'yearly': 1/12}.get(self.billing_cycle, 1) * float(self.amount)

    def days_until_billing(self):
        return (self.next_billing_date - timezone.now().date()).days
