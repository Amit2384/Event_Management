from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.utils import timezone
import logging

# Set up logging
logger = logging.getLogger(__name__)

def get_from_email():
    """Get the from email address from settings or use default"""
    return getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@eventmanagement.com')

def send_html_email(subject, html_content, recipient_list):
    """
    Send HTML email with plain text fallback.
    
    Args:
        subject: Email subject
        html_content: HTML content for email
        recipient_list: List of recipient email addresses
    
    Returns:
        Boolean indicating success or failure
    """
    try:
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=get_from_email(),
            to=recipient_list
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send(fail_silently=False)
        
        logger.info(f"Email sent successfully to {len(recipient_list)} recipient(s): {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email '{subject}': {str(e)}")
        return False

def send_event_notification(event, action):
    """
    Send notification when event is created, updated, or cancelled.
    
    Args:
        event: Event object
        action: 'created', 'updated', or 'cancelled'
    
    Returns:
        Boolean indicating success or failure
    """
    # Prepare email based on action
    if action == 'created':
        subject = f"✅ Event Created: {event.title}"
        template_name = 'notifications/emails/event_created.html'
        
    elif action == 'updated':
        subject = f"🔔 Event Updated: {event.title}"
        template_name = 'notifications/emails/event_updated.html'
        
    elif action == 'cancelled':
        subject = f"❌ Event Cancelled: {event.title}"
        template_name = 'notifications/emails/event_cancelled.html'
        
        # If event is cancelled, notify all attendees
        from rsvp.models import RSVP
        attendees = RSVP.objects.filter(
            event=event
        ).exclude(status='cancelled').select_related('user')
        
        if attendees:
            send_event_cancellation_to_attendees(event, attendees)
    else:
        logger.warning(f"Unknown action '{action}' for event notification")
        return False
    
    # Create context for email template
    context = {
        'event': event,
        'organizer': event.organizer,
        'action': action,
        'event_url': f"{settings.SITE_URL}/events/{event.slug}/" if hasattr(settings, 'SITE_URL') else '',
    }
    
    # Render HTML email
    html_content = render_to_string(template_name, context)
    
    # Send to organizer
    return send_html_email(subject, html_content, [event.organizer.email])

def send_event_cancellation_to_attendees(event, attendees):
    """
    Send cancellation notification to all event attendees.
    
    Args:
        event: Event object
        attendees: QuerySet of RSVP objects
    """
    subject = f"❌ Event Cancelled: {event.title}"
    
    for rsvp in attendees:
        context = {
            'event': event,
            'user': rsvp.user,
            'rsvp': rsvp,
            'ticket_number': rsvp.ticket_number,
        }
        
        html_content = render_to_string(
            'notifications/emails/event_cancelled_attendee.html', 
            context
        )
        
        send_html_email(subject, html_content, [rsvp.user.email])
        
        # Update RSVP status
        rsvp.status = 'cancelled'
        rsvp.save()

def send_rsvp_notification(rsvp, action):
    """
    Send notification when RSVP is created, confirmed, or cancelled.
    
    Args:
        rsvp: RSVP object
        action: 'created', 'confirmed', or 'cancelled'
    
    Returns:
        Boolean indicating success or failure
    """
    event = rsvp.event
    user = rsvp.user
    
    # Notification to attendee
    if action == 'created' or action == 'confirmed':
        subject = f"🎉 Registration Confirmed: {event.title}"
        template_name = 'notifications/emails/rsvp_confirmed.html'
        
        context = {
            'event': event,
            'user': user,
            'rsvp': rsvp,
            'ticket_number': rsvp.ticket_number,
            'event_url': f"{settings.SITE_URL}/events/{event.slug}/" if hasattr(settings, 'SITE_URL') else '',
            'ticket_url': f"{settings.SITE_URL}/rsvp/{rsvp.id}/" if hasattr(settings, 'SITE_URL') else '',
        }
        
        html_content = render_to_string(template_name, context)
        attendee_email_sent = send_html_email(subject, html_content, [user.email])
        
        # Notification to organizer
        organizer_subject = f"🎟️ New Registration: {event.title}"
        organizer_context = {
            'event': event,
            'organizer': event.organizer,
            'attendee': user,
            'rsvp': rsvp,
            'remaining_seats': event.available_seats,
            'event_url': f"{settings.SITE_URL}/events/{event.slug}/" if hasattr(settings, 'SITE_URL') else '',
        }
        
        organizer_html = render_to_string(
            'notifications/emails/new_registration_organizer.html',
            organizer_context
        )
        
        organizer_email_sent = send_html_email(
            organizer_subject,
            organizer_html,
            [event.organizer.email]
        )
        
        return attendee_email_sent and organizer_email_sent
        
    elif action == 'cancelled':
        subject = f"🔄 Registration Cancelled: {event.title}"
        template_name = 'notifications/emails/rsvp_cancelled.html'
        
        context = {
            'event': event,
            'user': user,
            'rsvp': rsvp,
            'event_url': f"{settings.SITE_URL}/events/{event.slug}/" if hasattr(settings, 'SITE_URL') else '',
        }
        
        html_content = render_to_string(template_name, context)
        
        return send_html_email(subject, html_content, [user.email])
    
    else:
        logger.warning(f"Unknown action '{action}' for RSVP notification")
        return False

def send_event_reminder(rsvp, days_before=1):
    """
    Send reminder notification before event starts.
    Can be called via a scheduled task (e.g., Django-cron, Celery).
    
    Args:
        rsvp: RSVP object
        days_before: Number of days before event (default: 1)
    
    Returns:
        Boolean indicating success or failure
    """
    event = rsvp.event
    user = rsvp.user
    
    # Check if event is in the future
    if event.start_date <= timezone.now():
        logger.info(f"Event {event.title} has already started. Reminder not sent.")
        return False
    
    if days_before == 1:
        subject = f"⏰ Reminder: {event.title} is Tomorrow!"
    else:
        subject = f"⏰ Reminder: {event.title} in {days_before} Days"
    
    context = {
        'event': event,
        'user': user,
        'rsvp': rsvp,
        'days_before': days_before,
        'ticket_number': rsvp.ticket_number,
        'event_url': f"{settings.SITE_URL}/events/{event.slug}/" if hasattr(settings, 'SITE_URL') else '',
        'ticket_url': f"{settings.SITE_URL}/rsvp/{rsvp.id}/" if hasattr(settings, 'SITE_URL') else '',
    }
    
    html_content = render_to_string(
        'notifications/emails/event_reminder.html',
        context
    )
    
    return send_html_email(subject, html_content, [user.email])

def send_checkin_notification(checkin):
    """
    Send notification when attendee is checked in.
    
    Args:
        checkin: CheckIn object
    
    Returns:
        Boolean indicating success or failure
    """
    rsvp = checkin.rsvp
    event = rsvp.event
    user = rsvp.user
    
    subject = f"✅ Checked In: {event.title}"
    
    context = {
        'event': event,
        'user': user,
        'rsvp': rsvp,
        'checkin': checkin,
        'checkin_time': checkin.checked_in_at,
    }
    
    html_content = render_to_string(
        'notifications/emails/checkin_confirmation.html',
        context
    )
    
    return send_html_email(subject, html_content, [user.email])

def send_bulk_notification(event, subject, message, include_html=False):
    """
    Send bulk notification to all registered attendees of an event.
    
    Args:
        event: Event object
        subject: Email subject
        message: Email message (plain text or HTML if include_html=True)
        include_html: Boolean to indicate if message is HTML
    
    Returns:
        Dictionary with success and failure counts
    """
    from rsvp.models import RSVP
    
    # Get all confirmed attendees
    rsvps = RSVP.objects.filter(
        event=event,
        status__in=['confirmed', 'attended']
    ).select_related('user')
    
    if not rsvps.exists():
        logger.info(f"No recipients found for event {event.title}")
        return {'sent': 0, 'failed': 0}
    
    success_count = 0
    failure_count = 0
    
    for rsvp in rsvps:
        context = {
            'event': event,
            'user': rsvp.user,
            'rsvp': rsvp,
            'custom_message': message,
            'organizer': event.organizer,
        }
        
        if include_html:
            html_content = message
        else:
            # Use template with custom message
            html_content = render_to_string(
                'notifications/emails/bulk_notification.html',
                context
            )
        
        # Send to individual attendee
        if send_html_email(subject, html_content, [rsvp.user.email]):
            success_count += 1
        else:
            failure_count += 1
    
    logger.info(f"Bulk notification sent: {success_count} success, {failure_count} failed")
    
    return {
        'sent': success_count,
        'failed': failure_count,
        'total': rsvps.count()
    }

def send_ticket_email(rsvp):
    """
    Send email with ticket information and QR code.
    
    Args:
        rsvp: RSVP object
    
    Returns:
        Boolean indicating success or failure
    """
    event = rsvp.event
    user = rsvp.user
    
    subject = f"🎫 Your Ticket: {event.title}"
    
    context = {
        'event': event,
        'user': user,
        'rsvp': rsvp,
        'ticket_number': rsvp.ticket_number,
        'qr_code_url': rsvp.qr_code.url if rsvp.qr_code else None,
        'ticket_url': f"{settings.SITE_URL}/rsvp/{rsvp.id}/download-ticket/" if hasattr(settings, 'SITE_URL') else '',
    }
    
    html_content = render_to_string(
        'notifications/emails/ticket_email.html',
        context
    )
    
    return send_html_email(subject, html_content, [user.email])

def send_welcome_email(user):
    """
    Send welcome email to newly registered users.
    
    Args:
        user: User object
    
    Returns:
        Boolean indicating success or failure
    """
    subject = "👋 Welcome to Event Management System!"
    
    context = {
        'user': user,
        'dashboard_url': f"{settings.SITE_URL}/dashboard/" if hasattr(settings, 'SITE_URL') else '',
        'events_url': f"{settings.SITE_URL}/events/" if hasattr(settings, 'SITE_URL') else '',
    }
    
    html_content = render_to_string(
        'notifications/emails/welcome_email.html',
        context
    )
    
    return send_html_email(subject, html_content, [user.email])

def send_event_full_notification(event):
    """
    Send notification to organizer when event is fully booked.
    
    Args:
        event: Event object
    
    Returns:
        Boolean indicating success or failure
    """
    subject = f"🎉 Event Full: {event.title}"
    
    context = {
        'event': event,
        'organizer': event.organizer,
        'total_seats': event.total_seats,
        'event_url': f"{settings.SITE_URL}/events/{event.slug}/" if hasattr(settings, 'SITE_URL') else '',
    }
    
    html_content = render_to_string(
        'notifications/emails/event_full.html',
        context
    )
    
    return send_html_email(subject, html_content, [event.organizer.email])

def send_password_reset_email(user, reset_link):
    """
    Send password reset email (if implementing password reset).
    
    Args:
        user: User object
        reset_link: Password reset link
    
    Returns:
        Boolean indicating success or failure
    """
    subject = "🔐 Password Reset Request"
    
    context = {
        'user': user,
        'reset_link': reset_link,
    }
    
    html_content = render_to_string(
        'notifications/emails/password_reset.html',
        context
    )
    
    return send_html_email(subject, html_content, [user.email])

# Utility function to send reminders for all upcoming events
def send_all_event_reminders(days_before=1):
    """
    Send reminders for all events happening in specified days.
    Should be called by a scheduled task (cron job or Celery).
    
    Args:
        days_before: Number of days before event
    
    Returns:
        Dictionary with statistics
    """
    from rsvp.models import RSVP
    from datetime import timedelta
    
    # Calculate target date range
    target_start = timezone.now() + timedelta(days=days_before)
    target_end = target_start + timedelta(days=1)
    
    # Get all RSVPs for events in target date range
    rsvps = RSVP.objects.filter(
        event__start_date__gte=target_start,
        event__start_date__lt=target_end,
        status='confirmed'
    ).select_related('event', 'user')
    
    success_count = 0
    failure_count = 0
    
    for rsvp in rsvps:
        if send_event_reminder(rsvp, days_before):
            success_count += 1
        else:
            failure_count += 1
    
    logger.info(f"Event reminders sent: {success_count} success, {failure_count} failed")
    
    return {
        'sent': success_count,
        'failed': failure_count,
        'total': rsvps.count()
    }