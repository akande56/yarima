# core/views.py
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db.models import Sum, F
from yarima_mining.users.models import User  # Adjust import as needed

from .models import MineralBatch, MineralItem, MineralType, MineralGrade


@login_required
def dashboard_router(request):
    """Redirect user to their office-specific dashboard based on role."""
    user = request.user

    if user.role == User.Roles.OFFICE_1:
        return redirect('office1:dashboard')
    elif user.role == User.Roles.OFFICE_2:
        return redirect('office2:dashboard')
    elif user.role == User.Roles.OFFICE_3:
        return redirect('office3:dashboard')
    elif user.role == User.Roles.OFFICE_4:
        return redirect('office4:dashboard')
    elif user.is_superuser:
        return redirect('admin:index')
    else:
        return HttpResponseForbidden("Access denied.")





def today_analysis_view(request):
    """
    KPI dashboard for today's PAID mineral batches.
    Shows per-mineral KPIs including:
      - kg (original)
      - lb (raw)
      - converted_kg (from lb)
      - converted_lb (from kg)
      - total_value
    """
    # Use Decimal for all accumulators
    ZERO = Decimal('0.00')

    # Get today's date in local timezone
    today = timezone.localtime(timezone.now()).date()
    start_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
    end_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))

    # Filter MineralItems from batches that are 'paid' and received today
    paid_items = MineralItem.objects.filter(
        batch__status='paid',
        batch__timestamp__range=(start_of_day, end_of_day)
    ).select_related('mineral_type', 'grade', 'batch')

    # Compute KPIs per mineral type
    kpi_data = {}
    for item in paid_items:
        mineral = item.mineral_type
        if mineral not in kpi_data:
            kpi_data[mineral] = {
                'kg_original': ZERO,      # kg entered directly
                'lb_raw': ZERO,           # lb entered directly
                'converted_kg': ZERO,     # TOTAL in kg (kg + lb→kg)
                'converted_lb': ZERO,     # TOTAL in lb (lb + kg→lb)
                'total_value': ZERO,
            }

        weight = item.weight

        if item.weight_unit == 'kg':
            kpi_data[mineral]['kg_original'] += weight
            # Add to total kg
            kpi_data[mineral]['converted_kg'] += weight
            # Convert to lb and add to total lb
            kpi_data[mineral]['converted_lb'] += weight * Decimal('2.20462')
        elif item.weight_unit == 'lb':
            kpi_data[mineral]['lb_raw'] += weight
            # Convert to kg and add to total kg
            kpi_data[mineral]['converted_kg'] += weight * Decimal('0.453592')
            # Add to total lb
            kpi_data[mineral]['converted_lb'] += weight

        # Add value
        kpi_data[mineral]['total_value'] += item.total_value

    # Convert to list for template (rounding at presentation layer)
    kpi_list = [
        {
            'mineral': mineral,
            'kg_original': round(float(data['kg_original']), 2),
            'lb_raw': round(float(data['lb_raw']), 2),
            'converted_kg': round(float(data['converted_kg']), 2),
            'converted_lb': round(float(data['converted_lb']), 2),
            'total_value': round(float(data['total_value']), 2),
        }
        for mineral, data in kpi_data.items()
    ]

    # All mineral types and grades for future filtering (optional)
    all_minerals = MineralType.objects.all()
    all_grades = MineralGrade.objects.select_related('mineral').all()

    context = {
        'kpi_list': kpi_list,
        'all_minerals': all_minerals,
        'all_grades': all_grades,
    }

    return render(request, 'core/today_analysis.html', context)