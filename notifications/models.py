from django.db import models
from django.contrib.auth.models import User
from events.models import Event

class Notification(models.Model):
    """
    Track all notifications sent through the system.
    Optional model for notification history.
    """
    
    NOTIFICATION_TYPES = (
        ('event_created', 'Event Created'),
        ('event_updated', 'Event Updated'),
        ('rsvp_created', 'RSVP Created'),
        ('rsvp_cancelled', 'RSVP Cancelled'),
        ('event_reminder', 'Event Reminder'),
        ('checkin_confirmation', 'Check-in Confirmation'),
        ('bulk_message', 'Bulk Message'),
    )
    
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.notification_type} - {self.recipient.username}"
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-sent_at']