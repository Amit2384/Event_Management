from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Event
from .forms import EventForm

def event_list(request):
    """
    Display list of all published events.
    Includes pagination and basic filtering.
    """
    events = Event.objects.filter(status='published').select_related('organizer')
    
    # Filter by category if specified
    # category_id = request.GET.get('category')
    # if category_id:
    #     events = events.filter(category_id=category_id)
    
    # Pagination
    paginator = Paginator(events, 9)  # Show 9 events per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        # 'categories': categories,
        # 'selected_category': category_id,
        'title': 'All Events'
    }
    return render(request, 'events/event_list.html', context)

def event_detail(request, slug):
    """
    Display detailed information about a specific event.
    Shows event details, organizer info, and RSVP status.
    """
    event = get_object_or_404(
        Event.objects.select_related('organizer', 'organizer__profile'),
        slug=slug
    )
    
    # Check if user has RSVP'd to this event
    user_rsvp = None
    if request.user.is_authenticated:
        from rsvp.models import RSVP
        user_rsvp = RSVP.objects.filter(event=event, user=request.user).first()
    
    context = {
        'event': event,
        'user_rsvp': user_rsvp,
        'title': event.title
    }
    return render(request, 'events/event_detail.html', context)

@login_required
def event_create(request):
    """
    Create a new event.
    Only accessible to logged-in users (preferably organizers).
    """
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            messages.success(request, f'Event "{event.title}" created successfully!')
            
            # Send notification (will be handled by notifications module)
            from notifications.utils import send_event_notification
            send_event_notification(event, 'created')
            
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
        messages.error(request, 'You do not have permission to edit this event.')
        return redirect('events:event_detail', slug=slug)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save()
            messages.success(request, f'Event "{event.title}" updated successfully!')
            
            # Send notification about update
            from notifications.utils import send_event_notification
            send_event_notification(event, 'updated')
            
            return redirect('events:event_detail', slug=event.slug)
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
        messages.error(request, 'You do not have permission to delete this event.')
        return redirect('events:event_detail', slug=slug)
    
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f'Event "{event_title}" deleted successfully!')
        return redirect('events:event_list')
    
    context = {
        'event': event,
        'title': f'Delete {event.title}'
    }
    return render(request, 'events/event_confirm_delete.html', context)

@login_required
def my_events(request):
    """
    Display events organized by the current user.
    Shows all events regardless of status.
    """
    events = Event.objects.filter(organizer=request.user)
    
    # Pagination
    paginator = Paginator(events, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'title': 'My Events'
    }
    return render(request, 'events/my_events.html', context)

# def category_list(request):
#     """Display all event categories"""
#     categories = Category.objects.all()
    
#     context = {
#         'categories': categories,
#         'title': 'Event Categories'
#     }
#     return render(request, 'events/category_list.html', context)