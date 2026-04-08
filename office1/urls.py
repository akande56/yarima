# office1/urls.py

from django.urls import path
from . import views

app_name = 'office1'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Transactions (Batch Management)
    path('transactions/', views.transaction_view, name='transactions'),

    # Receipt
    path('receipt/<int:transaction_id>/', views.receipt_view, name='receipt'),

    # Reject Batch
    path('transactions/reject/<int:batch_id>/', views.reject_batch, name='reject_batch'),
    
    # Delete Batch
    path('transactions/delete/<int:batch_id>/', views.delete_batch, name='delete_batch'),
]