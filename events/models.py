from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse


# Category to comment out
# class Category(models.Model):
#     """
#     Event categories for organizing events.
#     Examples: Conference, Workshop, Seminar, Concert, etc.
#     """
#     name = models.CharField(max_length=100, unique=True)
#     description = models.TextField(blank=True)
#     icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return self.name
    
#     def event_count(self):
#         return self.events.filter(status='published').count()
    
#     class Meta:
#         db_table = 'categories'
#         verbose_name_plural = 'Categories'
#         ordering = ['name']

class Event(models.Model):
    """
    Main event model containing all event information.
    Handles event creation, updates, and status management.
    """
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    EVENT_TYPES = (
        ('free', 'Free'),
        ('paid', 'Paid'),
    )
    
    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    # category = models.ForeignKey(
    #     Category, 
    #     on_delete=models.SET_NULL, 
    #     null=True, 
    #     related_name='events'
    # )
    organizer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='organized_events'
    )
    
    # Event Details
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES, default='free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Date and Time
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Location
    venue_name = models.CharField(max_length=200)
    venue_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    
    # Capacity
    total_seats = models.IntegerField()
    available_seats = models.IntegerField()
    
    # Pricing
    ticket_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Price per ticket (0.00 for free events)"
    )
    
    # Media
    banner_image = models.ImageField(
        upload_to='event_banners/', 
        blank=True, 
        null=True,
        help_text="Event banner image"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Generate slug and set available seats on creation"""
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Set available seats equal to total seats on first save
        if not self.pk:
            self.available_seats = self.total_seats
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('events:event_detail', kwargs={'slug': self.slug})
    
    def is_full(self):
        """Check if event is fully booked"""
        return self.available_seats <= 0
    
    def get_booked_seats(self):
        """Calculate number of booked seats"""
        return self.total_seats - self.available_seats
    
    def get_booking_percentage(self):
        """Calculate booking percentage"""
        if self.total_seats > 0:
            return (self.get_booked_seats() / self.total_seats) * 100
        return 0
    
    def is_upcoming(self):
        """Check if event is upcoming"""
        from django.utils import timezone
        return self.start_date > timezone.now()
    
    def is_past(self):
        """Check if event is past"""
        from django.utils import timezone
        return self.end_date < timezone.now()
    
    class Meta:
        db_table = 'events'
        ordering = ['-start_date']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'