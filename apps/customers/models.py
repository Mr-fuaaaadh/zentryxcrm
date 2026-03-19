from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL


class CustomerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        return super().get_queryset()

class Customer(models.Model):

    CUSTOMER_TYPE = (
        ('INDIVIDUAL', 'Individual'),
        ('COMPANY', 'Company'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_code = models.CharField(max_length=30, unique=True, editable=False)
    customer_type = models.CharField(max_length=20,choices=CUSTOMER_TYPE,default='INDIVIDUAL')
    name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20, db_index=True)
    alternate_phone = models.CharField(max_length=20, blank=True)
    gst_number = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    assigned_to = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name='assigned_customers')
    source = models.CharField(max_length=100,blank=True,help_text="Website / Facebook / Referral / Cold Call")
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomerManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer_code']),
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
        ]

    def __str__(self):
        return f"{self.name} ({self.customer_code})"

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def save(self, *args, **kwargs):
        if Customer.objects.filter(
            email=self.email
        ).exclude(pk=self.pk).exists():
            raise ValueError("Customer with this email already exists.")

        super().save(*args, **kwargs)
