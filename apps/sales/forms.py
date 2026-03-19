from django import forms
from django.forms import inlineformset_factory
from .models import Proposal, Product, Estimate, StaffMonthlyTarget
from django.contrib.auth import get_user_model

User = get_user_model()

class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = [
            'document_number', 'customer', 'price_level', 'issue_date', 'expiry_date',
            'subtotal', 'tax_amount', 'discount_amount', 'total_amount',
            'status', 'notes'
        ]
        widgets = {
            'document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PROP-XXXX'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'price_level': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'subtotal': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Internal notes or terms...'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'unit_price', 'quantity', 'tax_percent', 'total']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control product-select', 'placeholder': 'Product Name'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control price-input', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control qty-input', 'step': '0.01'}),
            'tax_percent': forms.NumberInput(attrs={'class': 'form-control tax-input', 'step': '0.01'}),
            'total': forms.NumberInput(attrs={'class': 'form-control total-input', 'readonly': 'readonly'}),
        }


ProposalItemFormSet = inlineformset_factory(
    Proposal, Product,
    form=ProductForm,
    extra=1,
    can_delete=True
)


class EstimateForm(forms.ModelForm):
    class Meta:
        model = Estimate
        fields = [
            'document_number', 'customer', 'price_level', 'issue_date', 'expiry_date',
            'subtotal', 'tax_amount', 'discount_amount', 'total_amount',
            'status', 'notes'
        ]
        widgets = {
            'document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'EST-XXXX'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'price_level': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'subtotal': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Internal notes or terms...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        issue_date = cleaned_data.get('issue_date')
        expiry_date = cleaned_data.get('expiry_date')

        if issue_date and expiry_date and expiry_date < issue_date:
            self.add_error('expiry_date', "Expiry date cannot be before the issue date.")

        return cleaned_data

EstimateItemFormSet = inlineformset_factory(
    Estimate, Product,
    form=ProductForm,
    extra=1,
    can_delete=True
)

class StaffMonthlyTargetForm(forms.ModelForm):
    class Meta:
        model = StaffMonthlyTarget
        fields = [
            'staff', 'month', 'year', 'leads_target', 'calls_target',
            'meetings_target', 'proposals_target', 'deals_target', 'revenue_target'
        ]
        widgets = {
            'staff': forms.Select(attrs={'class': 'form-select'}),
            'month': forms.Select(choices=[(i, i) for i in range(1, 13)], attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2024, 'max': 2100}),
            'leads_target': forms.NumberInput(attrs={'class': 'form-control'}),
            'calls_target': forms.NumberInput(attrs={'class': 'form-control'}),
            'meetings_target': forms.NumberInput(attrs={'class': 'form-control'}),
            'proposals_target': forms.NumberInput(attrs={'class': 'form-control'}),
            'deals_target': forms.NumberInput(attrs={'class': 'form-control'}),
            'revenue_target': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.staff.models import Staff
        staff_qs = Staff.objects.filter(is_active=True).select_related('user')
        self.fields['staff'].queryset = staff_qs
        self.fields['staff'].label_from_instance = lambda obj: obj.user.get_full_name() or obj.user.username
        # Month choices with names
        self.fields['month'].widget = forms.Select(
            choices=[
                (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
                (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
                (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'),
            ],
            attrs={'class': 'form-select'}
        )
