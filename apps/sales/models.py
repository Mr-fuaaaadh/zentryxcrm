from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL



class StaffMonthlyTarget(models.Model):

    staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
        related_name="monthly_targets"
    )

    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()

    leads_target = models.PositiveIntegerField(default=0)
    calls_target = models.PositiveIntegerField(default=0)
    meetings_target = models.PositiveIntegerField(default=0)
    proposals_target = models.PositiveIntegerField(default=0)
    deals_target = models.PositiveIntegerField(default=0)

    revenue_target = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("staff", "month", "year")
        indexes = [
            models.Index(fields=["staff", "month", "year"])
        ]

    def __str__(self):
        return f"{self.staff} Target {self.month}/{self.year}"
    


class StaffPerformance(models.Model):

    staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
        related_name="performances"
    )

    date = models.DateField()

    leads_generated = models.PositiveIntegerField(default=0)
    calls_made = models.PositiveIntegerField(default=0)
    meetings_booked = models.PositiveIntegerField(default=0)
    proposals_sent = models.PositiveIntegerField(default=0)
    deals_closed = models.PositiveIntegerField(default=0)

    revenue_generated = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("staff", "date")
        indexes = [
            models.Index(fields=["staff", "date"])
        ]

    def __str__(self):
        return f"{self.staff} Performance {self.date}"
    

class BaseDocument(models.Model):

    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("SENT", "Sent"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled"),
    )

    document_number = models.CharField(max_length=50, unique=True)

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="%(class)ss"
    )

    price_level = models.ForeignKey(
        'PriceLevel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)ss"
    )

    issue_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT"
    )

    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True



class Proposal(BaseDocument):

    class Meta:
        ordering = ["-issue_date"]

    def __str__(self):
        return f"Proposal - {self.document_number}"
    

class Estimate(BaseDocument):

    class Meta:
        ordering = ["-issue_date"]

    def __str__(self):
        return f"Estimate - {self.document_number}"
    



class Invoice(BaseDocument):

    PAYMENT_STATUS = (
        ("UNPAID", "Unpaid"),
        ("PARTIAL", "Partial"),
        ("PAID", "Paid"),
        ("OVERDUE", "Overdue"),
    )

    due_date = models.DateField()

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="UNPAID"
    )

    class Meta:
        ordering = ["-issue_date"]

    def update_payment_status(self):
        total_paid = sum(p.amount for p in self.payments.all())

        if total_paid == 0:
            self.payment_status = "UNPAID"
        elif total_paid < self.total_amount:
            self.payment_status = "PARTIAL"
        else:
            self.payment_status = "PAID"

        self.save(update_fields=["payment_status"])

    def __str__(self):
        return f"Invoice - {self.document_number}"
    


class PriceLevel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProductPrice(models.Model):
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name="price_tiers"
    )
    price_level = models.ForeignKey(
        PriceLevel,
        on_delete=models.CASCADE,
        related_name="product_prices"
    )
    price = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        unique_together = ('product', 'price_level')

    def __str__(self):
        return f"{self.product.name} - {self.price_level.name}: {self.price}"


class Product(models.Model):

    proposal = models.ForeignKey(Proposal,on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="items"
    )

    estimate = models.ForeignKey(Estimate,on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="items"
    )

    invoice = models.ForeignKey( Invoice,on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="items"
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name






class Payment(models.Model):

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    payment_date = models.DateField(default=timezone.now)

    amount = models.DecimalField(max_digits=14, decimal_places=2)

    method = models.CharField(
        max_length=20,
        choices=(
            ("CASH", "Cash"),
            ("BANK", "Bank Transfer"),
            ("CARD", "Card"),
            ("UPI", "UPI"),
        )
    )

    reference_number = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invoice.update_payment_status()

    def __str__(self):
        return f"{self.invoice.document_number} - {self.amount}"
    


class CreditNote(models.Model):

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="credit_notes"
    )

    credit_number = models.CharField(max_length=50, unique=True)

    amount = models.DecimalField(max_digits=14, decimal_places=2)

    reason = models.TextField(blank=True)

    issued_date = models.DateField(default=timezone.now)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.credit_number