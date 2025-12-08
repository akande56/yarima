# office3/views.py

import json
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from django.contrib import messages
from django.db.models import Sum, F, Case, When, DecimalField, Count
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
from django.db import transaction
import logging

from core.models import (
    MineralBatch,
    MineralItem,
    MineralType,
    MineralGrade,
    MineralSale,
    PaymentComponent,
)
from core.forms import MineralGradeForm, MineralTypeForm
from yarima_mining.users.models import User  # adjust import as needed
from .utils.exporter import TransactionExcelExporter, SaleTransactionExcelExporter
from .utils.filter import get_filtered_sales

logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
    if request.user.role != User.Roles.OFFICE_3:
        return redirect('dashboard_router')

    # KPIs
    total_batches = MineralBatch.objects.exclude(status='rejected').count()
    user_count = User.objects.exclude(role=User.Roles.UNASSIGNED).count()

    supplier_count = MineralBatch.objects.values('supplier_name').distinct().count()

    # PAID batches only
    paid_batches = MineralBatch.objects.filter(status='paid')

    # === KPI Calculations using correct model methods ===
    total_value = sum(batch.total_value() for batch in paid_batches)
    total_value = total_value.quantize(Decimal('0.00')) if total_value else Decimal('0.00')

    total_kg = sum(batch.total_original_kg() for batch in paid_batches)
    total_kg = total_kg.quantize(Decimal('0.00')) if total_kg else Decimal('0.00')

    total_lb = sum(batch.total_original_lb() for batch in paid_batches)
    total_lb = total_lb.quantize(Decimal('0.00')) if total_lb else Decimal('0.00')

    # Today's data
    today = timezone.now().date()
    today_paid_batches = paid_batches.filter(timestamp__date=today)

    today_total_value = sum(batch.total_value() for batch in today_paid_batches)
    today_total_value = today_total_value.quantize(Decimal('0.00')) if today_total_value else Decimal('0.00')

    today_total_kg = sum(batch.total_original_kg() for batch in today_paid_batches)
    today_total_kg = today_total_kg.quantize(Decimal('0.00')) if today_total_kg else Decimal('0.00')

    today_total_lb = sum(batch.total_original_lb() for batch in today_paid_batches)
    today_total_lb = today_total_lb.quantize(Decimal('0.00')) if today_total_lb else Decimal('0.00')

    # Recent batches
    recent_batches = MineralBatch.objects.select_related(
        'recorded_by', 'approved_by', 'paid_by'
    ).prefetch_related('items__mineral_type', 'items__grade').order_by('-timestamp')[:10]
    
    # Unassigned users
    unassigned_users = User.objects.filter(role=User.Roles.UNASSIGNED)

    return render(request, 'office3/dashboard.html', {
        'total_transactions': total_batches,
        'supplier_count': supplier_count,
        'user_count': user_count,
        'total_value': total_value,
        'total_kg': total_kg,
        'total_lb': total_lb,
        'today_total_value': today_total_value,
        'today_total_kg': today_total_kg,
        'today_total_lb': today_total_lb,
        'recent_transactions': recent_batches,
        'unassigned_users': unassigned_users,
    })

@login_required
def assign_role(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)

    if not (request.user.role == User.Roles.OFFICE_3 or request.user.is_superuser):
        return JsonResponse({"success": False, "message": "Permission denied."}, status=403)

    user_id = request.POST.get("user_id")
    role_selected = request.POST.get("office")

    valid_roles = {
        "office1": User.Roles.OFFICE_1,
        "office2": User.Roles.OFFICE_2,
    }

    if role_selected not in valid_roles:
        return JsonResponse({"success": False, "message": "Invalid role selected."}, status=400)

    user_to_assign = get_object_or_404(User, id=user_id)

    if user_to_assign.role != User.Roles.UNASSIGNED:
        return JsonResponse({"success": False, "message": f"{user_to_assign.name} already has a role."}, status=400)

    user_to_assign.role = valid_roles[role_selected]
    user_to_assign.save()

    return JsonResponse({
        "success": True,
        "message": f"{user_to_assign.name} assigned to {valid_roles[role_selected].label}."
    }, status=200)


### Manage Minerals ###

@login_required
def manage_minerals(request):
    minerals = MineralType.objects.prefetch_related('grades').all()
    mineral_form = MineralTypeForm()
    grade_form = MineralGradeForm()

    context = {
        'minerals': minerals,
        'mineral_form': mineral_form,
        'grade_form': grade_form,
    }
    return render(request, 'office3/manage_minerals.html', context)


# office3/views.py

@login_required
def transaction_list(request):
    """
    Display filtered list of mineral batches with KPIs.
    Supports filtering by date range and mineral type.
    Only shows PAID batches.
    """
    # Base queryset
    queryset = MineralBatch.objects.select_related(
        'recorded_by', 'approved_by', 'paid_by'
    ).prefetch_related('items__mineral_type', 'items__grade').filter(status='paid').order_by('-timestamp')

    # Get filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    mineral_type_id = request.GET.get('mineral_type', '')

    today = timezone.now().date()

    # Apply date_from
    if date_from:
        try:
            dt = datetime.fromisoformat(date_from)
            queryset = queryset.filter(timestamp__date__gte=dt.date())
        except ValueError:
            pass
    else:
        queryset = queryset.filter(timestamp__date__gte=today)

    # Apply date_to
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            queryset = queryset.filter(timestamp__date__lte=dt.date())
        except ValueError:
            pass
    else:
        queryset = queryset.filter(timestamp__date__lte=today)

    # Apply mineral type filter
    if mineral_type_id:
        try:
            mineral_type_id = int(mineral_type_id)
            queryset = queryset.filter(items__mineral_type_id=mineral_type_id).distinct()
        except (ValueError, TypeError):
            pass

    # === KPIs: Use original recorded units ===
    total_kg = sum(batch.total_original_kg() for batch in queryset)
    total_lb = sum(batch.total_original_lb() for batch in queryset)
    total_value = sum(batch.total_value() for batch in queryset)

    total_kg = Decimal(str(total_kg)) if total_kg else Decimal('0.00')
    total_lb = Decimal(str(total_lb)) if total_lb else Decimal('0.00')
    total_value = Decimal(str(total_value)) if total_value else Decimal('0.00')

    total_kg = total_kg.quantize(Decimal('0.00'))
    total_lb = total_lb.quantize(Decimal('0.00'))
    total_value = total_value.quantize(Decimal('0.00'))

    # Pagination
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page')
    batches = paginator.get_page(page_number)

    # All mineral types for dropdown
    mineral_types = MineralType.objects.all().order_by('name')

    context = {
        'batches': batches,
        'date_from': date_from,
        'date_to': date_to,
        'mineral_type_id': mineral_type_id,
        'mineral_types': mineral_types,
        'total_kg': total_kg,
        'total_lb': total_lb,
        'total_value': total_value,
        'total_transactions': queryset.count(),
    }

    return render(request, 'office3/transaction_list.html', context)




@login_required
def transaction_export(request):
    """
    Export filtered mineral batches to Excel.
    Supports: date_from, date_to, mineral_type
    """
    try:
        queryset = MineralBatch.objects.filter(status='paid').select_related(
            'recorded_by', 'approved_by', 'paid_by'
        ).prefetch_related(
            'items__mineral_type',
            'items__grade',
            'payments'
        ).order_by('-timestamp')

        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')

        if date_from:
            try:
                d = datetime.fromisoformat(date_from)
                start_dt = make_aware(datetime.combine(d, datetime.min.time()))
                queryset = queryset.filter(timestamp__gte=start_dt)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid date_from='{date_from}': {e}")

        if date_to:
            try:
                d = datetime.fromisoformat(date_to)
                end_dt = make_aware(datetime.combine(d, datetime.max.time()))
                queryset = queryset.filter(timestamp__lte=end_dt)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid date_to='{date_to}': {e}")

        mineral_type_id = request.GET.get('mineral_type')
        if mineral_type_id:
            try:
                mineral_type_id = int(mineral_type_id)
                queryset = queryset.filter(items__mineral_type_id=mineral_type_id).distinct()
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid mineral_type_id='{mineral_type_id}': {e}")

        exporter = TransactionExcelExporter()
        return exporter.export_to_response(queryset)

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        return JsonResponse({'error': 'Export failed due to an internal error.'}, status=500)


### API: Mineral Management ###

@login_required
def api_list_minerals(request):
    minerals = MineralType.objects.all().values('id', 'name', 'description')
    return JsonResponse(list(minerals), safe=False)


@csrf_exempt
@login_required
def api_create_mineral(request):
    if request.method == 'POST':
        try:
            form = MineralTypeForm(request.POST)
            if form.is_valid():
                mineral = form.save()
                return JsonResponse({
                    'id': mineral.id,
                    'name': mineral.name,
                    'description': mineral.description
                })
            else:
                return JsonResponse({'error': 'Invalid data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid method'}, status=405)


@csrf_exempt
@login_required
def api_update_mineral(request, pk):
    mineral = get_object_or_404(MineralType, pk=pk)
    if request.method == 'POST':
        form = MineralTypeForm(request.POST, instance=mineral)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'id': mineral.id,
                'name': mineral.name,
                'description': mineral.description
            })
        else:
            return JsonResponse({'error': 'Invalid data'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)


@csrf_exempt
@login_required
def api_delete_mineral(request, pk):
    mineral = get_object_or_404(MineralType, pk=pk)
    if request.method == 'POST':
        name = mineral.name
        mineral.delete()
        return JsonResponse({'message': f'{name} deleted successfully'})
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
def api_list_grades(request):
    grades = MineralGrade.objects.select_related('mineral').values(
        'id', 'mineral__id', 'mineral__name', 'grade_name',
        'price_per_pound', 'price_per_kg'
    )
    data = [
        {
            'id': g['id'],
            'mineral_id': g['mineral__id'],
            'mineral_name': g['mineral__name'],
            'grade_name': g['grade_name'],
            'price_per_pound': float(g['price_per_pound']) if g['price_per_pound'] is not None else None,
            'price_per_kg': float(g['price_per_kg']) if g['price_per_kg'] is not None else None,
        }
        for g in grades
    ]
    return JsonResponse(data, safe=False)


@csrf_exempt
@login_required
def api_create_grade(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mineral_id = data.get('mineral')
            grade_name = data.get('grade_name')
            price_per_pound = data.get('price_per_pound')
            price_per_kg = data.get('price_per_kg')

            mineral = get_object_or_404(MineralType, id=mineral_id)

            if price_per_kg is not None and price_per_pound is not None:
                return JsonResponse({'error': 'Cannot set both price_per_kg and price_per_pound.'}, status=400)
            if price_per_kg is None and price_per_pound is None:
                return JsonResponse({'error': 'Either price_per_kg or price_per_pound must be set.'}, status=400)

            if MineralGrade.objects.filter(mineral=mineral, grade_name=grade_name).exists():
                return JsonResponse({'error': 'Grade already exists for this mineral.'}, status=400)

            grade = MineralGrade.objects.create(
                mineral=mineral,
                grade_name=grade_name,
                price_per_pound=price_per_pound,
                price_per_kg=price_per_kg
            )

            return JsonResponse({
                'id': grade.id,
                'mineral_id': grade.mineral.id,
                'mineral_name': grade.mineral.name,
                'grade_name': grade.grade_name,
                'price_per_pound': float(grade.price_per_pound) if grade.price_per_pound else None,
                'price_per_kg': float(grade.price_per_kg) if grade.price_per_kg else None,
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid method'}, status=405)


@csrf_exempt
@login_required
def api_update_grade(request, pk):
    grade = get_object_or_404(MineralGrade, pk=pk)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mineral_id = data.get('mineral')
            grade_name = data.get('grade_name')
            price_per_pound = data.get('price_per_pound')
            price_per_kg = data.get('price_per_kg')

            mineral = get_object_or_404(MineralType, id=mineral_id)

            if price_per_kg is not None and price_per_pound is not None:
                return JsonResponse({'error': 'Cannot set both price_per_kg and price_per_pound.'}, status=400)
            if price_per_kg is None and price_per_pound is None:
                return JsonResponse({'error': 'Either price_per_kg or price_per_pound must be set.'}, status=400)

            if MineralGrade.objects.filter(mineral=mineral, grade_name=grade_name).exclude(id=pk).exists():
                return JsonResponse({'error': 'Grade already exists for this mineral.'}, status=400)

            grade.mineral = mineral
            grade.grade_name = grade_name
            grade.price_per_pound = price_per_pound
            grade.price_per_kg = price_per_kg
            grade.save()

            return JsonResponse({
                'id': grade.id,
                'mineral_id': grade.mineral.id,
                'mineral_name': grade.mineral.name,
                'grade_name': grade.grade_name,
                'price_per_pound': float(grade.price_per_pound) if grade.price_per_pound else None,
                'price_per_kg': float(grade.price_per_kg) if grade.price_per_kg else None,
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid method'}, status=405)


@csrf_exempt
@login_required
def api_delete_grade(request, pk):
    grade = get_object_or_404(MineralGrade, pk=pk)
    if request.method == 'POST':
        name = grade.grade_name
        grade.delete()
        return JsonResponse({'message': f'{name} deleted successfully'})
    return JsonResponse({'error': 'Invalid method'}, status=405)


### Sale Transaction Management ###

def convert_weight(quantity, unit, target_unit):
    if unit == target_unit:
        return quantity
    if unit == 'kg' and target_unit == 'lb':
        return quantity * Decimal('2.20462')
    if unit == 'lb' and target_unit == 'kg':
        return quantity / Decimal('2.20462')
    return quantity


@login_required
def sale_transaction_list(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return sale_transaction_data(request)
    return render(request, 'office3/sale_transaction_list.html')


@login_required
def sale_transaction_data(request):
    # Use shared filter
    queryset = get_filtered_sales(request.GET)

    # === KPIs: Separate original units ===
    totals = queryset.aggregate(
        total_count=Count('id'),
        total_kg=Sum(
            Case(
                When(quantity_unit='kg', then=F('quantity')),
                output_field=DecimalField()
            )
        ),
        total_lb=Sum(
            Case(
                When(quantity_unit='lb', then=F('quantity')),
                output_field=DecimalField()
            )
        ),
        total_value=Sum('total_price')
    )

    # Format totals
    total_kg = totals['total_kg'] or Decimal('0.00')
    total_lb = totals['total_lb'] or Decimal('0.00')
    total_value = totals['total_value'] or Decimal('0.00')

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    rows_html = render_to_string('office3/_sale_transaction_rows.html', {'page_obj': page_obj}, request=request)
    pagination_html = render_to_string('office3/_pagination.html', {'page_obj': page_obj}, request=request)

    return JsonResponse({
        'rows_html': rows_html,
        'pagination_html': pagination_html,
        'pagination_info': f"Showing {page_obj.start_index()} to {page_obj.end_index()} of {page_obj.paginator.count}",
        'kpis': {
            'total_count': int(totals['total_count']),
            'total_kg': round(float(total_kg), 2),
            'total_lb': round(float(total_lb), 2),
            'total_value': round(float(total_value), 2),
        }
    })


@require_http_methods(["GET"])
def sale_transaction_detail_api(request, pk):
    transaction = get_object_or_404(MineralSale, pk=pk)
    recorded_by = transaction.processed_by
    recorded_by_name = recorded_by.get_full_name().strip() if recorded_by else ''
    if not recorded_by_name:
        recorded_by_name = recorded_by.username if recorded_by else 'Unknown'

    grade_name = transaction.grade.grade_name if transaction.grade else 'N/A'

    return JsonResponse({
        'id': transaction.id,
        'reference_number': transaction.reference_number,
        'mineral_type': transaction.mineral_type.name,
        'grade': grade_name,
        'buyer_name': transaction.buyer_name,
        'quantity': str(transaction.quantity),
        'quantity_unit': transaction.quantity_unit,
        'total_price': str(transaction.total_price),
        'sale_date': transaction.sale_date.isoformat(),
        'status': transaction.status,
        'price_per_unit': str(transaction.price_per_unit),
        'notes': transaction.notes or '',
        'processed_by': recorded_by_name,
        'buyer_contact': transaction.buyer_contact or 'N/A',
        # === New ID Fields ===
        'bvn': transaction.bvn or 'N/A',
        'nin': transaction.nin or 'N/A',
        'international_id': transaction.international_id or 'N/A',
        'driver_license': transaction.driver_license or 'N/A',
    })


@csrf_exempt
@require_http_methods(["POST"])
def approve_sale_transaction(request, pk):
    transaction = get_object_or_404(MineralSale, pk=pk)
    if transaction.status != 'pending':
        return JsonResponse({'success': False, 'error': 'Only pending transactions can be approved.'}, status=400)

    transaction.status = 'paid'
    transaction.save()
    return JsonResponse({'success': True})


@login_required
def sale_transaction_create(request):
    mineral_types = MineralType.objects.prefetch_related('grades').all()
    return render(request, 'office3/sale_transaction_create.html', {
        'mineral_types': mineral_types,
        'title': 'Create New Sale Transaction'
    })


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def sale_transaction_create_submit(request):
    try:
        data = json.loads(request.body)

        # Required fields validation
        required = ['mineral_type_id', 'grade_id', 'buyer_name', 'quantity', 'quantity_unit', 'price_per_unit']
        for field in required:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'{field.replace("_", " ").title()} is required.'
                })

        mineral_type = get_object_or_404(MineralType, id=int(data['mineral_type_id']))
        grade = get_object_or_404(MineralGrade, id=int(data['grade_id']))

        try:
            quantity = Decimal(data['quantity'])
            price_per_unit = Decimal(data['price_per_unit'])
        except (ValueError, TypeError, InvalidOperation):
            return JsonResponse({
                'success': False,
                'error': 'Invalid number format for quantity or price.'
            })

        if quantity <= 0:
            return JsonResponse({'success': False, 'error': 'Quantity must be greater than zero.'})
        if price_per_unit <= 0:
            return JsonResponse({'success': False, 'error': 'Price per unit must be greater than zero.'})

        # Parse sale date
        sale_date_str = data.get('sale_date')
        if sale_date_str:
            try:
                sale_date = datetime.fromisoformat(sale_date_str)
                if timezone.is_naive(sale_date):
                    sale_date = timezone.make_aware(sale_date)
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid date format.'})
        else:
            sale_date = timezone.now()

        # Clean and conditionally save ID fields (only if non-empty)
        def clean_or_none(value):
            cleaned = str(value).strip() if value else ''
            return cleaned if cleaned else None

        with transaction.atomic():
            sale = MineralSale.objects.create(
                mineral_type=mineral_type,
                grade=grade,
                quantity=quantity,
                quantity_unit=data['quantity_unit'],
                price_per_unit=price_per_unit,
                buyer_name=data['buyer_name'].strip(),
                buyer_contact=clean_or_none(data.get('buyer_contact')),
                sale_date=sale_date,
                processed_by=request.user,
                status='pending',
                notes=clean_or_none(data.get('notes')),

                # Optional IDs
                bvn=clean_or_none(data.get('bvn')),
                nin=clean_or_none(data.get('nin')),
                international_id=clean_or_none(data.get('international_id')),
                driver_license=clean_or_none(data.get('driver_license')),
            )

        return JsonResponse({
            'success': True,
            'id': sale.id,
            'reference_number': sale.reference_number,
            'redirect_url': f"/office3/sales/?status=pending"
        })

    except Exception as e:
        logger.error("Error creating sale: ", exc_info=True)
        return JsonResponse({'success': False, 'error': 'An internal error occurred. Please try again.'})


@login_required
def sale_transaction_export(request):
    
    try:
        # Use the same filter logic
        queryset = get_filtered_sales(request.GET)

        exporter = SaleTransactionExcelExporter()
        return exporter.export_to_response(queryset)

    except Exception as e:
        logger.error("Export failed: ", exc_info=True)
        return JsonResponse({'error': f"Export failed: {str(e)}"}, status=500)