# core/admin.py

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    MineralType,
    MineralGrade,
    MineralBatch,
    MineralItem,
    PaymentComponent,
    TransactionStatusLog,
    License,
    MineralSale
)


# --- Mineral Type Admin ---
@admin.register(MineralType)
class MineralTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


# --- Mineral Grade Admin ---
@admin.register(MineralGrade)
class MineralGradeAdmin(admin.ModelAdmin):
    list_display = ('mineral', 'grade_name', 'price_per_kg', 'price_per_pound')
    search_fields = ('mineral__name', 'grade_name')
    list_filter = ('mineral',)
    ordering = ('mineral', 'grade_name')

    def save_model(self, request, obj, form, change):
        # Optional: Prevent both prices from being set
        if obj.price_per_kg and obj.price_per_pound:
            from django.core.exceptions import ValidationError
            raise ValidationError("Cannot set both price_per_kg and price_per_pound.")
        super().save_model(request, obj, form, change)


# --- Mineral Batch Admin ---
@admin.register(MineralBatch)
class MineralBatchAdmin(admin.ModelAdmin):
    list_display = (
        'batch_no',
        'supplier_name',
        'supplier_phone',
        'total_items',
        'total_value_display',
        'status',
        'recorded_by',
        'timestamp'
    )
    list_filter = ('status', 'timestamp', 'recorded_by')
    search_fields = ('batch_no', 'supplier_name', 'supplier_phone')
    readonly_fields = ('batch_no', 'timestamp', 'total_items', 'total_value')
    ordering = ('-timestamp',)

    def total_items(self, obj):
        return obj.items.count()
    total_items.short_description = "Items"

    def total_value_display(self, obj):
        return f"₦{obj.total_value():,.2f}"
    total_value_display.short_description = "Total Value"

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of non-pending batches
        if obj and obj.status != 'pending':
            return False
        return super().has_delete_permission(request, obj)


# --- Mineral Item Admin ---
@admin.register(MineralItem)
class MineralItemAdmin(admin.ModelAdmin):
    list_display = (
        'mineral_type',
        'grade',
        'weight',
        'weight_unit',
        'agreed_payout',
        'total_value',
        'batch_link'
    )
    list_filter = ('mineral_type', 'grade', 'weight_unit', 'batch__status')
    search_fields = ('mineral_type__name', 'grade__grade_name', 'batch__batch_no')
    raw_id_fields = ('batch',)

    def batch_link(self, obj):
        url = f"/admin/core/mineralbatch/{obj.batch.id}/change/"
        return format_html('<a href="{}">Batch {}</a>', url, obj.batch.batch_no)
    batch_link.short_description = "Batch"


# --- Payment Component Admin ---
@admin.register(PaymentComponent)
class PaymentComponentAdmin(admin.ModelAdmin):
    list_display = ('batch', 'method', 'amount', 'recorded_at')
    list_filter = ('method', 'recorded_at')
    search_fields = ('batch__batch_no', 'reference')
    raw_id_fields = ('batch',)


# --- Transaction Status Log Admin ---
@admin.register(TransactionStatusLog)
class TransactionStatusLogAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'status', 'updated_by', 'updated_at')
    search_fields = ('transaction__batch_no', 'transaction__supplier_name', 'status')
    list_filter = ('status', 'updated_at')
    ordering = ('-updated_at',)
    readonly_fields = ('transaction', 'status', 'updated_by', 'updated_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# --- License Admin ---
@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ('key', 'expiry_date', 'active', 'is_valid_display')
    list_filter = ('active', 'expiry_date')
    search_fields = ('key',)
    readonly_fields = ('is_valid_display',)

    def is_valid_display(self, obj):
        return obj.is_valid
    is_valid_display.short_description = 'Valid'
    is_valid_display.boolean = True


# --- Mineral Sale Admin ---
@admin.register(MineralSale)
class MineralSaleAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number', 'mineral_type', 'grade', 'quantity', 'total_price',
        'buyer_name', 'sale_date', 'status', 'processed_by'
    ]
    list_filter = ['status', 'mineral_type', 'grade', 'sale_date', 'processed_by']
    search_fields = ['reference_number', 'buyer_name', 'mineral_type__name']
    readonly_fields = ['reference_number', 'total_price', 'sale_date', 'processed_by']
    fieldsets = (
        ('Transaction', {
            'fields': ('mineral_type', 'grade', 'status', 'reference_number')
        }),
        ('Details', {
            'fields': ('quantity', 'quantity_unit', 'price_per_unit', 'total_price')
        }),
        ('Buyer', {
            'fields': ('buyer_name', 'buyer_contact')
        }),
        ('Meta', {
            'fields': ('sale_date', 'processed_by', 'notes')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'mineral_type', 'grade', 'processed_by'
        )