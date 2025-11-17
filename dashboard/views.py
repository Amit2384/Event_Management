from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q, Sum
from datetime import timedelta
from events.models import Event
from rsvp.models import RSVP
from checkin.models import CheckIn

@login_required
def home(request):
    """
    Main dashboard showing overview and statistics.
    Different view for organizers and attendees.
    """
    user = request.user
    
    if user.profile.user_type == 'organizer':
        return organizer_dashboard(request)
    else:
        return attendee_dashboard(request)

@login_required
def organizer_dashboard(request):
    """
    Dashboard for event organizers with analytics.
    Shows event statistics, RSVPs, revenue, and recent activity.
    """
    user = request.user
    
    # Get organizer's events
    my_events = Event.objects.filter(organizer=user)
    
    # Event Statistics
    total_events = my_events.count()
    published_events = my_events.filter(status='published').count()
    draft_events = my_events.filter(status='draft').count()
    completed_events = my_events.filter(status='completed').count()
    
    # Upcoming events
    upcoming_events = my_events.filter(
        status='published',
        start_date__gte=timezone.now()
    ).order_by('start_date')[:5]
    
    # Recent events
    recent_events = my_events.filter(
        status='published'
    ).order_by('-created_at')[:5]
    
    # RSVP Statistics
    total_rsvps = RSVP.objects.filter(
        event__organizer=user
    ).exclude(status='cancelled').count()
    
    confirmed_rsvps = RSVP.objects.filter(
        event__organizer=user,
        status='confirmed'
    ).count()
    
    attended_rsvps = RSVP.objects.filter(
        event__organizer=user,
        status='attended'
    ).count()
    
    # Total tickets sold
    total_tickets = RSVP.objects.filter(
        event__organizer=user
    ).exclude(status='cancelled').aggregate(
        total=Sum('number_of_tickets')
    )['total'] or 0
    
    # Revenue calculation (for paid events)
    total_revenue = 0
    paid_events = my_events.filter(event_type='paid')
    for event in paid_events:
        event_rsvps = RSVP.objects.filter(
            event=event
        ).exclude(status='cancelled')
        event_tickets = sum(rsvp.number_of_tickets for rsvp in event_rsvps)
        total_revenue += event_tickets * float(event.ticket_price)
    
    # Check-in Statistics
    total_checkins = CheckIn.objects.filter(
        rsvp__event__organizer=user
    ).count()
    
    # Recent RSVPs
    recent_rsvps = RSVP.objects.filter(
        event__organizer=user
    ).exclude(status='cancelled').select_related(
        'event', 'user'
    ).order_by('-created_at')[:10]
    
    # Monthly event stats (last 6 months)
    monthly_stats = []
    for i in range(5, -1, -1):
        month_start = timezone.now() - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        
        events_count = my_events.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        
        rsvps_count = RSVP.objects.filter(
            event__organizer=user,
            created_at__gte=month_start,
            created_at__lt=month_end
        ).exclude(status='cancelled').count()
        
        monthly_stats.append({
            'month': month_start.strftime('%b %Y'),
            'events': events_count,
            'rsvps': rsvps_count
        })
    
    context = {
        'user_type': 'organizer',
        'total_events': total_events,
        'published_events': published_events,
        'draft_events': draft_events,
        'completed_events': completed_events,
        'upcoming_events': upcoming_events,
        'recent_events': recent_events,
        'total_rsvps': total_rsvps,
        'confirmed_rsvps': confirmed_rsvps,
        'attended_rsvps': attended_rsvps,
        'total_tickets': total_tickets,
        'total_revenue': total_revenue,
        'total_checkins': total_checkins,
        'recent_rsvps': recent_rsvps,
        'monthly_stats': monthly_stats,
        'title': 'Organizer Dashboard'
    }
    return render(request, 'dashboard/organizer_dashboard.html', context)

@login_required
def attendee_dashboard(request):
    """
    Dashboard for attendees.
    Shows registered events, upcoming events, and recommendations.
    """
    user = request.user
    
    # Get user's RSVPs
    my_rsvps = RSVP.objects.filter(user=user).select_related('event')
    
    # Upcoming registered events
    upcoming_registered = my_rsvps.filter(
        status__in=['confirmed', 'pending'],
        event__start_date__gte=timezone.now()
    ).order_by('event__start_date')[:5]
    
    # Past attended events
    past_attended = my_rsvps.filter(
        status='attended'
    ).order_by('-event__start_date')[:5]
    
    # Statistics
    total_registered = my_rsvps.exclude(status='cancelled').count()
    total_attended = my_rsvps.filter(status='attended').count()
    upcoming_count = upcoming_registered.count()
    
    # Available upcoming events (not registered)
    registered_event_ids = my_rsvps.values_list('event_id', flat=True)
    available_events = Event.objects.filter(
        status='published',
        start_date__gte=timezone.now()
    ).exclude(
        id__in=registered_event_ids
    ).order_by('start_date')[:6]
    
    # Recommended events (all available events)
    recommended_events = available_events[:4]
    
    # Recent activity
    recent_activity = my_rsvps.order_by('-created_at')[:5]
    
    context = {
        'user_type': 'attendee',
        'upcoming_registered': upcoming_registered,
        'past_attended': past_attended,
        'total_registered': total_registered,
        'total_attended': total_attended,
        'upcoming_count': upcoming_count,
        'available_events': available_events,
        'recommended_events': recommended_events,
        'recent_activity': recent_activity,
        'title': 'My Dashboard'
    }
    return render(request, 'dashboard/attendee_dashboard.html', context)

@login_required
def analytics(request):
    """
    Detailed analytics page for organizers.
    Shows comprehensive statistics and charts data.
    """
    user = request.user
    
    # Only for organizers
    if user.profile.user_type != 'organizer':
        from django.contrib import messages
        messages.error(request, 'Access denied. This page is only for organizers.')
        return redirect('dashboard:home')
    
    my_events = Event.objects.filter(organizer=user)
    
    # Overall Statistics
    total_events = my_events.count()
    total_views = 0  # Can be implemented with a view tracking system
    
    # RSVP trends
    rsvp_data = RSVP.objects.filter(
        event__organizer=user
    ).exclude(status='cancelled')
    
    # Attendance rate
    total_confirmed = rsvp_data.filter(status='confirmed').count()
    total_attended = rsvp_data.filter(status='attended').count()
    attendance_rate = (total_attended / total_confirmed * 100) if total_confirmed > 0 else 0
    
    # Event performance (top events by RSVPs)
    top_events = my_events.annotate(
        rsvp_count=Count('rsvps', filter=Q(rsvps__status__in=['confirmed', 'attended']))
    ).order_by('-rsvp_count')[:5]
    
    # Monthly trends (last 12 months)
    monthly_trends = []
    for i in range(11, -1, -1):
        month_start = timezone.now() - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        
        month_data = {
            'month': month_start.strftime('%b'),
            'events': my_events.filter(
                start_date__gte=month_start,
                start_date__lt=month_end
            ).count(),
            'rsvps': RSVP.objects.filter(
                event__organizer=user,
                created_at__gte=month_start,
                created_at__lt=month_end
            ).exclude(status='cancelled').count(),
            'checkins': CheckIn.objects.filter(
                rsvp__event__organizer=user,
                checked_in_at__gte=month_start,
                checked_in_at__lt=month_end
            ).count()
        }
        monthly_trends.append(month_data)
    
    # Revenue by event type
    free_events = my_events.filter(event_type='free').count()
    paid_events = my_events.filter(event_type='paid').count()
    
    # Location statistics
    location_stats = my_events.values('city').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    context = {
        'total_events': total_events,
        'attendance_rate': round(attendance_rate, 2),
        'top_events': top_events,
        'monthly_trends': monthly_trends,
        'free_events': free_events,
        'paid_events': paid_events,
        'location_stats': location_stats,
        'title': 'Analytics Dashboard'
    }
    return render(request, 'dashboard/analytics.html', context)