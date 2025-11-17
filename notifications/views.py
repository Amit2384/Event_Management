from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from events.models import Event
from .utils import send_bulk_notification

@login_required
def send_event_notification(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    
    if event.organizer != request.user:
        messages.error(request, 'You do not have permission to send notifications.')
        return redirect('events:event_detail', slug=event_slug)
    
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        if not subject or not message:
            messages.error(request, 'Please provide both subject and message.')
        else:
            send_bulk_notification(event, subject, message)
            messages.success(request, 'Notification sent successfully!')
            return redirect('events:event_detail', slug=event_slug)
    
    return render(request, 'notifications/send_notification.html', {'event': event})