from django.contrib import admin
from .models import (UserProfile, InvestmentType, Category, Transaction,
                     Investment, MonthlyLimit, PurchasePlan, Subscription)

admin.site.register(UserProfile)
admin.site.register(InvestmentType)
admin.site.register(Category)
admin.site.register(Transaction)
admin.site.register(Investment)
admin.site.register(MonthlyLimit)
admin.site.register(PurchasePlan)
admin.site.register(Subscription)
