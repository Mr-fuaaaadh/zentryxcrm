from django.conf import settings
from django.utils import timezone
from django.db import models, transaction
from apps.core.models import Department, Designation
import uuid


class Staff(models.Model):

    EMPLOYMENT_TYPE = (
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('INTERN', 'Intern'),
    )

    EMPLOYMENT_STATUS = (
        ('ACTIVE', 'Active'),
        ('ON_LEAVE', 'On Leave'),
        ('RESIGNED', 'Resigned'),
        ('TERMINATED', 'Terminated'),
    )


    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile'
    )

    employee_id = models.CharField(max_length=30, unique=True, editable=False)

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name="staff_members"
    )

    designation = models.ForeignKey(
        Designation,
        on_delete=models.SET_NULL,
        null=True
    )

    reporting_manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_members"
    )

    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE)
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS,
        default='ACTIVE'
    )

    joining_date = models.DateField()
    confirmation_date = models.DateField(null=True, blank=True)
    relieving_date = models.DateField(null=True, blank=True)

    official_phone = models.CharField(max_length=20, blank=True)
    personal_phone = models.CharField(max_length=20, blank=True)

    address = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['employee_id']
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['employment_status']),
        ]

    def save(self, *args, **kwargs):
        if not self.employee_id:
            with transaction.atomic():
                last = Staff.objects.select_for_update().order_by('-created_at').first()
                if last and last.employee_id:
                    last_number = int(last.employee_id.split('-')[-1])
                    new_number = last_number + 1
                else:
                    new_number = 1
                self.employee_id = f"EMP-{timezone.now().year}-{new_number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})" if self.user.get_full_name() else f"{self.user.username} ({self.employee_id})"





