# utils/filters.py
from datetime import datetime
from django.utils import timezone
from decimal import Decimal
from core.models import MineralSale



def get_filtered_sales(request_get):
    """
    Reusable filter logic for both AJAX view and export.
    Takes request.GET or dict.
    """
    queryset = MineralSale.objects.select_related(
        'mineral_type', 'grade', 'processed_by'
    ).order_by('-sale_date')

    status = request_get.get('status')
    start_date = request_get.get('start_date')
    end_date = request_get.get('end_date')
    reference_number = request_get.get('reference_number', '').strip()

    if status:
        queryset = queryset.filter(status=status)

    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            start_dt = timezone.make_aware(datetime.combine(start.date(), datetime.min.time()))
            queryset = queryset.filter(sale_date__gte=start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end_dt = timezone.make_aware(datetime.combine(end.date(), datetime.max.time()))
            queryset = queryset.filter(sale_date__lte=end_dt)
        except ValueError:
            pass

    if reference_number:
        queryset = queryset.filter(reference_number__icontains=reference_number)

    return queryset