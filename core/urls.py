from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path('dashboard/', views.dashboard_router, name='dashboard_router'),
    path('today-analysis/', views.today_analysis_view, name='today_analysis'),
]
