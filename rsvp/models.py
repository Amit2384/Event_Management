from django.db import models
from django.contrib.auth.models import User
from events.models import Event
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

class RSVP(models.Model):
    """
    RSVP model for event registration.
    Handles user responses and ticket generation.
    """
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('attended', 'Attended'),
    )
    
    # Basic Information
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rsvps')
    
    # RSVP Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    number_of_tickets = models.IntegerField(default=1)
    
    # Ticket Information
    ticket_number = models.CharField(max_length=100, unique=True, blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional Information
    notes = models.TextField(blank=True, null=True, help_text="Special requests or notes")
    
    def save(self, *args, **kwargs):
        """Generate ticket number and QR code on creation"""
        if not self.ticket_number:
            # Generate unique ticket number
            self.ticket_number = f"TKT-{uuid.uuid4().hex[:12].upper()}"
        
        super().save(*args, **kwargs)
        
        # Generate QR code if not exists
        if not self.qr_code:
            self.generate_qr_code()
    
    def generate_qr_code(self):
        """Generate QR code for ticket"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # QR code data includes ticket number and event info
        qr_data = f"TICKET:{self.ticket_number}|EVENT:{self.event.id}|USER:{self.user.id}"
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to file
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        file_name = f'qr_{self.ticket_number}.png'
        self.qr_code.save(file_name, File(buffer), save=False)
        buffer.close()
        
        # Save without triggering save method again
        super().save(update_fields=['qr_code'])
    
    def confirm(self):
        """Confirm RSVP"""
        from django.utils import timezone
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        self.save()
    
    def cancel(self):
        """Cancel RSVP and restore event seats"""
        self.status = 'cancelled'
        self.event.available_seats += self.number_of_tickets
        self.event.save()
        self.save()
    
    def mark_attended(self):
        """Mark as attended during check-in"""
        self.status = 'attended'
        self.save()
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.ticket_number})"
    
    class Meta:
        db_table = 'rsvps'
        unique_together = ['event', 'user']
        ordering = ['-created_at']
        verbose_name = 'RSVP'
        verbose_name_plural = 'RSVPs'