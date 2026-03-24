import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Department, Designation

logger = logging.getLogger('core.signals')

@receiver(post_save, sender=Department)
def log_department_save(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    logger.info(f"Department {action}: {instance.name} (Code: {instance.code})")

@receiver(post_delete, sender=Department)
def log_department_delete(sender, instance, **kwargs):
    logger.info(f"Department deleted: {instance.name} (Code: {instance.code})")

@receiver(post_save, sender=Designation)
def log_designation_save(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    logger.info(f"Designation {action}: {instance.title} (Level: {instance.level})")

@receiver(post_delete, sender=Designation)
def log_designation_delete(sender, instance, **kwargs):
    logger.info(f"Designation deleted: {instance.title}")
