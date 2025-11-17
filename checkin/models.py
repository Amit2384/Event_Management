from django.db import models
from django.contrib.auth.models import User
from rsvp.models import RSVP

class CheckIn(models.Model):
    """
    Records attendee check-ins at events.
    Tracks who checked in, when, and by whom.
    """
    
    rsvp = models.OneToOneField(RSVP, on_delete=models.CASCADE, related_name='checkin')
    checked_in_at = models.DateTimeField(auto_now_add=True)
    checked_in_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='checkins_performed',
        help_text="Staff member who performed the check-in"
    )
    notes = models.TextField(blank=True, null=True, help_text="Check-in notes")
    
    def __str__(self):
        return f"{self.rsvp.user.username} - {self.rsvp.event.title}"
    
    class Meta:
        db_table = 'checkins'
        ordering = ['-checked_in_at']
        verbose_name = 'Check-in'
        verbose_name_plural = 'Check-ins'