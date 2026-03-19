from django import forms
from django.contrib.auth import get_user_model
from .models import Staff
from apps.core.models import Department, Designation

User = get_user_model()

class StaffForm(forms.ModelForm):
    # User fields
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter First Name'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Last Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))
    profile_image = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'd-none', 'id': 'profile_image'}))

    class Meta:
        model = Staff
        fields = [
            'department', 'designation', 'reporting_manager', 
            'employment_type', 'employment_status', 'joining_date',
            'official_phone', 'personal_phone', 'address'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select select2'}),
            'designation': forms.Select(attrs={'class': 'form-select select2'}),
            'reporting_manager': forms.Select(attrs={'class': 'form-select select2'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'employment_status': forms.Select(attrs={'class': 'form-select'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-MM-DD', 'data-provide': 'datepicker', 'data-date-format': 'yyyy-mm-dd'}),
            'official_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Official Extension or Phone'}),
            'personal_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 890'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': '1', 'placeholder': 'Enter Permanent Address'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        email = cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
            
        return cleaned_data

class StaffUpdateForm(forms.ModelForm):
    # User fields for update (Email usually readonly or handled carefully)
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))
    profile_image = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'd-none', 'id': 'profile_image'}))

    class Meta:
        model = Staff
        fields = [
            'department', 'designation', 'reporting_manager', 
            'employment_type', 'employment_status', 'joining_date',
            'official_phone', 'personal_phone', 'address'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select select2'}),
            'designation': forms.Select(attrs={'class': 'form-select select2'}),
            'reporting_manager': forms.Select(attrs={'class': 'form-select select2'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'employment_status': forms.Select(attrs={'class': 'form-select'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'data-provide': 'datepicker', 'data-date-format': 'yyyy-mm-dd'}),
            'official_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'personal_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
