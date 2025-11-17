from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from .models import RSVP
from .forms import RSVPForm
from events.models import Event
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from io import BytesIO
import os

@login_required
def create_rsvp(request, event_slug):
    """
    Create RSVP for an event.
    Generates ticket with QR code automatically.
    Validates availability and user eligibility.
    """
    event = get_object_or_404(Event, slug=event_slug, status='published')
    
    # Check if user already has RSVP for this event
    existing_rsvp = RSVP.objects.filter(event=event, user=request.user).first()
    if existing_rsvp and existing_rsvp.status != 'cancelled':
        messages.warning(request, 'You have already registered for this event.')
        return redirect('rsvp:my_rsvps')
    
    # Check if event is full
    if event.is_full():
        messages.error(request, 'Sorry, this event is fully booked.')
        return redirect('events:event_detail', slug=event_slug)
    
    # Check if event has already started
    if event.start_date < timezone.now():
        messages.error(request, 'Registration is closed. This event has already started.')
        return redirect('events:event_detail', slug=event_slug)
    
    if request.method == 'POST':
        form = RSVPForm(request.POST, event=event)
        if form.is_valid():
            rsvp = form.save(commit=False)
            rsvp.event = event
            rsvp.user = request.user
            rsvp.status = 'confirmed'
            
            # Check availability one more time
            if rsvp.number_of_tickets > event.available_seats:
                messages.error(request, f'Only {event.available_seats} seats remaining.')
                return redirect('events:event_detail', slug=event_slug)
            
            # Update available seats
            event.available_seats -= rsvp.number_of_tickets
            event.save()
            
            # Confirm RSVP
            rsvp.save()
            rsvp.confirm()
            
            messages.success(
                request, 
                f'Successfully registered for {event.title}! Your ticket number is {rsvp.ticket_number}.'
            )
            
            # Send confirmation notification
            from notifications.utils import send_rsvp_notification
            send_rsvp_notification(rsvp, 'created')
            
            return redirect('rsvp:rsvp_detail', rsvp_id=rsvp.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RSVPForm(event=event)
    
    context = {
        'form': form,
        'event': event,
        'title': f'Register for {event.title}'
    }
    return render(request, 'rsvp/rsvp_form.html', context)

@login_required
def rsvp_detail(request, rsvp_id):
    """
    Display RSVP details and ticket information.
    Shows ticket number, QR code, and event details.
    """
    rsvp = get_object_or_404(RSVP, id=rsvp_id, user=request.user)
    
    context = {
        'rsvp': rsvp,
        'title': 'Your Ticket'
    }
    return render(request, 'rsvp/rsvp_detail.html', context)

@login_required
def my_rsvps(request):
    """
    Display all RSVPs for current user.
    Organized by upcoming, past, and cancelled events.
    """
    rsvps = RSVP.objects.filter(user=request.user).select_related('event') #, 'event__category'
    
    # Current time
    now = timezone.now()
    
    # Separate by status and date
    upcoming_rsvps = rsvps.filter(
        status__in=['confirmed', 'pending'], 
        event__start_date__gte=now
    ).order_by('event__start_date')
    
    past_rsvps = rsvps.filter(
        event__end_date__lt=now
    ).exclude(status='cancelled').order_by('-event__start_date')
    
    cancelled_rsvps = rsvps.filter(status='cancelled').order_by('-created_at')
    
    # Count statistics
    total_attended = rsvps.filter(status='attended').count()
    total_upcoming = upcoming_rsvps.count()
    
    context = {
        'upcoming_rsvps': upcoming_rsvps,
        'past_rsvps': past_rsvps,
        'cancelled_rsvps': cancelled_rsvps,
        'total_attended': total_attended,
        'total_upcoming': total_upcoming,
        'title': 'My Registrations'
    }
    return render(request, 'rsvp/my_rsvps.html', context)

@login_required
def cancel_rsvp(request, rsvp_id):
    """
    Cancel an RSVP.
    Restores seats to event availability.
    """
    rsvp = get_object_or_404(RSVP, id=rsvp_id, user=request.user)
    
    # Check if already cancelled
    if rsvp.status == 'cancelled':
        messages.warning(request, 'This registration is already cancelled.')
        return redirect('rsvp:my_rsvps')
    
    # Check if event has already started
    if rsvp.event.start_date < timezone.now():
        messages.error(request, 'Cannot cancel registration. The event has already started.')
        return redirect('rsvp:my_rsvps')
    
    # Check if already attended
    if rsvp.status == 'attended':
        messages.error(request, 'Cannot cancel registration. You have already attended this event.')
        return redirect('rsvp:my_rsvps')
    
    if request.method == 'POST':
        # Cancel the RSVP
        rsvp.cancel()
        
        messages.success(
            request, 
            f'Your registration for {rsvp.event.title} has been cancelled. {rsvp.number_of_tickets} seat(s) have been released.'
        )
        
        # Send cancellation notification
        from notifications.utils import send_rsvp_notification
        send_rsvp_notification(rsvp, 'cancelled')
        
        return redirect('rsvp:my_rsvps')
    
    context = {
        'rsvp': rsvp,
        'title': 'Cancel Registration'
    }
    return render(request, 'rsvp/rsvp_cancel.html', context)

@login_required
def download_ticket(request, rsvp_id):
    """
    Generate and download PDF ticket with QR code.
    This is the main ticket generation functionality.
    Creates a professional PDF ticket with all event details.
    """
    rsvp = get_object_or_404(RSVP, id=rsvp_id, user=request.user)
    
    # Check if RSVP is active
    if rsvp.status == 'cancelled':
        messages.error(request, 'Cannot download ticket for cancelled registration.')
        return redirect('rsvp:my_rsvps')
    
    # Create PDF in memory
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Draw border
    p.setStrokeColorRGB(0.2, 0.2, 0.2)
    p.setLineWidth(2)
    p.rect(50, 50, width - 100, height - 100, stroke=1, fill=0)
    
    # Header - Title
    p.setFillColorRGB(0.2, 0.4, 0.8)
    p.rect(50, height - 150, width - 100, 50, stroke=0, fill=1)
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 28)
    p.drawCentredString(width / 2, height - 130, "EVENT TICKET")
    
    # Ticket Number (prominent)
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(80, height - 180, f"Ticket #: {rsvp.ticket_number}")
    
    # Status badge
    if rsvp.status == 'confirmed':
        status_color = (0, 0.7, 0)
        status_text = "CONFIRMED"
    elif rsvp.status == 'attended':
        status_color = (0.2, 0.6, 0.2)
        status_text = "ATTENDED"
    else:
        status_color = (0.8, 0.6, 0)
        status_text = rsvp.status.upper()
    
    p.setFillColorRGB(*status_color)
    p.setFont("Helvetica-Bold", 14)
    p.drawRightString(width - 80, height - 180, status_text)
    
    # Event Details Section
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(80, height - 230, "Event Details")
    
    # Draw line under section header
    p.setStrokeColorRGB(0.7, 0.7, 0.7)
    p.setLineWidth(1)
    p.line(80, height - 235, width - 80, height - 235)
    
    p.setFont("Helvetica-Bold", 13)
    y_position = height - 260
    
    # Event Name
    p.drawString(80, y_position, "Event:")
    p.setFont("Helvetica", 12)
    p.drawString(180, y_position, rsvp.event.title)
    
    # Date
    y_position -= 25
    p.setFont("Helvetica-Bold", 13)
    p.drawString(80, y_position, "Date:")
    p.setFont("Helvetica", 12)
    p.drawString(180, y_position, rsvp.event.start_date.strftime('%B %d, %Y'))
    
    # Time
    y_position -= 25
    p.setFont("Helvetica-Bold", 13)
    p.drawString(80, y_position, "Time:")
    p.setFont("Helvetica", 12)
    time_str = f"{rsvp.event.start_date.strftime('%I:%M %p')} - {rsvp.event.end_date.strftime('%I:%M %p')}"
    p.drawString(180, y_position, time_str)
    
    # Venue
    y_position -= 25
    p.setFont("Helvetica-Bold", 13)
    p.drawString(80, y_position, "Venue:")
    p.setFont("Helvetica", 12)
    p.drawString(180, y_position, rsvp.event.venue_name)
    
    # Address
    y_position -= 25
    p.setFont("Helvetica-Bold", 13)
    p.drawString(80, y_position, "Address:")
    p.setFont("Helvetica", 11)
    p.drawString(180, y_position, rsvp.event.venue_address)
    
    # City
    y_position -= 20
    p.drawString(180, y_position, f"{rsvp.event.city}, {rsvp.event.state}, {rsvp.event.country}")
    
    # Attendee Details Section
    y_position -= 50
    p.setFont("Helvetica-Bold", 16)
    p.drawString(80, y_position, "Attendee Details")
    
    # Draw line
    p.line(80, y_position - 5, width - 80, y_position - 5)
    
    y_position -= 30
    p.setFont("Helvetica-Bold", 13)
    p.drawString(80, y_position, "Name:")
    p.setFont("Helvetica", 12)
    full_name = rsvp.user.get_full_name() or rsvp.user.username
    p.drawString(180, y_position, full_name)
    
    # Email
    y_position -= 25
    p.setFont("Helvetica-Bold", 13)
    p.drawString(80, y_position, "Email:")
    p.setFont("Helvetica", 12)
    p.drawString(180, y_position, rsvp.user.email)
    
    # Number of Tickets
    y_position -= 25
    p.setFont("Helvetica-Bold", 13)
    p.drawString(80, y_position, "Tickets:")
    p.setFont("Helvetica", 12)
    p.drawString(180, y_position, str(rsvp.number_of_tickets))
    
    # QR Code Section
    if rsvp.qr_code and os.path.exists(rsvp.qr_code.path):
        try:
            qr_image = ImageReader(rsvp.qr_code.path)
            
            # QR Code box
            qr_x = width - 220
            qr_y = 150
            qr_size = 150
            
            # Draw QR code background
            p.setFillColorRGB(0.95, 0.95, 0.95)
            p.rect(qr_x - 10, qr_y - 10, qr_size + 20, qr_size + 20, stroke=1, fill=1)
            
            # Draw QR code
            p.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)
            
            # QR Code instructions
            p.setFillColorRGB(0, 0, 0)
            p.setFont("Helvetica-Bold", 10)
            p.drawCentredString(qr_x + qr_size/2, qr_y - 25, "SCAN FOR CHECK-IN")
        except Exception as e:
            # If QR code cannot be loaded, show message
            p.setFont("Helvetica", 10)
            p.drawString(width - 220, 200, "QR Code unavailable")
    
    # Important Notes Section
    y_position = 120
    p.setFont("Helvetica-Bold", 12)
    p.drawString(80, y_position, "Important Notes:")
    
    y_position -= 20
    p.setFont("Helvetica", 9)
    p.drawString(80, y_position, "• Please bring this ticket (printed or digital) to the event")
    
    y_position -= 15
    p.drawString(80, y_position, "• Arrive 15 minutes early for check-in")
    
    y_position -= 15
    p.drawString(80, y_position, "• This ticket is non-transferable")
    
    y_position -= 15
    p.drawString(80, y_position, f"• Event Type: {rsvp.event.get_event_type_display()}")
    
    if rsvp.event.event_type == 'paid':
        y_position -= 15
        p.drawString(80, y_position, f"• Ticket Price: ${rsvp.event.ticket_price} per ticket")
    
    # Footer
    p.setFont("Helvetica-Italic", 8)
    p.setFillColorRGB(0.5, 0.5, 0.5)
    p.drawCentredString(
        width / 2, 
        70, 
        f"Generated on {timezone.now().strftime('%B %d, %Y at %I:%M %p')}"
    )
    p.drawCentredString(width / 2, 60, "Event Management System")
    
    # Finalize PDF
    p.showPage()
    p.save()
    
    # Get PDF content
    buffer.seek(0)
    
    # Create HTTP response
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"ticket_{rsvp.ticket_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
def event_attendees(request, event_slug):
    """
    Display list of attendees for an event.
    Only accessible by event organizer.
    Shows all confirmed registrations.
    """
    event = get_object_or_404(Event, slug=event_slug)
    
    # Check if user is the organizer
    if event.organizer != request.user:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('events:event_detail', slug=event_slug)
    
    # Get all RSVPs except cancelled
    rsvps = RSVP.objects.filter(
        event=event
    ).exclude(
        status='cancelled'
    ).select_related(
        'user', 'user__profile'
    ).order_by('-created_at')
    
    # Calculate statistics
    total_attendees = rsvps.count()
    total_tickets = sum(rsvp.number_of_tickets for rsvp in rsvps)
    confirmed_count = rsvps.filter(status='confirmed').count()
    attended_count = rsvps.filter(status='attended').count()
    pending_count = rsvps.filter(status='pending').count()
    
    # Calculate revenue for paid events
    total_revenue = 0
    if event.event_type == 'paid':
        total_revenue = sum(
            rsvp.number_of_tickets * float(event.ticket_price) 
            for rsvp in rsvps
        )
    
    context = {
        'event': event,
        'rsvps': rsvps,
        'total_attendees': total_attendees,
        'total_tickets': total_tickets,
        'confirmed_count': confirmed_count,
        'attended_count': attended_count,
        'pending_count': pending_count,
        'total_revenue': total_revenue,
        'title': f'Attendees - {event.title}'
    }
    return render(request, 'rsvp/event_attendees.html', context)