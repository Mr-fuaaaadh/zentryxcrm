from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'customer_type', 'name', 'company_name', 'email', 
            'phone', 'alternate_phone', 'gst_number', 'website', 
            'assigned_to', 'source', 'is_active', 'notes'
        ]
        widgets = {
            'customer_type': forms.Select(attrs={'class': 'form-select select2', 'data-placeholder': 'Select Type'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. John Doe'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Acme Corp'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@domain.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +91 9876543210'}),
            'alternate_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional GSTIN'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select select2', 'data-placeholder': 'Assign to staff'}),
            'source': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Website, Referral'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Internal notes about the customer...'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email').lower().strip()
        qs = Customer.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise forms.ValidationError("A customer with this email address already exists in our records.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone').strip()
        # Basic normalization could be added here if needed
        qs = Customer.objects.filter(phone=phone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise forms.ValidationError("This phone number is already registered to another customer.")
        return phone

    def clean_website(self):
        website = self.cleaned_data.get('website')
        if website and not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        return website
