from django.shortcuts import render
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from events.models import Event #, Category

def search_events(request):
    """
    Advanced search functionality for events.
    Supports keyword search, filters, and sorting.
    """
    # Get search parameters
    query = request.GET.get('q', '').strip()
    # category_id = request.GET.get('category', '')
    event_type = request.GET.get('type', '')
    city = request.GET.get('city', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    sort_by = request.GET.get('sort', 'date')
    status = request.GET.get('status', 'upcoming')
    
    # Base queryset - only published events
    events = Event.objects.filter(status='published').select_related('organizer') #.select_related('category', 'organizer')
    
    # Keyword search
    if query:
        events = events.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(venue_name__icontains=query) |
            Q(city__icontains=query) |
            Q(organizer__first_name__icontains=query) |
            Q(organizer__last_name__icontains=query)
        )
    
    # Filter by category
    # if category_id:
    #     events = events.filter(category_id=category_id)
    
    # Filter by event type
    if event_type:
        events = events.filter(event_type=event_type)
    
    # Filter by city
    if city:
        events = events.filter(city__icontains=city)
    
    # Filter by date range
    if date_from:
        events = events.filter(start_date__gte=date_from)
    
    if date_to:
        events = events.filter(start_date__lte=date_to)
    
    # Filter by status (upcoming/past)
    now = timezone.now()
    if status == 'upcoming':
        events = events.filter(start_date__gte=now)
    elif status == 'past':
        events = events.filter(end_date__lt=now)
    
    # Sorting
    if sort_by == 'date':
        events = events.order_by('start_date')
    elif sort_by == 'date_desc':
        events = events.order_by('-start_date')
    elif sort_by == 'title':
        events = events.order_by('title')
    elif sort_by == 'popular':
        events = events.annotate(
            rsvp_count=Count('rsvps')
        ).order_by('-rsvp_count')
    elif sort_by == 'price_low':
        events = events.order_by('ticket_price')
    elif sort_by == 'price_high':
        events = events.order_by('-ticket_price')
    
    # Get all categories for filter dropdown
    # categories = Category.objects.all()
    
    # Get unique cities for filter dropdown
    cities = Event.objects.filter(
        status='published'
    ).values_list('city', flat=True).distinct().order_by('city')
    
    # Pagination
    paginator = Paginator(events, 12)  # 12 events per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Search statistics
    total_results = events.count()
    
    context = {
        'page_obj': page_obj,
        'query': query,
        # 'categories': categories,
        'cities': cities,
        # 'selected_category': category_id,
        'selected_type': event_type,
        'selected_city': city,
        'selected_status': status,
        'date_from': date_from,
        'date_to': date_to,
        'sort_by': sort_by,
        'total_results': total_results,
        'title': 'Search Events'
    }
    return render(request, 'search/search_results.html', context)

# def filter_by_category(request, category_id):
#     """Filter events by specific category"""
#     category = get_object_or_404(Category, id=category_id)
#     
#     events = Event.objects.filter(
#         category=category,
#         status='published',
#         start_date__gte=timezone.now()
#     ).select_related('organizer').order_by('start_date')
#     
#     # Pagination
#     paginator = Paginator(events, 12)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#     
#     context = {
#         'page_obj': page_obj,
#         'category': category,
#         'total_results': events.count(),
#         'title': f'{category.name} Events'
#     }
#     return render(request, 'search/category_events.html', context)

def advanced_search(request):
    """Display advanced search form with all filter options"""
    # categories = Category.objects.all()
    cities = Event.objects.filter(
        status='published'
    ).values_list('city', flat=True).distinct().order_by('city')
    
    context = {
        # 'categories': categories,
        'cities': cities,
        'title': 'Advanced Search'
    }
    return render(request, 'search/advanced_search.html', context)