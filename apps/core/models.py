from django.db import models
import uuid


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True



class Department(TimeStampedModel):
    """
    Model representing a department within the organization.
    """
    name = models.CharField(max_length=100, unique=True, help_text="The full name of the department.")
    code = models.CharField(max_length=20, unique=True, help_text="A unique code for identifying the department (e.g., HR, IT).")

    is_active = models.BooleanField(default=True, help_text="Whether this department is currently active.")

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        ordering = ['name']
        indexes = [models.Index(fields=['code'])]

    def __str__(self):
        return f"{self.name} ({self.code})"



class Designation(TimeStampedModel):
    """
    Model representing a job title/designation within the organization.
    """
    title = models.CharField(max_length=100, unique=True, help_text="The title of the designation.")
    level = models.PositiveIntegerField(default=1, help_text="Hierarchy level (1 being the highest or most senior).")

    class Meta:
        verbose_name = "Designation"
        verbose_name_plural = "Designations"
        ordering = ['level', 'title']

    def __str__(self):
        return self.title


