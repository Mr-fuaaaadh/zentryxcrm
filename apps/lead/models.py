from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import QuerySet
from apps.staff.models import Staff



class LeadQuerySet(QuerySet):

    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)


class LeadManager(models.Manager):

    def get_queryset(self):
        return LeadQuerySet(self.model, using=self._db).active()

    def all_with_deleted(self):
        return LeadQuerySet(self.model, using=self._db)

    def deleted(self):
        return LeadQuerySet(self.model, using=self._db).deleted()
    





class Lead(models.Model):

    STATUS_CHOICES = (
        ("new", "New"),
        ("contacted", "Contacted"),
        ("qualified", "Qualified"),
        ("proposal_sent", "Proposal Sent"),
        ("negotiation", "Negotiation"),
        ("won", "Won"),
        ("lost", "Lost"),
    )

    SOURCE_CHOICES = (
        ("website", "Website"),
        ("facebook", "Facebook"),
        ("instagram", "Instagram"),
        ("google_ads", "Google Ads"),
        ("referral", "Referral"),
        ("direct_call", "Direct Call"),
        ("other", "Other"),
    )

    PRIORITY_CHOICES = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    )

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)

    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)

    company_name = models.CharField(max_length=255, blank=True)
    designation = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
        db_index=True
    )

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default="website",
        db_index=True
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="medium",
        db_index=True
    )

    expected_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )

    assigned_to = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assigned_leads"
    )

    next_follow_up = models.DateTimeField(blank=True, null=True)

    notes = models.TextField(blank=True)

    is_converted = models.BooleanField(default=False)
    converted_at = models.DateTimeField(blank=True, null=True)

    is_deleted = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_leads"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LeadManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["email"]),
            models.Index(fields=["status"]),
            models.Index(fields=["assigned_to"]),
            models.Index(fields=["next_follow_up"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class LeadActivity(models.Model):

    ACTIVITY_TYPE_CHOICES = (
        ("call", "Call"),
        ("meeting", "Meeting"),
        ("proposal", "Proposal Sent"),
        ("closing", "Deal Closed"),
        ("email", "Email"),
        ("whatsapp", "WhatsApp"),
        ("note", "Note"),
    )

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="activities"
    )

    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPE_CHOICES
    )

    description = models.TextField(blank=True)

    activity_date = models.DateTimeField(default=timezone.now)

    created_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        related_name="activities"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-activity_date"]
        indexes = [
            models.Index(fields=["activity_type"]),
            models.Index(fields=["activity_date"])
        ]

    def __str__(self):
        return f"{self.activity_type} - {self.lead}"
