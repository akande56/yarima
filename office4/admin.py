from django.contrib import admin
from .models import Invoice, ExpenseItem

class ExpenseItemInline(admin.TabularInline):
    model = ExpenseItem
    extra = 1  # Number of empty rows to display for quick adding
    min_num = 1
    verbose_name = "Expense Item"
    verbose_name_plural = "Expense Items"

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("sn", "expense_type", "vendor_supplier", "payment_method", "payment_date", "total_amount")
    search_fields = ("sn", "vendor_supplier", "expense_type")
    list_filter = ("payment_method", "payment_date")
    inlines = [ExpenseItemInline]

    def total_amount(self, obj):
        total = sum(item.amount for item in obj.items.all())
        return f"₦{total:,.2f}"
    total_amount.short_description = "Total Amount"

@admin.register(ExpenseItem)
class ExpenseItemAdmin(admin.ModelAdmin):
    list_display = ("invoice", "category", "amount")
    list_filter = ("category",)
    search_fields = ("invoice__sn",)