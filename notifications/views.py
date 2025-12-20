from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from events.models import Event
from rsvp.models import RSVP
from .utils import send_bulk_notification


@login_required
def send_event_notification(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    
    # Check permission
    if event.organizer != request.user:
        messages.error(request, 'You do not have permission to send notifications.')
        return redirect('events:event_detail', slug=event_slug)
    
    # Get attendee count
    attendees_count = RSVP.objects.filter(
        event=event,
        status='confirmed'
    ).count()
    
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        if not subject or not message:
            messages.error(request, 'Please provide both subject and message.')
        else:
            # Send notifications
            result = send_bulk_notification(event, subject, message)
            
            # Show results
            if result['success_count'] > 0:
                messages.success(
                    request, 
                    f'✅ Notification sent to {result["success_count"]} attendee(s)!'
                )
            
            if result['fail_count'] > 0:
                messages.warning(
                    request,
                    f'⚠️ Failed to send to {result["fail_count"]} attendee(s).'
                )
            
            if result['success_count'] == 0 and result['fail_count'] == 0:
                messages.info(request, 'No attendees to notify.')
            
            return redirect('rsvp:event_attendees', event_slug=event_slug)
    
    context = {
        'event': event,
        'attendees_count': attendees_count,
    }
    
    return render(request, 'notifications/send_notification.html', context)