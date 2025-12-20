from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from rsvp.models import RSVP


def send_bulk_notification(event, subject, message):
    """
    Send bulk notification to all confirmed attendees of an event
    """
    from django.contrib.sites.shortcuts import get_current_site
    from django.http import HttpRequest
    
    # Get all confirmed attendees
    attendees = RSVP.objects.filter(
        event=event,
        status='confirmed'
    ).select_related('user')
    
    success_count = 0
    fail_count = 0
    
    # Create a dummy request object for domain (if needed)
    domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')
    
    for rsvp in attendees:
        try:
            context = {
                'rsvp': rsvp,
                'event': event,
                'attendee': rsvp.user,
                'subject': subject,
                'message': message,
                'domain': domain,
            }
            
            email_subject = f'{subject} - {event.title}'
            
            # Render HTML email
            html_message = render_to_string(
                'notifications/emails/bulk_notification.html',
                context
            )
            
            # Render plain text email
            plain_message = render_to_string(
                'notifications/emails/bulk_notification.txt',
                context
            )
            
            # Send email
            send_mail(
                email_subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [rsvp.user.email],
                html_message=html_message,
                fail_silently=True,
            )
            
            success_count += 1
            
        except Exception as e:
            print(f"Failed to send notification to {rsvp.user.email}: {e}")
            fail_count += 1
    
    return {
        'success_count': success_count,
        'fail_count': fail_count,
        'total_sent': success_count,
        'total_failed': fail_count
    }


def send_event_notification(event, notification_type):
    """
    Send event-related notifications (created, updated, cancelled)
    This is called when organizer creates/updates/cancels events
    """
    from django.contrib.sites.shortcuts import get_current_site
    
    domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')
    
    if notification_type == 'created':
        # Notify organizer that event was created
        try:
            context = {
                'event': event,
                'domain': domain,
            }
            
            subject = f'Event Created: {event.title}'
            html_message = render_to_string(
                'notifications/emails/event_created.html',
                context
            )
            plain_message = render_to_string(
                'notifications/emails/event_created.txt',
                context
            )
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [event.organizer.email],
                html_message=html_message,
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send event creation notification: {e}")
    
    elif notification_type == 'updated':
        # Notify all attendees that event was updated
        attendees = RSVP.objects.filter(
            event=event,
            status='confirmed'
        ).select_related('user')
        
        for rsvp in attendees:
            try:
                context = {
                    'event': event,
                    'attendee': rsvp.user,
                    'rsvp': rsvp,
                    'domain': domain,
                    'changes': ['Event details have been updated'],
                }
                
                subject = f'Event Updated - {event.title}'
                html_message = render_to_string(
                    'notifications/emails/event_updated.html',
                    context
                )
                plain_message = render_to_string(
                    'notifications/emails/event_updated.txt',
                    context
                )
                
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [rsvp.user.email],
                    html_message=html_message,
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Failed to send update notification to {rsvp.user.email}: {e}")


def send_rsvp_notification(rsvp, notification_type):
    """
    Send RSVP-related notifications (created, cancelled)
    """
    domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')
    
    if notification_type == 'created':
        # Send confirmation to attendee
        try:
            context = {
                'rsvp': rsvp,
                'domain': domain,
            }
            
            subject = f'Registration Confirmed - {rsvp.event.title}'
            html_message = render_to_string(
                'notifications/emails/rsvp_confirmed.html',
                context
            )
            plain_message = render_to_string(
                'notifications/emails/rsvp_confirmed.txt',
                context
            )
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [rsvp.user.email],
                html_message=html_message,
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send RSVP confirmation: {e}")
    
    elif notification_type == 'cancelled':
        # Send cancellation notice
        try:
            context = {
                'rsvp': rsvp,
                'domain': domain,
                'refund_info': rsvp.event.ticket_price > 0,
            }
            
            subject = f'Registration Cancelled - {rsvp.event.title}'
            html_message = render_to_string(
                'notifications/emails/rsvp_cancelled.html',
                context
            )
            plain_message = render_to_string(
                'notifications/emails/rsvp_cancelled.txt',
                context
            )
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [rsvp.user.email],
                html_message=html_message,
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send cancellation notification: {e}")