from django.urls import path
from . import views

app_name = 'office3'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('assign_role/', views.assign_role, name='assign_role'),
    path('minerals/', views.manage_minerals, name='manage_minerals'),
    
    
    # Transaction Management
    path('transactions/', views.transaction_list, name='transaction_list'), 
    path('transactions/export/', views.transaction_export, name='transaction_export'),

    # === Mineral & Grade API Endpoints ===
    path('api/minerals/', views.api_list_minerals, name='api_list_minerals'),
    path('api/minerals/create/', views.api_create_mineral, name='api_create_mineral'),
    path('api/minerals/<int:pk>/update/', views.api_update_mineral, name='api_update_mineral'),
    path('api/minerals/<int:pk>/delete/', views.api_delete_mineral, name='api_delete_mineral'),

    path('api/grades/', views.api_list_grades, name='api_list_grades'),
    path('api/grades/create/', views.api_create_grade, name='api_create_grade'),
    path('api/grades/<int:pk>/update/', views.api_update_grade, name='api_update_grade'),
    path('api/grades/<int:pk>/delete/', views.api_delete_grade, name='api_delete_grade'),

    #new mineral transaction endpoints
    path('sales/', views.sale_transaction_list, name='sale_transaction_list'),
    path('sales/data/', views.sale_transaction_data, name='sale_transaction_data'),
    path('sales/<int:pk>/detail/', views.sale_transaction_detail_api, name='sale_transaction_detail_api'),
    path('sales/<int:pk>/approve/', views.approve_sale_transaction, name='approve_sale_transaction'),
    path('sales/create/', views.sale_transaction_create, name='sale_transaction_create'),
    path('sales/create/submit/', views.sale_transaction_create_submit, name='sale_transaction_create_submit'),
    path('sales/export/', views.sale_transaction_export, name='sale_transaction_export'),
]
