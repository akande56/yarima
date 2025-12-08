# office2/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from django.db.models import Q
from core.models import (
    MineralBatch,
    TransactionStatusLog,
    PaymentComponent,
    PAYMENT_METHOD_CHOICES,
)
from yarima_mining.users.models import User

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator
import json
from datetime import datetime
from decimal import Decimal


@login_required
def dashboard_view(request):
    user = request.user
    if user.role != User.Roles.OFFICE_2:
        return redirect('dashboard_router')

    today = now().date()
    batches = MineralBatch.objects.filter(timestamp__date=today).exclude(status='rejected')

    pending_count = batches.filter(status='pending').count()
    approved_count = batches.filter(status='approved').count()
    paid_count = batches.filter(status='paid').count()
    total_today = batches.count()

    paid_batches = batches.filter(status='paid')
    paid_weight_kg = 0
    paid_weight_lb = 0
    paid_total_value = 0

    for batch in paid_batches:
        paid_weight_kg += batch.total_original_kg()
        paid_weight_lb += batch.total_original_lb()
        paid_total_value += batch.total_value()

    recent_batches = batches.order_by('-timestamp')[:10]

    return render(request, 'office2/dashboard.html', {
        'pending_count': pending_count,
        'approved_count': approved_count,
        'paid_count': paid_count,
        'total_transactions': total_today,
        'recent_batches': recent_batches,
        'paid_weight_kg': round(paid_weight_kg, 2),
        'paid_weight_lb': round(paid_weight_lb, 2),
        'paid_total_value': round(paid_total_value, 2),
    })


def serialize_batch(batch):
    latest_log = batch.status_logs.order_by('-updated_at').first()

    return {
        "id": batch.id,
        "batch_no": batch.batch_no,
        "supplier_name": batch.supplier_name,
        "supplier_phone": batch.supplier_phone or "Not Provided",
        "date_received": batch.timestamp.isoformat(),
        "updated_at": latest_log.updated_at.isoformat() if latest_log else batch.timestamp.isoformat(),
        "status": batch.status,
        "status_display": batch.get_status_display(),
        "total_value": float(batch.total_value()),
        "items_count": batch.total_items(),
        "total_weight_kg": float(batch.total_original_kg()),
        "total_weight_lb": float(batch.total_original_lb()),
        "recorded_by": f"{batch.recorded_by.name or batch.recorded_by.username}",
        "approved_by": f"{batch.approved_by.name or batch.approved_by.username}" if batch.approved_by else None,
        "paid_at": batch.paid_at.isoformat() if batch.paid_at else None,
        "paid_by": f"{batch.paid_by.name or batch.paid_by.username}" if batch.paid_by else None,
        "payment_components": [
            {
                "method": comp.method,
                "method_display": dict(PAYMENT_METHOD_CHOICES).get(comp.method, comp.method.title()),
                "amount": float(comp.amount),
                "payout_account_number": comp.payout_account_number,
                "payout_account_name": comp.payout_account_name,
                "reference": comp.reference,
                "recorded_at": comp.recorded_at.isoformat(),
            }
            for comp in batch.payments.all()
        ],
        "status_history": [
            {
                "status": log.status,
                "status_display": log.get_status_display(),
                "updated_by": f"{log.updated_by.get_full_name() or log.updated_by.username}",
                "updated_at": log.updated_at.isoformat(),
            }
            for log in batch.status_logs.all().order_by("-updated_at")
        ],
        "items": [
            {
                "mineral_type": item.mineral_type.name,
                "grade": item.grade.grade_name,
                "weight": float(item.weight),
                "weight_unit": item.get_weight_unit_display(),
                "total_value": float(item.total_value)
            }
            for item in batch.items.all()
        ]
    }


@require_http_methods(["GET"])
@login_required
def transaction_list(request):
    user = request.user
    if user.role != User.Roles.OFFICE_2:
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    batches = MineralBatch.objects.select_related(
        "recorded_by"
    ).prefetch_related("items", "payments", "status_logs").order_by("-timestamp")

    search_id = request.GET.get("search_id", "")
    status = request.GET.get("status", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")

    # if search_id.isdigit():
    #     batches = batches.filter(id=int(search_id))
     
    batches = batches.filter(batch_no__icontains=search_id)

    if status:
        batches = batches.filter(status=status)
    if date_from:
        try:
            dt = datetime.fromisoformat(date_from)
            batches = batches.filter(timestamp__date__gte=dt.date())
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            batches = batches.filter(timestamp__date__lte=dt.date())
        except ValueError:
            pass

    page_size = min(int(request.GET.get("page_size", 10)), 100)
    paginator = Paginator(batches, page_size)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "data": [serialize_batch(batch) for batch in page_obj],
            "pagination": {
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
                "total": paginator.count,
                "has_previous": page_obj.has_previous(),
                "has_next": page_obj.has_next(),
            }
        })

    return render(request, "office2/transaction_list.html", {
        "batches": page_obj,
    })


@require_http_methods(["GET"])
@login_required
def transaction_detail_api(request, pk):
    user = request.user
    if user.role != User.Roles.OFFICE_2:
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    batch = get_object_or_404(
        MineralBatch.objects.select_related(
            "recorded_by", "approved_by", "paid_by",
        ).prefetch_related("items__mineral_type", "items__grade", "payments", "status_logs"),
        id=pk
    )
    return JsonResponse({
        "success": True,
        "data": serialize_batch(batch),
    })


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def approve_batch(request, pk):
    user = request.user
    if user.role != User.Roles.OFFICE_2:
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    batch = get_object_or_404(MineralBatch, id=pk)
    if batch.status != "pending":
        return JsonResponse({
            "success": False,
            "error": f"Cannot approve batch in '{batch.get_status_display()}' state."
        }, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}

    payments = data.get("payments", [])
    reference = data.get("reference", f"Approved via Office 2 - {batch.batch_no}")

    expected_total = round(batch.total_value(), 2)
    total_paid = Decimal('0.00')
    valid_methods = dict(PAYMENT_METHOD_CHOICES)

    # ✅ Only validate and create payments if any were provided
    if payments:
        with transaction.atomic():
            for item in payments:
                method = item.get("method")
                amount = item.get("amount")
                account_number = item.get("payout_account_number")
                account_name = item.get("payout_account_name")

                if not method or method not in valid_methods:
                    transaction.set_rollback(True)
                    return JsonResponse({"success": False, "error": f"Invalid payment method: {method}"}, status=400)

                try:
                    amount = Decimal(str(amount))
                    if amount <= 0:
                        raise ValueError
                except (ValueError, Exception):
                    transaction.set_rollback(True)
                    return JsonResponse({"success": False, "error": f"Invalid amount: {amount}"}, status=400)

                total_paid += amount

            # ✅ Only validate total if payments exist
            if abs(total_paid - Decimal(str(expected_total))) > Decimal('0.01'):
                transaction.set_rollback(True)
                return JsonResponse({
                    "success": False,
                    "error": f"Total payment (₦{total_paid:,.2f}) must equal batch value (₦{expected_total:,.2f})."
                }, status=400)

            # ✅ All valid — create payment components
            for item in payments:
                PaymentComponent.objects.create(
                    batch=batch,
                    method=item["method"],
                    amount=Decimal(str(item["amount"])),
                    payout_account_number=item.get("payout_account_number"),
                    payout_account_name=item.get("payout_account_name"),
                    reference=reference
                )

    # ✅ Approve batch (even if no payments)
    batch.status = "approved"
    batch.approved_by = user
    batch.save()

    TransactionStatusLog.objects.create(
        transaction=batch,
        status="approved",
        updated_by=user,
    )

    message = "Batch approved successfully."
    if payments:
        message += f" Total: ₦{total_paid:,.2f}"

    return JsonResponse({
        "success": True,
        "message": message,
        "status": "approved"
    })


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def pay_batch(request, pk):
    user = request.user
    if user.role != User.Roles.OFFICE_2:
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    batch = get_object_or_404(MineralBatch, id=pk)
    if batch.status != "approved":
        return JsonResponse({
            "success": False,
            "error": f"Cannot mark as paid when status is '{batch.get_status_display()}'."
        }, status=400)

    # if not batch.payments.exists():
    #     return JsonResponse({
    #         "success": False,
    #         "error": "No payment method set. Please approve first."
    #     }, status=400)

    with transaction.atomic():
        batch.status = "paid"
        batch.paid_at = timezone.now()
        batch.paid_by = user
        batch.save()

        TransactionStatusLog.objects.create(
            transaction=batch,
            status="paid",
            updated_by=user,
        )

    return JsonResponse({
        "success": True,
        "message": "Batch marked as paid successfully.",
        "status": "paid"
    })