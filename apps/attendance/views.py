from django.views.generic import ListView, CreateView, UpdateView
from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from datetime import datetime, date
from .models import Attendance
from .forms import AttendanceForm
import calendar

class AttendanceListView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = 'attendance/list.html'
    context_object_name = 'attendance_list'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().select_related('staff__user', 'shift', 'staff__department', 'staff__designation')
        
        # Search
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(staff__user__first_name__icontains=search) |
                Q(staff__user__last_name__icontains=search) |
                Q(staff__employee_id__icontains=search)
            )

        # Filters
        date_val = self.request.GET.get('date')
        if date_val:
            try:
                queryset = queryset.filter(date=date_val)
            except (ValueError, ValidationError):
                pass

        month = self.request.GET.get('month')
        year = self.request.GET.get('year')
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(staff__department_id=department)

        designation = self.request.GET.get('designation')
        if designation:
            queryset = queryset.filter(staff__designation_id=designation)

        shift = self.request.GET.get('shift')
        if shift:
            queryset = queryset.filter(shift_id=shift)

        # Sorting
        sort = self.request.GET.get('sort', '-date')
        valid_sorts = ['date', '-date', 'staff__user__first_name', '-staff__user__first_name', 'total_working_hours', '-total_working_hours']
        if sort in valid_sorts:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        
        # Filter persistence
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_date'] = self.request.GET.get('date', '')
        context['selected_month'] = self.request.GET.get('month', '')
        context['selected_year'] = self.request.GET.get('year', str(today.year))
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_dept'] = self.request.GET.get('department', '')
        context['selected_desig'] = self.request.GET.get('designation', '')
        context['selected_shift'] = self.request.GET.get('shift', '')
        context['current_sort'] = self.request.GET.get('sort', '-date')

        # Metadata for dropdowns
        context['months'] = [(i, calendar.month_name[i]) for i in range(1, 13)]
        context['years'] = range(today.year - 5, today.year + 2)
        context['status_choices'] = Attendance.STATUS_CHOICES
        
        from apps.core.models import Department, Designation
        from apps.hr.models import Shift
        context['departments'] = Department.objects.all()
        context['designations'] = Designation.objects.all()
        context['shifts'] = Shift.objects.filter(is_active=True)

        # Summary Metrics
        summary_qs = self.get_queryset()
        summary = summary_qs.aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status='PRESENT')),
            absent=Count('id', filter=Q(status='ABSENT')),
            half_day=Count('id', filter=Q(status='HALF_DAY')),
            on_leave=Count('id', filter=Q(status='LEAVE')),
            late=Count('id', filter=Q(late_minutes__gt=0)),
            avg_hours=models.Avg('total_working_hours')
        )
        context['summary'] = summary
        
        # Pulse Logic: Current Date Check
        context['is_today'] = (context['selected_date'] == str(today)) or (not context['selected_date'])
        
        return context

import csv
from django.http import HttpResponse

@login_required
def export_attendance_csv(request):
    """
    Export filtered attendance records to CSV.
    """
    view = AttendanceListView()
    view.request = request
    queryset = view.get_queryset()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Employee ID', 'Name', 'Date', 'Status', 'Check In', 'Check Out', 'Lunch Break (Hrs)', 'Working Hours', 'Late (min)', 'Overtime (min)', 'Approved'])

    for record in queryset:
        # localizing times for export if they are aware
        check_in_str = ''
        if record.check_in:
            local_in = timezone.localtime(record.check_in) if timezone.is_aware(record.check_in) else record.check_in
            check_in_str = local_in.strftime('%H:%M')
            
        check_out_str = ''
        if record.check_out:
            local_out = timezone.localtime(record.check_out) if timezone.is_aware(record.check_out) else record.check_out
            check_out_str = local_out.strftime('%H:%M')

        writer.writerow([
            record.staff.employee_id,
            record.staff.user.get_full_name(),
            record.date,
            record.get_status_display(),
            check_in_str,
            check_out_str,
            record.lunch_time_houre,
            record.total_working_hours,
            record.late_minutes,
            record.overtime_minutes,
            'Yes' if record.is_approved else 'No'
        ])

    return response

class AttendanceCreateView(LoginRequiredMixin, CreateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = 'attendance/add.html'
    success_url = reverse_lazy('attendance:list')

    def form_valid(self, form):
        messages.success(self.request, "Attendance record created successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error creating the attendance record.")
        return super().form_invalid(form)

class AttendanceUpdateView(LoginRequiredMixin, UpdateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = 'attendance/add.html'
    success_url = reverse_lazy('attendance:list')

    def form_valid(self, form):
        messages.success(self.request, "Attendance record updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error updating the attendance record.")
        return super().form_invalid(form)
