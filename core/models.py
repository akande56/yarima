# core/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

class MineralType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# --- Supplier ---
# class Supplier(models.Model):
#     name = models.CharField(max_length=150)
#     date_created = models.DateTimeField(auto_now_add=True)
#     last_day_received = models.DateField(_("Last Delivery Date"), null=True, blank=True)
#     recorded_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True
#     )

#     class Meta:
#         ordering = ['-last_day_received', '-date_created']

#     def __str__(self):
#         return self.name


class MineralGrade(models.Model):
    mineral = models.ForeignKey(MineralType, on_delete=models.CASCADE, related_name='grades')
    grade_name = models.CharField(max_length=100)
    price_per_pound = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        unique_together = ('mineral', 'grade_name')
        verbose_name = _("Mineral Grade")
        verbose_name_plural = _("Mineral Grades")

    def __str__(self):
        return f"{self.mineral.name} - {self.grade_name}"
    


# --- Mineral Transaction ---
# class MineralTransaction(models.Model):
#     WEIGHT_UNIT_CHOICES = [
#         ('kg', _('Kilograms')),
#         ('lb', _('Pounds')),
#     ]

#     PAYMENT_METHOD_CHOICES = [
#         # Fintech / Digital Payments
#         ('opay', 'OPay'),
#         ('moniepoint', 'Moniepoint'),
#         ('palmpay', 'PalmPay'),
#         ('kuda', 'Kuda'),
#         ('flutterwave', 'Flutterwave'),
#         ('paystack', 'Paystack'),
#         ('cash', 'Cash'),
#         ('other_fintech', 'Other Fintech'),

#         # Bank Transfer Options (Popular Nigerian Banks)
#         ('access_bank', 'Access Bank'),
#         ('gtbank', 'GTBank'),
#         ('zenith_bank', 'Zenith Bank'),
#         ('first_bank', 'First Bank'),
#         ('uba', 'UBA'),
#         ('fcmb', 'FCMB'),
#         ('fidelity_bank', 'Fidelity Bank'),
#         ('union_bank', 'Union Bank'),
#         ('sterling_bank', 'Sterling Bank'),
#         ('wema_bank', 'Wema Bank'),
#         ('keystone_bank', 'Keystone Bank'),
#         ('polaris_bank', 'Polaris Bank'),
#         #  Generic Options
#         ('other_bank', 'Other Bank'),
#     ]

#     STATUS_CHOICES = [
#         ('pending', _("Pending Approval")),
#         ('approved', _("Approved")),
#         ('paid', _("Paid")),
#         ('completed', _("Completed")),
#         ('rejected', _("Rejected")),
#     ]

#     # Core fields
#     mineral_type = models.ForeignKey(MineralType, on_delete=models.CASCADE, related_name='mineral')
#     grade = models.ForeignKey(MineralGrade, on_delete=models.CASCADE, related_name='grade')
#     supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='supplier')
#     supplier_phone = models.CharField(
#         _("Supplier Phone"), max_length=20, blank=True, null=True,
#         help_text=_("Optional: Phone number of the supplier for contact purposes.")
#     )
#     weight = models.DecimalField(
#         _("Weight"), max_digits=10, decimal_places=2,
#         help_text=_("Enter the weight of the mineral received.")
#     )
#     weight_unit = models.CharField(
#         _("Weight Unit"), max_length=2, choices=WEIGHT_UNIT_CHOICES, default='kg',
#         help_text=_("Select the unit in which weight was measured.")
#     )
#     # New: Allow manual override of payout amount
#     agreed_payout = models.DecimalField(
#     _("Negotiated Price Per Unit"), max_digits=12, decimal_places=2, null=True, blank=True,
#     help_text=_("If set, this price per unit will be used instead of standard pricing (will be multiplied by weight).")
#     )

#     date_received = models.DateTimeField(_("Date Received"), auto_now_add=True)
#     recorded_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         verbose_name=_("Recorded By")
#     )

#     status = models.CharField(
#         _("Transaction Status"), max_length=20, choices=STATUS_CHOICES, default='pending'
#     )

#     # Payout details (all optional)
#     payment_method = models.CharField(
#         _("Payment Method"), max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True
#     )
#     payout_account_number = models.CharField(
#         _("Payout Account/Wallet Number"), max_length=50, blank=True, null=True
#     )
#     payout_account_name = models.CharField(
#         _("Payout Account Name"), max_length=150, blank=True, null=True
#     )
#     payout_reference = models.TextField(
#         _("Payout Reference"), blank=True, null=True)
#     paid_at = models.DateTimeField(_("Paid At"), null=True, blank=True)
#     paid_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         related_name='paid_transactions',
#         verbose_name=_("Paid By")
#     )
#     approved_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         related_name='approved_transactions',
#         verbose_name=_("Approved By")
#     )

#     class Meta:
#         ordering = ['-date_received']
#         verbose_name = _("Mineral Transaction")
#         verbose_name_plural = _("Mineral Transactions")

#     def __str__(self):
#         unit_display = dict(self.WEIGHT_UNIT_CHOICES).get(self.weight_unit, self.weight_unit)
#         return f"{self.mineral_type.name} ({self.grade.grade_name}) - {self.weight} {unit_display}"

#     @property
#     def total_value(self):
#         """
#         Return agreed_payout if set; otherwise calculate from weight and price.
#         """
#         if self.agreed_payout is not None:
#             return round(float(self.weight) * float(self.agreed_payout), 2)

#         if self.weight_unit == 'kg' and self.grade.price_per_kg is not None:
#             return round(float(self.weight) * float(self.grade.price_per_kg), 2)
#         elif self.weight_unit == 'lb' and self.grade.price_per_pound is not None:
#             return round(float(self.weight) * float(self.grade.price_per_pound), 2)
#         return 0.0

#     def clean(self):
#         if self.weight <= 0:
#             raise ValidationError(_("Weight must be greater than zero."))


class MineralBatch(models.Model):
    batch_no = models.CharField(max_length=20, unique=True, editable=False)
    supplier_name = models.CharField(
        _("Supplier Name"), max_length=150,
        help_text=_("Name as provided at intake.")
    )
    supplier_phone = models.CharField(
        _("Supplier Phone"), max_length=20, blank=True, null=True
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='mineral_batches'
    )
    timestamp = models.DateTimeField(_("Date Received"), default=timezone.now)

    STATUS_CHOICES = [
        ('pending', _("Pending Approval")),
        ('approved', _("Approved")),
        ('paid', _("Paid")),
        ('completed', _("Completed")),
        ('rejected', _("Rejected")),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_batches'
    )
    paid_at = models.DateTimeField(_("Paid At"), null=True, blank=True)
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='paid_batches'
    )
    notes = models.TextField(_("Internal Notes"), blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Mineral Batch"
        verbose_name_plural = "Mineral Batches"

    def __str__(self):
        return f"Batch {self.batch_no} - {self.supplier_name}"

    def save(self, *args, **kwargs):
        if not self.batch_no:
            year = self.timestamp.year % 100
            prefix = f"MB{year}-"

            # Get the highest batch_no with this prefix
            last_batch = MineralBatch.objects.filter(
                batch_no__startswith=prefix
            ).order_by('-batch_no').first()

            if last_batch:
                try:
                    # Extract number from batch_no: MB24-00151 → 151
                    last_num = int(last_batch.batch_no.split('-')[-1])
                    num = last_num + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1

            self.batch_no = f"{prefix}{num:05d}"

        super().save(*args, **kwargs)

    def has_negotiated_items(self):
        return self.items.filter(agreed_payout__isnull=False).exists()

    def total_value(self):
        return sum(item.total_value for item in self.items.all())

    def total_converted_kg(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.converted_weight_kg
        return total.quantize(Decimal('0.00'))

    def total_converted_lb(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.converted_weight_lb
        return total.quantize(Decimal('0.00'))
    
    def total_original_kg(self):
        """Sum of weights entered as kg — returns Decimal."""
        total = Decimal('0.00')
        for item in self.items.all():
            if item.weight_unit == 'kg':
                total += item.weight
        return total.quantize(Decimal('0.00'))

    def total_original_lb(self):
        """Sum of weights entered as lb — returns Decimal."""
        total = Decimal('0.00')
        for item in self.items.all():
            if item.weight_unit == 'lb':
                total += item.weight
        return total.quantize(Decimal('0.00'))

    def total_items(self):
        return self.items.count()

    def is_paid(self):
        return self.status in ['paid', 'completed']


class MineralItem(models.Model):
    batch = models.ForeignKey(
        MineralBatch,
        on_delete=models.CASCADE,
        related_name='items'
    )
    mineral_type = models.ForeignKey(MineralType, on_delete=models.CASCADE)
    grade = models.ForeignKey(MineralGrade, on_delete=models.CASCADE)
    weight = models.DecimalField(_("Weight"), max_digits=10, decimal_places=2)
    weight_unit = models.CharField(
        _("Weight Unit"), max_length=2,
        choices=[
            ('kg', _('Kilograms')),
            ('lb', _('Pounds')),
        ],
        default='kg'
    )
    agreed_payout = models.DecimalField(
        _("Negotiated Price Per Unit"), max_digits=12, decimal_places=2, null=True, blank=True,
        help_text=_("Overrides standard pricing if set.")
    )

    class Meta:
        verbose_name = "Mineral Item"
        verbose_name_plural = "Mineral Items"

    def __str__(self):
        unit = dict(MineralItem.weight_unit.field.choices).get(self.weight_unit)
        return f"{self.mineral_type.name} - {self.weight} {unit}"

    @property
    def total_value(self):
        """
            Calculate total value using Decimal for precision.
            Uses agreed_payout if set, otherwise standard price.
        """
        if self.agreed_payout is not None:
            return (self.weight * self.agreed_payout).quantize(Decimal('0.00'))

        if self.weight_unit == 'kg' and self.grade.price_per_kg is not None:
            return (self.weight * self.grade.price_per_kg).quantize(Decimal('0.00'))
        elif self.weight_unit == 'lb' and self.grade.price_per_pound is not None:
            return (self.weight * self.grade.price_per_pound).quantize(Decimal('0.00'))

    @property
    def converted_weight_kg(self):
        if self.weight_unit == 'kg':
            return self.weight
        return self.weight * Decimal('0.453592')

    @property
    def converted_weight_lb(self):
        if self.weight_unit == 'lb':
            return self.weight
        return self.weight * Decimal('2.20462')


PAYMENT_METHOD_CHOICES = [
    ('opay', 'OPay'),
    ('moniepoint', 'Moniepoint'),
    ('palmpay', 'PalmPay'),
    ('kuda', 'Kuda'),
    ('flutterwave', 'Flutterwave'),
    ('paystack', 'Paystack'),
    ('cash', 'Cash'),
    ('other_fintech', 'Other Fintech'),
    ('access_bank', 'Access Bank'),
    ('gtbank', 'GTBank'),
    ('zenith_bank', 'Zenith Bank'),
    ('first_bank', 'First Bank'),
    ('uba', 'UBA'),
    ('fcmb', 'FCMB'),
    ('fidelity_bank', 'Fidelity Bank'),
    ('union_bank', 'Union Bank'),
    ('sterling_bank', 'Sterling Bank'),
    ('wema_bank', 'Wema Bank'),
    ('keystone_bank', 'Keystone Bank'),
    ('polaris_bank', 'Polaris Bank'),
    ('other_bank', 'Other Bank'),
]


class PaymentComponent(models.Model):
    batch = models.ForeignKey(
        MineralBatch,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    method = models.CharField(_("Payment Method"), max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(_("Amount"), max_digits=12, decimal_places=2)
    payout_account_number = models.CharField(
        _("Payout Account/Wallet Number"), max_length=50, blank=True, null=True
    )
    payout_account_name = models.CharField(
        _("Payout Account Name"), max_length=150, blank=True, null=True
    )
    reference = models.TextField(_("Reference"), blank=True, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment Component"
        verbose_name_plural = "Payment Components"
        ordering = ['recorded_at']

    def __str__(self):
        return f"{self.method}: ₦{self.amount:,.2f} → {self.batch.batch_no}"


class TransactionStatusLog(models.Model):
    transaction = models.ForeignKey(
        MineralBatch, on_delete=models.CASCADE, related_name='status_logs'
    )
    # transaction = models.ForeignKey(
    #     'MineralTransaction',  
    #     on_delete=models.CASCADE,
    #     related_name='status_logs'
    # )
    status = models.CharField(max_length=20, choices=MineralBatch.STATUS_CHOICES)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.transaction} → {self.status} at {self.updated_at.strftime('%Y-%m-%d')}"


class MineralSale(models.Model):
    STATUS_CHOICES = [
        ('pending', _("Pending Payment")),
        ('paid', _("Paid")),
        ('shipped', _("Shipped")),
        ('completed', _("Completed")),
        ('cancelled', _("Cancelled")),
    ]

    mineral_type = models.ForeignKey('core.MineralType', on_delete=models.CASCADE, related_name='sales')
    grade = models.ForeignKey('core.MineralGrade', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2)
    quantity_unit = models.CharField(_("Quantity Unit"), max_length=10, default="kg")
    price_per_unit = models.DecimalField(_("Price per Unit"), max_digits=12, decimal_places=2)
    total_price = models.DecimalField(_("Total Price"), max_digits=15, decimal_places=2, editable=False)
    buyer_name = models.CharField(_("Buyer Name"), max_length=150)
    buyer_contact = models.CharField(_("Buyer Contact"), max_length=100, blank=True, null=True)
    sale_date = models.DateTimeField(_("Sale Date"), default=timezone.now)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sales_processed'
    )
    status = models.CharField(_("Sale Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    reference_number = models.CharField(_("Reference Number"), max_length=50, unique=True, editable=False)
    notes = models.TextField(_("Notes"), blank=True, null=True)

    # === Optional Identification Fields ===
    bvn = models.CharField(_("BVN"), max_length=11, blank=True, null=True, help_text=_("Bank Verification Number"))
    nin = models.CharField(_("NIN"), max_length=20, blank=True, null=True, help_text=_("National Identification Number"))
    international_id = models.CharField(
        _("International ID"), max_length=50, blank=True, null=True, help_text=_("Passport or other international ID number")
    )
    driver_license = models.CharField(
        _("Driver's License"), max_length=50, blank=True, null=True, help_text=_("Driver's license number")
    )

    class Meta:
        ordering = ['-sale_date']
        verbose_name = _("Mineral Sale")
        verbose_name_plural = _("Mineral Sales")

    # def save(self, *args, **kwargs):
    #     if not self.reference_number:
    #         year = timezone.now().year
    #         last_sale = MineralSale.objects.filter(reference_number__startswith=f"SALE-{year}") \
    #                                        .order_by('-id').first()
    #         last_number = int(last_sale.reference_number.split('-')[-1]) + 1 if last_sale else 1
    #         self.reference_number = f"SALE-{year}-{last_number:04d}"
    #     self.total_price = self.quantity * self.price_per_unit
    #     super().save(*args, **kwargs)
    def save(self, *args, **kwargs):
        if not self.reference_number:
            year = timezone.now().year
            with transaction.atomic():
                last_sale = MineralSale.objects.select_for_update().filter(
                    reference_number__startswith=f"SALE-{year}"
                ).order_by('id').last()  # last = highest ID
                if last_sale:
                    try:
                        last_num = int(last_sale.reference_number.split('-')[-1])
                        next_num = last_num + 1
                    except (ValueError, IndexError):
                        next_num = 1
                else:
                    next_num = 1
                self.reference_number = f"SALE-{year}-{next_num:04d}"
        self.total_price = self.quantity * self.price_per_unit
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Sale {self.reference_number} - {self.mineral_type.name} to {self.buyer_name}"


class License(models.Model):
    key = models.CharField(max_length=255, unique=True)
    expiry_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    @property
    def is_valid(self):
        if not self.expiry_date:
            return False
        return self.active and self.expiry_date >= timezone.now().date()

    def __str__(self):
        if not self.expiry_date:
            return f"License {self.key} (no expiry set)"
        status = "✅ Valid" if self.is_valid else "❌ Expired"
        return f"License {self.key} ({status}, expires {self.expiry_date})"

    class Meta:
        verbose_name = "License"
        verbose_name_plural = "Licenses"
