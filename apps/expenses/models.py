from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
import os


class Expense(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    )

    expense_number = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    expense_date = models.DateField(default=timezone.now)
    due_date = models.DateField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_expenses'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_expenses'
    )

    notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'

    def __str__(self):
        return f"{self.expense_number} - {self.title}"

    def save(self, *args, **kwargs):
        self.total_amount = (self.amount or Decimal('0.00')) + (self.tax_amount or Decimal('0.00'))
        super().save(*args, **kwargs)

    @property
    def paid_amount(self):
        return self.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    @property
    def balance_amount(self):
        return (self.total_amount or Decimal('0.00')) - self.paid_amount

    def update_payment_status(self):
        if self.status == 'rejected':
            return

        if self.paid_amount == Decimal('0.00'):
            self.status = 'approved'
        elif self.paid_amount < self.total_amount:
            self.status = 'partial'
        else:
            self.status = 'paid'

        self.save(update_fields=['status', 'updated_at'])


class ExpensePayment(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('cheque', 'Cheque'),
    )

    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')

    reference_number = models.CharField(max_length=100, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expense_payments'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']
        verbose_name = 'Expense Payment'
        verbose_name_plural = 'Expense Payments'

    def __str__(self):
        return f"{self.expense.expense_number} - {self.amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.expense.update_payment_status()

    def delete(self, *args, **kwargs):
        expense = self.expense
        super().delete(*args, **kwargs)
        expense.update_payment_status()


class ExpenseAttachment(models.Model):
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='expense_files/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expense_attachments'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def filename(self):
        return os.path.basename(self.file.name) if self.file else ""

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Expense Attachment'
        verbose_name_plural = 'Expense Attachments'

    def __str__(self):
        return self.file.name if self.file else "Attachment"


class ExpenseActivityLog(models.Model):
    ACTION_CHOICES = (
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('payment_added', 'Payment Added'),
        ('payment_deleted', 'Payment Deleted'),
        ('attachment_added', 'Attachment Added'),
    )

    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    message = models.CharField(max_length=255)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expense_activity_logs'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Expense Activity Log'
        verbose_name_plural = 'Expense Activity Logs'

    def __str__(self):
        return f"{self.expense.expense_number} - {self.action}"