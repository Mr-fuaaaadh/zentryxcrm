from django.db import models
from datetime import timedelta, datetime
from django.utils import timezone
from apps.hr.models import Shift


class Attendance(models.Model):

    STATUS_CHOICES = (
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("HALF_DAY", "Half Day"),
        ("LEAVE", "Leave"),
        ("HOLIDAY", "Holiday"),
        ("WEEK_OFF", "Week Off"),
    )

    staff = models.ForeignKey(
        "staff.Staff",
        on_delete=models.CASCADE,
        related_name="attendances"
    )

    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    date = models.DateField()

    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)

    lunch_time_houre = models.PositiveIntegerField(default=1)

    total_working_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    late_minutes = models.PositiveIntegerField(default=0)

    overtime_minutes = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PRESENT"
    )

    is_approved = models.BooleanField(default=False)

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("staff", "date")
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["staff", "date"]),
            models.Index(fields=["status"]),
        ]

    def calculate_hours(self):
        if self.check_in and self.check_out:
            # Calculate total duration
            duration = self.check_out - self.check_in
            total_seconds = duration.total_seconds()
            
            # Subtract lunch break (converted to seconds)
            lunch_seconds = self.lunch_time_houre * 3600
            net_seconds = total_seconds - lunch_seconds
            
            if net_seconds < 0:
                net_seconds = 0
                
            # Convert to hours with 2 decimal places
            self.total_working_hours = round(float(net_seconds / 3600.0), 2)

            # Late and Overtime calculation based on Shift
            if self.shift:
                # Combine date and shift start time for comparison
                shift_start = datetime.combine(self.date, self.shift.start_time)
                
                check_in_local = self.check_in
                if timezone.is_aware(check_in_local):
                    check_in_local = timezone.localtime(check_in_local).replace(tzinfo=None)
                
                # Late Minutes calculation
                grace_period = timedelta(minutes=self.shift.grace_minutes)
                if check_in_local > (shift_start + grace_period):
                    late_delta = check_in_local - shift_start
                    self.late_minutes = int(late_delta.total_seconds() / 60)
                else:
                    self.late_minutes = 0

                # Overtime calculation based on shift expected working hours
                expected_hours = float(self.shift.working_hours)
                if total_hours > expected_hours:
                    overtime = total_hours - expected_hours
                    self.overtime_minutes = int(overtime * 60)
                else:
                    self.overtime_minutes = 0
            else:
                # Fallback to standard 8 hours if no shift is assigned
                if total_hours > 8:
                    overtime = total_hours - 8
                    self.overtime_minutes = int(overtime * 60)
                else:
                    self.overtime_minutes = 0
                self.late_minutes = 0

    def save(self, *args, **kwargs):

        self.calculate_hours()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.staff.employee_id} - {self.date}"
    




class MonthlyAttendanceSummary(models.Model):

    staff = models.ForeignKey(
        "staff.Staff",
        on_delete=models.CASCADE,
        related_name="monthly_attendance"
    )

    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()

    total_present = models.PositiveIntegerField(default=0)
    total_absent = models.PositiveIntegerField(default=0)
    total_leave = models.PositiveIntegerField(default=0)
    total_half_day = models.PositiveIntegerField(default=0)
    total_overtime_minutes = models.PositiveIntegerField(default=0)
    total_late_minutes = models.PositiveIntegerField(default=0)
    total_working_hours = models.DecimalField(max_digits=6,decimal_places=2,default=0)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("staff", "month", "year")
        indexes = [
            models.Index(fields=["month", "year"]),
        ]

    def __str__(self):
        return f"{self.staff.employee_id} - {self.month}/{self.year}"