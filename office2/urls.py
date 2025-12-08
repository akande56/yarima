# office2/urls.py

from django.urls import path
from . import views

app_name = 'office2'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Transaction (Batch) Management
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/api/<int:pk>/', views.transaction_detail_api, name='transaction_detail_api'),
    path('transactions/approve/<int:pk>/', views.approve_batch, name='approve_batch'),
    path('transactions/pay/<int:pk>/', views.pay_batch, name='pay_batch'),
]