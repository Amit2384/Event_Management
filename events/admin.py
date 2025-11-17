from django.contrib import admin
from .models import Event #, Category

# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ['name', 'event_count', 'created_at']
#     search_fields = ['name', 'description']
#     readonly_fields = ['created_at']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'organizer', 'status', 'start_date', 'event_type', 'available_seats']
    list_filter = ['status', 'event_type', 'start_date']
    search_fields = ['title', 'description', 'organizer__username']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'slug']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'organizer')
        }),
        ('Event Details', {
            'fields': ('event_type', 'status', 'start_date', 'end_date')
        }),
        ('Location', {
            'fields': ('venue_name', 'venue_address', 'city', 'state', 'country', 'zip_code')
        }),
        ('Capacity & Pricing', {
            'fields': ('total_seats', 'available_seats', 'ticket_price')
        }),
        ('Media', {
            'fields': ('banner_image',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )