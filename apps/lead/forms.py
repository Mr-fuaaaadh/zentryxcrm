from django import forms
from .models import Lead, LeadActivity
from apps.staff.models import Staff


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'company_name', 'designation', 'status',
            'source', 'priority', 'expected_revenue',
            'next_follow_up', 'notes', 'assigned_to'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Designation'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'expected_revenue': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'next_follow_up': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Additional notes...'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active staff members in the assignee dropdown
        self.fields['assigned_to'].queryset = Staff.objects.filter(
            is_active=True
        ).select_related('user').order_by('user__first_name', 'user__last_name')
        # Show a human-readable label for each staff member
        self.fields['assigned_to'].label_from_instance = lambda obj: obj.user.get_full_name() or obj.user.username

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise forms.ValidationError("Phone number is required.")
        clean_phone = ''.join(filter(str.isdigit, phone))
        if len(clean_phone) < 10:
            raise forms.ValidationError("Please enter a valid phone number with at least 10 digits.")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and Lead.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A lead with this email already exists.")
        return email


class LeadActivityForm(forms.ModelForm):
    class Meta:
        model = LeadActivity
        fields = ['activity_type', 'description', 'activity_date']
        widgets = {
            'activity_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the interaction...'}),
            'activity_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
