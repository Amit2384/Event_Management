from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from .models import CheckIn
from .forms import CheckInForm
from rsvp.models import RSVP
from events.models import Event

@login_required
def checkin_dashboard(request, event_slug):
    """
    Check-in dashboard for event organizers.
    Shows check-in statistics and form.
    """
    event = get_object_or_404(Event, slug=event_slug)
    
    # Check if user is the organizer
    if event.organizer != request.user:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('events:event_detail', slug=event_slug)
    
    # Get statistics
    total_rsvps = RSVP.objects.filter(event=event).exclude(status='cancelled').count()
    checked_in = CheckIn.objects.filter(rsvp__event=event).count()
    pending_checkin = total_rsvps - checked_in
    
    # Recent check-ins
    recent_checkins = CheckIn.objects.filter(rsvp__event=event).select_related('rsvp__user')[:10]
    
    context = {
        'event': event,
        'total_rsvps': total_rsvps,
        'checked_in': checked_in,
        'pending_checkin': pending_checkin,
        'recent_checkins': recent_checkins,
        'title': f'Check-in - {event.title}'
    }
    return render(request, 'checkin/dashboard.html', context)

@login_required
def perform_checkin(request, event_slug):
    """
    Perform check-in for an attendee.
    Accepts ticket number or QR code data.
    """
    event = get_object_or_404(Event, slug=event_slug)
    
    # Check if user is the organizer
    if event.organizer != request.user:
        messages.error(request, 'You do not have permission to perform check-ins.')
        return redirect('events:event_detail', slug=event_slug)
    
    if request.method == 'POST':
        form = CheckInForm(request.POST)
        if form.is_valid():
            ticket_number = form.cleaned_data['ticket_number'].strip().upper()
            notes = form.cleaned_data.get('notes', '')
            
            # Extract ticket number from QR code data if necessary
            if 'TICKET:' in ticket_number:
                # QR code format: TICKET:XXX|EVENT:YYY|USER:ZZZ
                ticket_number = ticket_number.split('|')[0].replace('TICKET:', '')
            
            try:
                # Find RSVP
                rsvp = RSVP.objects.get(
                    ticket_number=ticket_number,
                    event=event
                )
                
                # Check if already checked in
                if hasattr(rsvp, 'checkin'):
                    messages.warning(
                        request, 
                        f'{rsvp.user.get_full_name()} has already been checked in at {rsvp.checkin.checked_in_at.strftime("%I:%M %p")}.'
                    )
                else:
                    # Perform check-in
                    checkin = CheckIn.objects.create(
                        rsvp=rsvp,
                        checked_in_by=request.user,
                        notes=notes
                    )
                    
                    # Update RSVP status
                    rsvp.mark_attended()
                    
                    messages.success(
                        request, 
                        f'Successfully checked in {rsvp.user.get_full_name()} ({rsvp.number_of_tickets} ticket(s)).'
                    )
                
                return redirect('checkin:checkin_dashboard', event_slug=event_slug)
                
            except RSVP.DoesNotExist:
                messages.error(request, 'Invalid ticket number or ticket not found for this event.')
        else:
            messages.error(request, 'Please enter a valid ticket number.')
    else:
        form = CheckInForm()
    
    context = {
        'form': form,
        'event': event,
        'title': f'Check-in - {event.title}'
    }
    return render(request, 'checkin/perform_checkin.html', context)

@login_required
def checkin_list(request, event_slug):
    """
    Display list of all check-ins for an event.
    Sortable and searchable.
    """
    event = get_object_or_404(Event, slug=event_slug)
    
    # Check if user is the organizer
    if event.organizer != request.user:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('events:event_detail', slug=event_slug)
    
    checkins = CheckIn.objects.filter(rsvp__event=event).select_related('rsvp__user', 'checked_in_by')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        checkins = checkins.filter(
            Q(rsvp__user__first_name__icontains=search_query) |
            Q(rsvp__user__last_name__icontains=search_query) |
            Q(rsvp__user__email__icontains=search_query) |
            Q(rsvp__ticket_number__icontains=search_query)
        )
    
    context = {
        'event': event,
        'checkins': checkins,
        'search_query': search_query,
        'title': f'Check-in List - {event.title}'
    }
    return render(request, 'checkin/checkin_list.html', context)

@login_required
def undo_checkin(request, checkin_id):
    """Undo a check-in (for corrections)"""
    checkin = get_object_or_404(CheckIn, id=checkin_id)
    event = checkin.rsvp.event
    
    # Check if user is the organizer
    if event.organizer != request.user:
        messages.error(request, 'You do not have permission to undo this check-in.')
        return redirect('events:event_detail', slug=event.slug)
    
    if request.method == 'POST':
        # Revert RSVP status
        checkin.rsvp.status = 'confirmed'
        checkin.rsvp.save()
        
        # Delete check-in record
        user_name = checkin.rsvp.user.get_full_name()
        checkin.delete()
        
        messages.success(request, f'Check-in for {user_name} has been undone.')
        return redirect('checkin:checkin_dashboard', event_slug=event.slug)
    
    context = {
        'checkin': checkin,
        'title': 'Undo Check-in'
    }
    return render(request, 'checkin/undo_checkin.html', context)