from django.db import models
import uuid


class TimeStampedUUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True



class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['code'])]

    def __str__(self):
        return self.name



class Designation(models.Model):
    title = models.CharField(max_length=100, unique=True)
    level = models.PositiveIntegerField(default=1)  # hierarchy level

    def __str__(self):
        return self.title
