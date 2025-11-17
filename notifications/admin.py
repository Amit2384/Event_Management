from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['notification_type', 'recipient', 'event', 'subject', 'sent_at', 'is_read']
    list_filter = ['notification_type', 'is_read', 'sent_at']
    search_fields = ['recipient__username', 'subject', 'message']
    readonly_fields = ['sent_at']