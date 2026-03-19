from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
import uuid

class StudentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        return super().get_queryset()

class Student(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('GRADUATED', 'Graduated'),
        ('DROPPED', 'Dropped'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    student_id = models.CharField(max_length=30, unique=True, editable=False)
    
    course = models.ForeignKey(
        'course.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    joining_date = models.DateField(default=timezone.now)
    emergency_contact = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    
    is_deleted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = StudentManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['status']),
        ]

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def save(self, *args, **kwargs):
        if not self.student_id:
            with transaction.atomic():
                last = Student.all_with_deleted().select_for_update().order_by('-created_at').first()
                if last and last.student_id:
                    try:
                        last_number = int(last.student_id.split('-')[-1])
                        new_number = last_number + 1
                    except (ValueError, IndexError):
                        new_number = 1
                else:
                    new_number = 1
                self.student_id = f"STD-{timezone.now().year}-{new_number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student_id} - {self.user.get_full_name()}"
