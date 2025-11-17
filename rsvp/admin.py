from django.contrib import admin
from .models import RSVP

@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'user', 'event', 'status', 'number_of_tickets', 'created_at']
    list_filter = ['status', 'created_at', 'event']
    search_fields = ['ticket_number', 'user__username', 'user__email', 'event__title']
    readonly_fields = ['ticket_number', 'qr_code', 'created_at', 'updated_at', 'confirmed_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('event', 'user', 'status', 'number_of_tickets')
        }),
        ('Ticket Details', {
            'fields': ('ticket_number', 'qr_code')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at'),
            'classes': ('collapse',)
        }),
    )