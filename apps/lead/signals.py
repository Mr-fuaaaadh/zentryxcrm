from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Lead, LeadActivity
from apps.sales.models import StaffPerformance
from apps.staff.models import Staff


# -----------------------------------------
# Track previous status to detect changes
# -----------------------------------------
@receiver(pre_save, sender=Lead)
def track_previous_status(sender, instance, **kwargs):
    """Store the old status before save so we can detect transitions."""
    if instance.pk:
        try:
            instance._previous_status = Lead.objects.get(pk=instance.pk).status
        except Lead.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


# -----------------------------------------
# Lead Created -> Update Leads Generated
# -----------------------------------------
@receiver(post_save, sender=Lead)
def update_leads_generated(sender, instance, created, **kwargs):
    """When a new lead is assigned to a staff, increment their leads_generated."""
    if created and instance.assigned_to:
        staff = instance.assigned_to
        if isinstance(staff, Staff):
            today = timezone.now().date()
            performance, _ = StaffPerformance.objects.get_or_create(
                staff=staff,
                date=today
            )
            performance.leads_generated += 1
            performance.save(update_fields=['leads_generated'])


# -----------------------------------------
# Lead Status -> Won: Update Deals Closed
# -----------------------------------------
@receiver(post_save, sender=Lead)
def update_deals_closed(sender, instance, created, **kwargs):
    """
    When a lead's status transitions TO 'won', increment deals_closed
    and revenue_generated for the assigned staff.
    Only fires on the first transition, not on every subsequent save.
    """
    if created:
        return  # New lead — not a "won" transition yet

    previous_status = getattr(instance, '_previous_status', None)

    # Only act when status changes FROM something else TO 'won'
    if instance.status != 'won' or previous_status == 'won':
        return

    staff = instance.assigned_to
    if not isinstance(staff, Staff):
        return

    today = timezone.now().date()
    performance, _ = StaffPerformance.objects.get_or_create(
        staff=staff,
        date=today
    )
    performance.deals_closed += 1
    if instance.expected_revenue:
        performance.revenue_generated += instance.expected_revenue
    performance.save(update_fields=['deals_closed', 'revenue_generated'])


# -----------------------------------------
# LeadActivity Created -> Update Performance
# -----------------------------------------
@receiver(post_save, sender=LeadActivity)
def update_activity_performance(sender, instance, created, **kwargs):
    """
    When a new LeadActivity is logged, update the staff member's
    performance counters for calls, meetings, and proposals.
    """
    if not created:
        return

    staff = instance.created_by  # This is already a Staff object
    if not isinstance(staff, Staff):
        return  # Safety guard — skip if somehow not a Staff instance

    today = timezone.now().date()
    performance, _ = StaffPerformance.objects.get_or_create(
        staff=staff,  # Correct: pass the Staff object, not instance.created_by
        date=today
    )

    activity_type = instance.activity_type

    if activity_type == 'call':
        performance.calls_made += 1
        performance.save(update_fields=['calls_made'])
    elif activity_type == 'meeting':
        performance.meetings_booked += 1
        performance.save(update_fields=['meetings_booked'])
    elif activity_type == 'proposal':
        performance.proposals_sent += 1
        performance.save(update_fields=['proposals_sent'])