from django.db import models

# Create your models here.
class Shift(models.Model):

    name = models.CharField(max_length=100, unique=True)

    start_time = models.TimeField()
    end_time = models.TimeField()

    grace_minutes = models.PositiveIntegerField(default=15)
    half_day_threshold_minutes = models.PositiveIntegerField(default=240)

    working_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Expected working hours per shift"
    )

    is_night_shift = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return self.name
    

class Holiday(models.Model):

    name = models.CharField(max_length=200)
    date = models.DateField(unique=True)
    is_paid = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.name} - {self.date}"
    


class Leave(models.Model):

    LEAVE_TYPE = (
        ("CASUAL", "Casual Leave"),
        ("SICK", "Sick Leave"),
        ("ANNUAL", "Annual Leave"),
        ("UNPAID", "Unpaid Leave"),
    )

    STATUS = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    staff = models.ForeignKey(
        "staff.Staff",
        on_delete=models.CASCADE,
        related_name="leaves"
    )

    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE)
    start_date = models.DateField()
    end_date = models.DateField()

    reason = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="PENDING"
    )

    approved_by = models.ForeignKey(
        "staff.Staff",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_leaves"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.staff.employee_id} - {self.leave_type}"