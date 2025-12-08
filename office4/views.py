# office4/views.py

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
from django.db.models import (
    Count, 
    F, 
    Sum,
    DecimalField, 
    Case, 
    When, 
    Q,
)
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
import logging

from core.models import (
    MineralBatch,
    MineralItem,
    MineralSale,
    MineralType
)

from yarima_mining.users.models import User  
from office3.utils.exporter import TransactionExcelExporter, SaleTransactionExcelExporter

from .models import Invoice, ExpenseItem
from .utils.exporter import InvoiceExcelExporter
from .utils.filter import get_filtered_sales


logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
    if request.user.role != User.Roles.OFFICE_4:
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

    return render(request, 'office4/dashboard.html', {
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

    return render(request, 'office4/transaction_list.html', context)


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




# Helper to convert weight
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
    # This view serves both HTML and AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return sale_transaction_data(request)

    return render(request, 'office4/sale_transaction_list.html')



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

    rows_html = render_to_string('office4/_sale_transaction_rows.html', {'page_obj': page_obj}, request=request)
    pagination_html = render_to_string('office4/_pagination.html', {'page_obj': page_obj}, request=request)

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

    # Safely get recorded_by name
    recorded_by = transaction.processed_by  # Correct field name: processed_by
    recorded_by_name = recorded_by.get_full_name().strip() if recorded_by else ''
    if not recorded_by_name:
        recorded_by_name = recorded_by.username if recorded_by else 'Unknown'

    # Safely get grade name
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
        'status_display': transaction.get_status_display(),
        'processed_by': recorded_by_name,
        'buyer_contact': transaction.buyer_contact or 'N/A',
    })






# @login_required
# def sale_transaction_detail(request, pk):
#     """
#     Returns the transaction details as HTML fragment for modal.
#     """
#     transaction = get_object_or_404(MineralSale, pk=pk)
#     return render(request, 'office4/_transaction_detail.html', {'transaction': transaction})




@login_required
def sale_transaction_export(request):
    """
    Export filtered MineralSale records to Excel.
    Uses the shared get_filtered_sales() for consistency with UI filters.
    """
    try:
        # Apply filters using shared logic
        queryset = get_filtered_sales(request.GET)

        # === Optional: Log export event ===
        count = queryset.count()
        filters = dict(request.GET.items())
        logger.info(
            f"User '{request.user}' exported {count} sale(s). "
            f"Filters: {filters}"
        )

        # If no data, return 404 instead of empty Excel
        if not queryset.exists():
            return HttpResponse(
                "No sales match the selected filters.",
                content_type="text/plain",
                status=404
            )

        # Use enhanced exporter
        exporter = SaleTransactionExcelExporter()
        return exporter.export_to_response(queryset)

    except Exception as e:
        logger.error("Sale transaction export failed", exc_info=True)
        return JsonResponse({'error': f"Export failed: {str(e)}"}, status=500)



#invoice
@login_required
def invoice_list(request):
    # Get filter parameters
    time_filter = request.GET.get('time', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    # Base queryset
    queryset = Invoice.objects.prefetch_related('items').order_by('-payment_date')

    # Apply time filter (shortcut)
    now = timezone.now()
    if time_filter == 'today':
        queryset = queryset.filter(payment_date=now.date())
    elif time_filter == 'week':
        start = (now - timezone.timedelta(days=7)).date()
        queryset = queryset.filter(payment_date__gte=start)
    elif time_filter == 'month':
        start = now.replace(day=1).date()
        queryset = queryset.filter(payment_date__gte=start)
    elif time_filter == 'year':
        start = now.replace(month=1, day=1).date()
        queryset = queryset.filter(payment_date__gte=start)

    # Apply custom date range (overrides time_filter if used)
    if from_date:
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
            queryset = queryset.filter(payment_date__gte=from_dt)
        except ValueError:
            pass  # Ignore invalid date

    if to_date:
        try:
            to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
            queryset = queryset.filter(payment_date__lte=to_dt)
        except ValueError:
            pass  # Ignore invalid date

    # KPIs
    total_invoices = queryset.count()
    total_expenses = sum(
        item.amount for inv in queryset for item in inv.items.all()
    )

    # Pagination
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page')
    invoices = paginator.get_page(page_number)

    # Add total_amount to each invoice
    for inv in invoices:
        total = inv.items.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        inv.total_amount = float(total)

    # Serialize for JS (modal, etc.)
    invoices_data = []
    for inv in invoices:
        items = [{'category': item.category, 'amount': float(item.amount)} for item in inv.items.all()]
        invoices_data.append({
            'id': inv.id,
            'sn': inv.sn,
            'expense_type': inv.expense_type,
            'vendor_supplier': inv.vendor_supplier,
            'payment_method': inv.payment_method,
            'payment_date': inv.payment_date.isoformat() if inv.payment_date else '',
            'description': inv.description or '',
            'remark': inv.remark or '',
            'total_amount': float(sum(item['amount'] for item in items)),
            'items': items,
        })

    context = {
        'invoices': invoices,
        'invoices_json': json.dumps(invoices_data),
        'total_expenses': float(total_expenses),
        'total_invoices': total_invoices,
        'selected_time': time_filter,
        'from_date': from_date,
        'to_date': to_date,
        'CATEGORY_CHOICES': ExpenseItem.CATEGORY_CHOICES,
    }
    return render(request, 'office4/invoice_list.html', context)


@login_required
def invoice_create_or_update(request):
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            invoice_id = data.get('id')

            with transaction.atomic():
                if invoice_id:
                    invoice = get_object_or_404(Invoice, id=invoice_id)
                else:
                    invoice = Invoice()

                invoice.expense_type = data['expense_type']
                invoice.vendor_supplier = data.get('vendor_supplier', '')
                invoice.payment_method = data.get('payment_method', '')
                invoice.payment_date = data['payment_date']
                invoice.description = data.get('description', '')
                invoice.remark = data.get('remark', '')
                invoice.save()

                # Clear and recreate items
                invoice.items.all().delete()
                for item in data['items']:
                    if item['category'] and item['amount']:
                        ExpenseItem.objects.create(
                            invoice=invoice,
                            category=item['category'],
                            amount=Decimal(str(item['amount']))
                        )

            return JsonResponse({
                'success': True,
                'message': f"Invoice #{invoice.sn} saved successfully.",
                'invoice': {
                    'id': invoice.id,
                    'sn': invoice.sn,
                    'total_amount': float(sum(item.amount for item in invoice.items.all())),
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid method'}, status=405)


# office4/views.py
@login_required
def invoice_export(request):
    try:
        time_filter = request.GET.get('time', '')
        from_date = request.GET.get('from_date', '')
        to_date = request.GET.get('to_date', '')

        queryset = Invoice.objects.prefetch_related('items').order_by('-payment_date')

        # Apply same filters as list view
        now = timezone.now()
        if time_filter == 'today':
            queryset = queryset.filter(payment_date=now.date())
        elif time_filter == 'week':
            start = (now - timezone.timedelta(days=7)).date()
            queryset = queryset.filter(payment_date__gte=start)
        elif time_filter == 'month':
            start = now.replace(day=1).date()
            queryset = queryset.filter(payment_date__gte=start)
        elif time_filter == 'year':
            start = now.replace(month=1, day=1).date()
            queryset = queryset.filter(payment_date__gte=start)

        if from_date:
            try:
                from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
                queryset = queryset.filter(payment_date__gte=from_dt)
            except ValueError:
                pass

        if to_date:
            try:
                to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
                queryset = queryset.filter(payment_date__lte=to_dt)
            except ValueError:
                pass

        exporter = InvoiceExcelExporter()
        return exporter.export_to_response(queryset)

    except Exception as e:
        import logging
        logging.error(f"Invoice export failed: {e}")
        response = HttpResponse("Export failed.", content_type="text/plain")
        response['Content-Disposition'] = 'attachment; filename="error.txt"'
        return response
    

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def invoice_delete(request):
    """
    Delete an invoice and its associated expense items.
    Expects JSON payload with 'id' of the invoice.
    """
    try:
        data = json.loads(request.body)
        invoice_id = data.get("id")

        if not invoice_id:
            return JsonResponse({
                "success": False,
                "error": "Invoice ID is required."
            }, status=400)

        invoice = get_object_or_404(Invoice, id=invoice_id)

        # Store sn for success message before deletion
        invoice_sn = invoice.sn

        # Delete the invoice (and related ExpenseItems via CASCADE)
        invoice.delete()

        return JsonResponse({
            "success": True,
            "message": f"Invoice #{invoice_sn} deleted successfully."
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)