from django.utils import timezone

def update_status(transaction, new_status, user=None):
    """
    Safely update status of a transaction and log who made the change.
    
    Args:
        transaction: The transaction instance to update.
        new_status (str): New status value.
        user: User making the change (optional).
    
    Returns:
        transaction: Updated transaction instance.
    """
    allowed_statuses = ['pending', 'approved', 'completed', 'rejected']
    if new_status not in allowed_statuses:
        raise ValueError(f"Invalid status: {new_status}")

    transaction.status = new_status
    transaction.last_updated = timezone.now()

    # Optionally log update metadata
    if hasattr(transaction, 'updated_by') and user:
        transaction.updated_by = user

    transaction.save()
    return transaction
