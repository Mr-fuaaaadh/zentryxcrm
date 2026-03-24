from django import forms
from .models import Department, Designation

class DepartmentForm(forms.ModelForm):
    """
    Form for creating and updating Department instances.
    """
    class Meta:
        model = Department
        fields = ['name', 'code', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Department Name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Department Code (e.g., HR)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DesignationForm(forms.ModelForm):
    """
    Form for creating and updating Designation instances.
    """
    class Meta:
        model = Designation
        fields = ['title', 'level']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Designation Title'}),
            'level': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Hierarchy Level'}),
        }
