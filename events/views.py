from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Q, Count
from django.utils import timezone
from .models import Event
from .forms import EventForm
from rsvp.models import RSVP


def event_list(request):
    """
    Display list of all published events.
    Includes pagination and search/filtering.
    """
    events = Event.objects.filter(
        status='published'
    ).select_related('organizer').order_by('start_date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(city__icontains=search_query)
        )
    
    # Filter by event type
    event_type = request.GET.get('type', '')
    if event_type in ['free', 'paid']:
        events = events.filter(event_type=event_type)
    
    # Filter by city
    city = request.GET.get('city', '')
    if city:
        events = events.filter(city__iexact=city)
    
    # Filter upcoming/past events
    filter_time = request.GET.get('filter', '')
    if filter_time == 'upcoming':
        events = events.filter(start_date__gte=timezone.now())
    elif filter_time == 'past':
        events = events.filter(end_date__lt=timezone.now())
    
    # Get unique cities for filter dropdown
    cities = Event.objects.filter(
        status='published'
    ).values_list('city', flat=True).distinct().order_by('city')
    
    # Pagination
    paginator = Paginator(events, 9)  # Show 9 events per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'title': 'All Events',
        'search_query': search_query,
        'selected_type': event_type,
        'selected_city': city,
        'cities': cities,
        'filter_time': filter_time,
    }
    return render(request, 'events/event_list.html', context)


def event_detail(request, slug):
    """
    Display detailed information about a specific event.
    Shows event details, organizer info, and RSVP status.
    """
    event = get_object_or_404(
        Event.objects.select_related('organizer'),
        slug=slug
    )
    
    # Check if user has RSVP'd to this event
    user_rsvp = None
    if request.user.is_authenticated:
        user_rsvp = RSVP.objects.filter(
            event=event, 
            user=request.user  # ✅ Changed from attendee to user
        ).first()
    
    # Check if event is full
    is_full = event.available_seats <= 0
    
    # Get registration count
    registration_count = RSVP.objects.filter(
        event=event,
        status='confirmed'  # ✅ Changed from payment_status to status
    ).count()
    
    context = {
        'event': event,
        'user_rsvp': user_rsvp,
        'is_full': is_full,
        'registration_count': registration_count,
        'title': event.title
    }
    return render(request, 'events/event_detail.html', context)


@login_required
def event_create(request):
    """
    Create a new event.
    Only accessible to logged-in users.
    """
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            
            messages.success(
                request, 
                f'Event "{event.title}" created successfully!'
            )
            
            # Send notification email (optional - fails silently)
            try:
                send_event_created_notification(event, request)
            except Exception as e:
                print(f"Failed to send event creation notification: {e}")
            
            return redirect('events:event_detail', slug=event.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EventForm()
    
    context = {
        'form': form,
        'title': 'Create Event',
        'button_text': 'Create Event'
    }
    return render(request, 'events/event_form.html', context)


@login_required
def event_update(request, slug):
    """
    Update an existing event.
    Only the event organizer can update their events.
    """
    event = get_object_or_404(Event, slug=slug)
    
    # Check if user is the organizer
    if event.organizer != request.user:
        messages.error(
            request, 
            'You do not have permission to edit this event.'
        )
        return redirect('events:event_detail', slug=slug)
    
    # Store original values to detect changes
    original_data = {
        'start_date': event.start_date,
        'venue_name': event.venue_name,
        'ticket_price': event.ticket_price,
    }
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            updated_event = form.save()
            
            messages.success(
                request, 
                f'Event "{updated_event.title}" updated successfully!'
            )
            
            # Notify attendees about update (optional - fails silently)
            try:
                # Detect changes
                changes = []
                if updated_event.start_date != original_data['start_date']:
                    changes.append(
                        f"Date/Time changed to {updated_event.start_date.strftime('%B %d, %Y at %I:%M %p')}"
                    )
                if updated_event.venue_name != original_data['venue_name']:
                    changes.append(f"Venue changed to {updated_event.venue_name}")
                if updated_event.ticket_price != original_data['ticket_price']:
                    changes.append(f"Price changed to ${updated_event.ticket_price}")
                
                if changes:
                    send_event_updated_notification(updated_event, changes, request)
            except Exception as e:
                print(f"Failed to send event update notification: {e}")
            
            return redirect('events:event_detail', slug=updated_event.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EventForm(instance=event)
    
    context = {
        'form': form,
        'event': event,
        'title': f'Edit {event.title}',
        'button_text': 'Update Event'
    }
    return render(request, 'events/event_form.html', context)


@login_required
def event_delete(request, slug):
    """
    Delete an event.
    Only the event organizer can delete their events.
    """
    event = get_object_or_404(Event, slug=slug)
    
    # Check if user is the organizer
    if event.organizer != request.user:
        messages.error(
            request, 
            'You do not have permission to delete this event.'
        )
        return redirect('events:event_detail', slug=slug)
    
    if request.method == 'POST':
        event_title = event.title
        
        # Check if event has registrations
        registration_count = RSVP.objects.filter(event=event).count()
        if registration_count > 0:
            messages.warning(
                request,
                f'Warning: This event has {registration_count} registration(s). '
                'Consider canceling it instead of deleting.'
            )
        
        event.delete()
        messages.success(request, f'Event "{event_title}" deleted successfully!')
        
        # ✅ Fixed redirect - use one of these options:
        return redirect('events:my_events')  # Option 1: Go to My Events
        # return redirect('dashboard:home')  # Option 2: Go to Dashboard
        # return redirect('events:event_list')  # Option 3: Go to All Events
    
    # Get registration count for confirmation page
    registration_count = RSVP.objects.filter(event=event).count()
    
    context = {
        'event': event,
        'registration_count': registration_count,
        'title': f'Delete {event.title}'
    }
    return render(request, 'events/event_confirm_delete.html', context)

@login_required
def my_events(request):
    """
    Display events organized by the current user.
    Shows all events regardless of status.
    """
    events = Event.objects.filter(
        organizer=request.user
    ).annotate(
        registration_count=Count('rsvps')
    ).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        events = events.filter(status=status_filter)
    
    # Statistics
    total_events = events.count()
    published_events = Event.objects.filter(
        organizer=request.user, 
        status='published'
    ).count()
    draft_events = Event.objects.filter(
        organizer=request.user, 
        status='draft'
    ).count()
    
    # Pagination
    paginator = Paginator(events, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_events': total_events,
        'published_events': published_events,
        'draft_events': draft_events,
        'status_filter': status_filter,
        'title': 'My Events'
    }
    return render(request, 'events/my_events.html', context)


# Helper Functions for Email Notifications

def send_event_created_notification(event, request):
    """Send notification when event is created"""
    try:
        context = {
            'event': event,
            'domain': request.get_host(),
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
        print(f"Error sending event created notification: {e}")


def send_event_updated_notification(event, changes, request):
    """Send notification to attendees when event is updated"""
    try:
        # Get all confirmed attendees
        confirmed_rsvps = RSVP.objects.filter(
            event=event,
            status='confirmed'  # ✅ Changed from payment_status to status
        ).select_related('user')  # ✅ Changed from attendee to user
        
        for rsvp in confirmed_rsvps:
            try:
                context = {
                    'event': event,
                    'attendee': rsvp.user,  # ✅ Changed from rsvp.attendee to rsvp.user
                    'changes': changes,
                    'domain': request.get_host(),
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
                    [rsvp.user.email],  # ✅ Changed from rsvp.attendee.email
                    html_message=html_message,
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Failed to notify {rsvp.user.email}: {e}")
                
    except Exception as e:
        print(f"Error sending event update notifications: {e}")