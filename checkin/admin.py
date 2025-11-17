from django.contrib import admin
from .models import CheckIn

@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ['get_attendee', 'get_event', 'checked_in_at', 'checked_in_by']
    list_filter = ['checked_in_at', 'rsvp__event']
    search_fields = ['rsvp__user__username', 'rsvp__user__email', 'rsvp__ticket_number']
    readonly_fields = ['checked_in_at']
    
    def get_attendee(self, obj):
        return obj.rsvp.user.get_full_name()
    get_attendee.short_description = 'Attendee'
    
    def get_event(self, obj):
        return obj.rsvp.event.title
    get_event.short_description = 'Event'