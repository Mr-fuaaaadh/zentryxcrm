from django import forms
from .models import Project
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name', 'project_code', 'description', 
            'customer', 'lead', 'manager', 'team_members',
            'status', 'priority', 'start_date', 'end_date',
            'budget', 'estimated_cost'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Name'}),
            'project_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PRJ-001'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter project details...'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'lead': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'team_members': forms.SelectMultiple(attrs={'class': 'form-select select2-multiple'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
        }

    def clean_project_code(self):
        project_code = self.cleaned_data.get('project_code')
        queryset = Project.objects.filter(project_code=project_code)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ValidationError("A project with this code already exists.")
        return project_code

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise ValidationError({
                'end_date': "End date must be after the start date."
            })
        
        return cleaned_data
