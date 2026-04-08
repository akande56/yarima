# office1/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
from django.utils.timezone import now
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import HttpResponse

from datetime import datetime

from core.models import (
    MineralBatch,
    MineralItem,
    MineralType,
    MineralGrade,
    TransactionStatusLog
)
from .utils.receipt_generator import generate_receipt_pdf
import json


@login_required
def dashboard(request):
    user = request.user
    if not hasattr(user, 'role') or user.role != user.Roles.OFFICE_1:
        return redirect('dashboard_router')

    today = now().date()
    batches = MineralBatch.objects.filter(recorded_by=user, timestamp__date=today).exclude(status='rejected')

    total_weight_kg = sum(b.total_original_kg() for b in batches)
    total_weight_lb = sum(b.total_original_lb() for b in batches)
    pending_count = batches.filter(status='pending').count()
    recent_batches = MineralBatch.objects.filter(recorded_by=user).order_by('-timestamp')[:10]

    context = {
        "total_weight_kg": round(total_weight_kg, 2),
        "total_weight_lb": round(total_weight_lb, 2),
        "pending_count": pending_count,
        "batch_count": batches.count(),
        "recent_batches": recent_batches,
    }
    return render(request, "office1/dashboard.html", context)


@require_http_methods(["GET", "POST"])
@csrf_exempt
@login_required
def transaction_view(request):
    user = request.user
    allowed_roles = {user.Roles.OFFICE_1, user.Roles.OFFICE_2}
    if not hasattr(user, "role") or user.role not in allowed_roles:
        return redirect("dashboard_router")

    mineral_types = MineralType.objects.prefetch_related('grades').all()

    # Base queryset
    batches = MineralBatch.objects.filter(recorded_by=user).order_by('-timestamp')

    # Get filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    mineral_type_id = request.GET.get('mineral_type', '')

    # Apply date filters
    if date_from:
        try:
            dt = datetime.strptime(date_from, '%Y-%m-%d')
            batches = batches.filter(timestamp__date__gte=dt.date())
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, '%Y-%m-%d')
            batches = batches.filter(timestamp__date__lte=dt.date())
        except ValueError:
            pass

    # Apply mineral filter
    if mineral_type_id:
        try:
            mineral_id = int(mineral_type_id)
            batches = batches.filter(items__mineral_type_id=mineral_id).distinct()
        except (ValueError, TypeError):
            pass

    # Paginate
    paginator = Paginator(batches, 10)
    page_number = request.GET.get('page')
    batches = paginator.get_page(page_number)

    # Handle POST
    if request.method == 'POST':
        try:
            supplier_name = request.POST.get('supplier_name', '').strip()
            supplier_phone = request.POST.get('supplier_phone', '').strip() or None
            transaction_date_raw = request.POST.get('transaction_date', '').strip()

            mineral_type_ids = request.POST.getlist('mineral_type[]')
            grade_ids = request.POST.getlist('grade[]')
            weights = request.POST.getlist('weight[]')
            weight_units = request.POST.getlist('weight_unit[]')
            agreed_payouts = request.POST.getlist('agreed_payout[]')

            if not supplier_name:
                return JsonResponse({'success': False, 'error': 'Supplier name is required.'})
            if not mineral_type_ids:
                return JsonResponse({'success': False, 'error': 'At least one mineral entry is required.'})

            if len(mineral_type_ids) != len(grade_ids) or len(grade_ids) != len(weights):
                return JsonResponse({'success': False, 'error': 'Incomplete mineral data.'})

            if transaction_date_raw:
                try:
                    transaction_date = datetime.fromisoformat(transaction_date_raw)
                    if timezone.is_naive(transaction_date):
                        transaction_date = timezone.make_aware(transaction_date)
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid transaction date format.'})
            else:
                transaction_date = timezone.now()

            with transaction.atomic():
                batch = MineralBatch.objects.create(
                    supplier_name=supplier_name,
                    supplier_phone=supplier_phone,
                    recorded_by=user,
                    timestamp=transaction_date,
                    status='pending'
                )

                errors = []  # ← This is where we collect user-friendly messages
                for i in range(len(mineral_type_ids)):
                    try:
                        mineral_type = MineralType.objects.get(id=mineral_type_ids[i])
                        grade = MineralGrade.objects.get(id=grade_ids[i], mineral=mineral_type)
                        weight = float(weights[i])
                        if weight <= 0:
                            errors.append(f"Row {i+1}: Weight must be greater than 0.")
                            continue

                        weight_unit = weight_units[i] if i < len(weight_units) else 'kg'
                        agreed_payout = None
                        if agreed_payouts[i]:
                            ap = float(agreed_payouts[i])
                            if ap > 0:
                                agreed_payout = ap
                            else:
                                errors.append(f"Row {i+1}: Agreed payout must be greater than 0.")
                                continue

                        if not agreed_payout:
                            if weight_unit == 'kg' and not grade.price_per_kg:
                                errors.append(f"Row {i+1}: No price per kg for {grade.grade_name}. Add negotiated price.")
                                continue
                            if weight_unit == 'lb' and not grade.price_per_pound:
                                errors.append(f"Row {i+1}: No price per lb for {grade.grade_name}. Add negotiated price.")
                                continue

                        MineralItem.objects.create(
                            batch=batch,
                            mineral_type=mineral_type,
                            grade=grade,
                            weight=weight,
                            weight_unit=weight_unit,
                            agreed_payout=agreed_payout
                        )
                    except Exception as e:
                        errors.append(f"Row {i+1}: {str(e)}")

                # If there were validation errors, raise them
                if errors:
                    # Join with <br> so frontend can render line breaks
                    error_msg = "<br>".join(errors)
                    raise Exception(error_msg)

                TransactionStatusLog.objects.create(
                    transaction=batch,
                    status="pending",
                    updated_by=user
                )

            return JsonResponse({
                'success': True,
                'batch_id': batch.batch_no,
                'receipt_url': f"/office1/receipt/{batch.items.first().id}/",
                'transaction_count': batch.items.count()
            })

        except Exception as e:
            print(f"[Batch Creation Error] {e}")

            # ✅ Return the actual error message if it's a validation error
            # If it's a system error, fallback to generic message
            error_msg = str(e)

            # Only return detailed error if it's from our validation
            if "<br>" in error_msg or error_msg.startswith("Row "):
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                })
            else:
                # For unexpected system errors, keep it safe
                return JsonResponse({
                    'success': False,
                    'error': 'An error occurred while saving. Please try again.'
                })

    return render(request, 'office1/transactions.html', {
        'mineral_types': mineral_types,
        'batches': batches,
        'date_from': date_from,
        'date_to': date_to,
        'mineral_type_id': mineral_type_id,
        'is_office2_view': user.role == user.Roles.OFFICE_2,
    })


@login_required
def receipt_view(request, transaction_id):
    item = get_object_or_404(
        MineralItem.objects.select_related('batch', 'mineral_type', 'grade'),
        id=transaction_id
    )
    html_string = render_to_string('office1/receipt.html', {'item': item})
    pdf = generate_receipt_pdf(html_string)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="receipt_{item.batch.batch_no}.pdf"'
    return response


@require_http_methods(["POST"])
@login_required
def reject_batch(request, batch_id):
    user = request.user
    batch = get_object_or_404(MineralBatch, id=batch_id, recorded_by=user)
    print(f"[Reject Batch] User: {user.username}, Batch ID: {batch_id}, Status: {batch.status}")

    if batch.status != 'pending':
        return JsonResponse({
            'success': False,
            'error': f"Cannot reject batch in '{batch.get_status_display()}' state."
        }, status=400)

    with transaction.atomic():
        batch.status = 'rejected'
        batch.save()
        TransactionStatusLog.objects.create(
            transaction=batch,
            status='rejected',
            updated_by=user
        )
    print(f"[Reject Batch] User: {user.username}, Batch ID: {batch_id}, Status: {batch.status}")
    return JsonResponse({
        'success': True,
        'message': 'Batch rejected successfully.'
    })


@require_http_methods(["POST"])
@login_required
def delete_batch(request, batch_id):
    """
    Delete a batch transaction.
    Only pending and rejected batches can be deleted.
    Paid, approved, and completed batches cannot be deleted.
    """
    user = request.user
    batch = get_object_or_404(MineralBatch, id=batch_id, recorded_by=user)
    
    print(f"[Delete Batch] User: {user.username}, Batch ID: {batch_id}, Status: {batch.status}")

    # Prevent deletion of paid/approved/completed batches
    if batch.status in ['paid', 'approved', 'completed']:
        return JsonResponse({
            'success': False,
            'error': f"Cannot delete batch in '{batch.get_status_display()}' state. Only pending or rejected batches can be deleted."
        }, status=400)

    # Store batch info before deletion
    batch_no = batch.batch_no
    
    with transaction.atomic():
        # Delete related items and logs (cascade should handle this, but being explicit)
        batch.delete()
    
    print(f"[Delete Batch] Batch {batch_no} deleted successfully by {user.username}")
    
    return JsonResponse({
        'success': True,
        'message': f'Batch {batch_no} deleted successfully.'
    })
