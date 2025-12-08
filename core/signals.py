# core/signals.py

from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import MineralBatch, TransactionStatusLog


@receiver(pre_save, sender=MineralBatch)
def log_batch_status_change(sender, instance, **kwargs):
    """
    Log status change when MineralBatch status is updated.
    """
    if not instance.pk:
        # New batch — no previous status
        return

    try:
        previous = MineralBatch.objects.get(pk=instance.pk)
        if previous.status != instance.status:
            # Status changed — create log
            updated_by = instance.approved_by or instance.recorded_by  # fallback
            TransactionStatusLog.objects.create(
                transaction=instance,
                status=instance.status,
                updated_by=updated_by
            )
    except MineralBatch.DoesNotExist:
        pass  # Should not happen, but safe