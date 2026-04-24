from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Transactions
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/add/', views.transaction_add, name='transaction_add'),
    path('transactions/<int:pk>/edit/', views.transaction_edit, name='transaction_edit'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    path('transactions/bulk-categorize/', views.bulk_categorize, name='bulk_categorize'),
    
    # Investments
    path('investments/', views.investment_list, name='investment_list'),
    path('investments/add/', views.investment_add, name='investment_add'),
    path('investments/<int:pk>/edit/', views.investment_edit, name='investment_edit'),
    path('investments/<int:pk>/delete/', views.investment_delete, name='investment_delete'),
    path('investments/types/', views.investment_type_list, name='investment_type_list'),
    path('investments/types/<int:pk>/delete/', views.investment_type_delete, name='investment_type_delete'),
    
    # Analytics
    path('analytics/', views.analytics, name='analytics'),
    
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Limits
    path('limits/', views.limit_list, name='limit_list'),
    path('limits/<int:pk>/edit/', views.limit_edit, name='limit_edit'),
    path('limits/<int:pk>/delete/', views.limit_delete, name='limit_delete'),
    
    # Subscriptions
    path('subscriptions/', views.subscription_list, name='subscription_list'),
    path('subscriptions/add/', views.subscription_add, name='subscription_add'),
    path('subscriptions/<int:pk>/edit/', views.subscription_edit, name='subscription_edit'),
    path('subscriptions/<int:pk>/delete/', views.subscription_delete, name='subscription_delete'),
    
    # Savings & Plans
    path('savings/', views.savings_dashboard, name='savings_dashboard'),
    path('savings/plans/<int:pk>/edit/', views.plan_edit, name='plan_edit'),
    path('savings/plans/<int:pk>/delete/', views.plan_delete, name='plan_delete'),
    path('savings/plans/<int:pk>/toggle/', views.plan_toggle, name='plan_toggle'),
    
    # Summary
    path('summary/', views.summary, name='summary'),
    
    # PDF Upload
    path('upload/', views.upload_pdf, name='upload_pdf'),
    path('upload/preview/', views.pdf_preview, name='pdf_preview'),
    
    # Settings
    path('settings/', views.user_settings, name='user_settings'),
]
