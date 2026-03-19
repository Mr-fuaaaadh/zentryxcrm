from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Expense
import datetime

@receiver(pre_save, sender=Expense)
def generate_expense_number(sender, instance, **kwargs):
    if not instance.expense_number:
        # Generate format: EXP-YYYYMMDD-XXXX
        today = datetime.date.today()
        prefix = f"EXP-{today.strftime('%Y%m%d')}"
        last_expense = Expense.objects.filter(expense_number__startswith=prefix).order_by('-expense_number').first()
        
        if last_expense:
            last_number = int(last_expense.expense_number.split('-')[-1])
            new_number = f"{last_number + 1:04d}"
        else:
            new_number = "0001"
            
        instance.expense_number = f"{prefix}-{new_number}"

@receiver(pre_save, sender=Expense)
def calculate_total_amount(sender, instance, **kwargs):
    instance.tax_amount = instance.tax_amount or 0
    instance.total_amount = instance.amount + instance.tax_amount
