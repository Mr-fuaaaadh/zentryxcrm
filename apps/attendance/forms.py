from django import forms
from django.utils import timezone
from .models import Attendance
from apps.staff.models import Staff

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['staff', 'date', 'check_in', 'check_out', 'lunch_time_houre', 'status', 'is_approved', 'remarks']
        widgets = {
            'lunch_time_houre': forms.TextInput(attrs={'class': 'form-control', 'type': 'time'}),
            'staff': forms.Select(attrs={'class': 'form-select select2-staff'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'check_in': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'check_out': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter any additional notes or reason for attendance status...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        # lunch_time_houre = cleaned_data.get('lunch_time_houre')
        staff = cleaned_data.get('staff')
        date = cleaned_data.get('date')

        if not date:
            return cleaned_data

        # 1. Prevent future dates
        if date > timezone.now().date():
            self.add_error('date', "Attendance cannot be marked for a future date.")

        # 2. Check-out must be after check-in
        if check_in and check_out:
            if check_out <= check_in:
                self.add_error('check_out', "Check-out time must be after check-in time.")
            
            # Additional logic: Check-in/out should be on the attendance date
            if check_in.date() != date:
                 self.add_error('check_in', f"Check-in date ({check_in.date()}) must match attendance date ({date}).")
            if check_out.date() != date:
                 self.add_error('check_out', f"Check-out date ({check_out.date()}) must match attendance date ({date}).")

        # 3. Duplicate check for new records
        if not self.instance.pk:
            if Attendance.objects.filter(staff=staff, date=date).exists():
                raise forms.ValidationError(f"An attendance record already exists for {staff} on {date}.")

        return cleaned_data
