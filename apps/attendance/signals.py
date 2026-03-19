from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Count, Sum, Q
from .models import Attendance, MonthlyAttendanceSummary
from apps.staff.models import Staff
from django.utils import timezone

@receiver(post_save, sender=Attendance)
@receiver(post_delete, sender=Attendance)
def update_monthly_summary(sender, instance, **kwargs):
    """
    Update MonthlyAttendanceSummary whenever an Attendance record is saved or deleted.
    """
    staff = instance.staff
    date = instance.date
    month = date.month
    year = date.year

    # Get or create summary for this staff, month, and year
    summary, created = MonthlyAttendanceSummary.objects.get_or_create(
        staff=staff,
        month=month,
        year=year
    )

    # Calculate aggregates for this month
    stats = Attendance.objects.filter(
        staff=staff,
        date__month=month,
        date__year=year
    ).aggregate(
        present=Count('id', filter=Q(status='PRESENT')),
        absent=Count('id', filter=Q(status='ABSENT')),
        leave=Count('id', filter=Q(status='LEAVE')),
        half_day=Count('id', filter=Q(status='HALF_DAY')),
        late=Sum('late_minutes'),
        ot=Sum('overtime_minutes'),
        working_hours=Sum('total_working_hours')
    )

    # Update summary fields
    summary.total_present = stats['present'] or 0
    summary.total_absent = stats['absent'] or 0
    summary.total_leave = stats['leave'] or 0
    summary.total_half_day = stats['half_day'] or 0
    summary.total_late_minutes = stats['late'] or 0
    summary.total_overtime_minutes = stats['ot'] or 0
    summary.total_working_hours = stats['working_hours'] or 0
    summary.save()

@receiver(post_save, sender=Staff)
def auto_create_attendance_on_staff_add(sender, instance, created, **kwargs):
    """
    Automatically create an attendance record for the current day when a new staff member is added.
    """
    if created:
        today = timezone.now().date()
        Attendance.objects.get_or_create(
            staff=instance,
            date=today,
            defaults={'status': 'PRESENT', 'is_approved': False}
        )
