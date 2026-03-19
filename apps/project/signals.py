from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Project, ProjectActivity

@receiver(post_save, sender=Project)
def log_project_creation(sender, instance, created, **kwargs):
    if created:
        ProjectActivity.objects.create(
            project=instance,
            activity_type='status_change',
            description=f"Project '{instance.name}' was created with status '{instance.get_status_display()}'.",
            created_by=instance.created_by
        )

@receiver(pre_save, sender=Project)
def log_project_changes(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = Project.objects.get(pk=instance.pk)
    except Project.DoesNotExist:
        return

    changes = []
    if old_instance.status != instance.status:
        changes.append(f"Status changed from '{old_instance.get_status_display()}' to '{instance.get_status_display()}'.")
    if old_instance.priority != instance.priority:
        changes.append(f"Priority changed from '{old_instance.get_priority_display()}' to '{instance.get_priority_display()}'.")

    if changes:
        ProjectActivity.objects.create(
            project=instance,
            activity_type='status_change',
            description=" | ".join(changes),
        )
