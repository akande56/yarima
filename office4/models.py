from django.db import models

class Invoice(models.Model):
    sn = models.PositiveIntegerField("Serial Number", unique=True, editable=False)
    expense_type = models.CharField(max_length=100)  # e.g., "Maintenance", "Purchase"
    description = models.TextField(blank=True, null=True)
    vendor_supplier = models.CharField(max_length=255, blank=True, null=True)
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ("cash", "Cash"),
            ("bank_transfer", "Bank Transfer"),
            ("cheque", "Cheque"),
            ("pos", "POS"),
        ],
        blank=True,
        null=True
    )
    payment_date = models.DateField(blank=True, null=True)
    remark = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date']

    def save(self, *args, **kwargs):
        if not self.sn:  # Only set on creation
            last_invoice = Invoice.objects.order_by('-sn').first()
            if last_invoice:
                self.sn = last_invoice.sn + 1
            else:
                self.sn = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice #{self.sn} - {self.expense_type}"


class ExpenseItem(models.Model):
    CATEGORY_CHOICES = [
        ("diesel_petrol", "Diesel/Petrol"),
        ("generator", "Generator"),
        ("truck", "Truck"),
        ("cctv", "CCTV"),
        ("air_condition", "Air Condition"),
        ("electricity_spare_parts", "Electricity Spare Parts"),
        ("company_machines", "Company Machines"),
        ("commission", "Commission"),
        ("laborers_workers", "Laborer/Workers"),
        ("furniture", "Furniture"),
        ("bore_hole", "Bore Hole"),
        ("utility", "Utility"),
        ("taxes_paid", "Taxes Paid"),
        ("mosque", "Mosque"),
        ("sadaq_donation", "Sadaq/Donation"),
        ("medical_expenses", "Medical Expenses"),
        ("miscellaneous", "Miscellaneous"),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.get_category_display()} - {self.amount}"