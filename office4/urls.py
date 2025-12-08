from django.urls import path
from . import views

app_name = 'office4'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    
    # Transaction Management
    path('transactions/', views.transaction_list, name='transaction_list'), 
    path('transactions/export/', views.transaction_export, name='transaction_export'),

    #new mineral transaction endpoints
    path('sales/', views.sale_transaction_list, name='sale_transaction_list'),
    path('sales/data/', views.sale_transaction_data, name='sale_transaction_data'),
    path('sales/<int:pk>/detail/', views.sale_transaction_detail_api, name='sale_transaction_detail_api'),
    path('sales/export/', views.sale_transaction_export, name='sale_transaction_export'),

    # Main invoice list (with AJAX modal actions)
    path('invoices/', views.invoice_list, name='invoice_list'),

    # AJAX Create or Update (used by modal)
    path('invoices/save/', views.invoice_create_or_update, name='invoice_create_or_update'),

    path('invoices/delete/', views.invoice_delete, name='invoice_delete'),

    # Export to Excel
    path('invoices/export/', views.invoice_export, name='invoice_export'),

]
