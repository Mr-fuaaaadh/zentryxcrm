from django import forms
from .models import (
    Asset, Supplier, Purchase, PurchaseItem,
    StockOut, SerialNumber, InventoryBalance, AssetAssignment
)

# Common styling for enterprise-ready forms
FORM_WIDGET_CLASS = 'form-control shadow-sm focus:ring-primary'

class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                field.widget.attrs.update({'class': FORM_WIDGET_CLASS})


class AssetForm(StyledModelForm):
    class Meta:
        model = Asset
        fields = [
            'name', 'asset_code', 'description', 'asset_type', 
            'is_serialized', 'unit', 'min_stock_level',
            'default_purchase_price', 'default_selling_price'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'is_serialized': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def clean_asset_code(self):
        code = self.cleaned_data.get('asset_code').upper()
        if Asset.objects.filter(asset_code=code).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("An asset with this code already exists.")
        return code


class AssetAssignmentForm(StyledModelForm):
    class Meta:
        model = AssetAssignment
        fields = ['staff_name', 'quantity', 'serial_number', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.asset = kwargs.pop('asset', None)
        super().__init__(*args, **kwargs)
        if self.asset and self.asset.is_serialized:
            self.fields['serial_number'].queryset = SerialNumber.objects.filter(
                item=self.asset, status='IN_STOCK'
            )
            self.fields['quantity'].widget = forms.HiddenInput()
            self.fields['quantity'].initial = 1
        else:
            self.fields.pop('serial_number')


class SupplierForm(StyledModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address']


class PurchaseForm(StyledModelForm):
    class Meta:
        model = Purchase
        fields = ['supplier', 'invoice_number', 'purchase_date']
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
        }
