# core/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import MineralType, MineralGrade

# Optional: Only include if Supplier model is active
# from .models import Supplier


class MineralTypeForm(forms.ModelForm):
    """
    Form for creating/editing mineral types.
    """
    class Meta:
        model = MineralType
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter mineral name'),
                'autocomplete': 'off',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('Optional description of the mineral type'),
                'rows': 3,
                'maxlength': 500,
            }),
        }
        help_texts = {
            'name': _('A unique name for the mineral (e.g., Cassiterite, Coltan).'),
            'description': _('Provide additional details like origin, appearance, or usage.'),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            return name.strip().title()  # Normalize formatting
        return name


class MineralGradeForm(forms.ModelForm):
    """
    Form for creating/editing mineral grades.
    Ensures only one price field is set: per kg OR per pound.
    """
    class Meta:
        model = MineralGrade
        fields = ['mineral', 'grade_name', 'price_per_pound', 'price_per_kg']
        widgets = {
            'mineral': forms.Select(attrs={
                'class': 'form-select',
            }),
            'grade_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., High Grade, Medium, Low'),
                'autocomplete': 'off',
            }),
            'price_per_pound': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Price per pound (optional)'),
                'step': '0.01',
                'min': '0',
            }),
            'price_per_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Price per kg (optional)'),
                'step': '0.01',
                'min': '0',
            }),
        }
        help_texts = {
            'mineral': _('The base mineral this grade belongs to.'),
            'grade_name': _('Name of the quality tier (e.g., Premium, Standard).'),
            'price_per_pound': _('Set only if transactions are typically in pounds.'),
            'price_per_kg': _('Set only if transactions are typically in kilograms.'),
        }

    def clean(self):
        cleaned_data = super().clean()
        price_per_kg = cleaned_data.get('price_per_kg')
        price_per_pound = cleaned_data.get('price_per_pound')

        # Convert Decimal('0.00') to None for validation
        kg_is_set = price_per_kg is not None and price_per_kg != 0
        lb_is_set = price_per_pound is not None and price_per_pound != 0

        if kg_is_set and lb_is_set:
            raise forms.ValidationError(
                _("You cannot set both 'Price per kg' and 'Price per pound'. Please choose one unit.")
            )

        if not kg_is_set and not lb_is_set:
            raise forms.ValidationError(
                _("You must set either 'Price per kg' or 'Price per pound' to a value greater than zero.")
            )

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Improve UX: show placeholder when no mineral types exist
        if not MineralType.objects.exists():
            self.fields['mineral'].disabled = True
            self.fields['mineral'].help_text = _(
                "No mineral types available. Please create one first."
            )
        else:
            self.fields['mineral'].queryset = MineralType.objects.all().order_by('name')


# ==============================
#  OPTIONAL: SupplierForm
# ==============================
# Only uncomment and use if you've re-enabled the Supplier model
#
# class SupplierForm(forms.ModelForm):
#     """
#     Form for managing suppliers.
#     To be used when Supplier model is active.
#     """
#     class Meta:
#         model = Supplier
#         fields = [
#             'name',
#             'contact_phone',
#             'contact_email',
#             'address',
#         ]
#         widgets = {
#             'name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': _('Full supplier name'),
#                 'autocomplete': 'off',
#             }),
#             'contact_phone': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': _('Phone number, e.g., +234 803 123 4567'),
#                 'type': 'tel',
#             }),
#             'contact_email': forms.EmailInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': _('Email address (optional)'),
#                 'autocomplete': 'email',
#             }),
#             'address': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'placeholder': _('Full address (optional)'),
#                 'rows': 3,
#             }),
#         }
#         help_texts = {
#             'name': _('The legal or commonly known name of the supplier.'),
#             'contact_phone': _('Used for communication during intake.'),
#             'contact_email': _('Optional. Used for digital correspondence.'),
#             'address': _('Physical location or region of operation.'),
#         }
#
#     def clean_name(self):
#         name = self.cleaned_data.get('name')
#         if name:
#             return name.strip().title()
#         return name
#
#     def clean_contact_phone(self):
#         phone = self.cleaned_data.get('contact_phone')
#         if phone:
#             return phone.strip()
#         return phone