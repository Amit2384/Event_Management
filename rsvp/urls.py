from django.urls import path
from . import views
from django.utils import timezone

app_name = 'rsvp'

urlpatterns = [
    path('event/<slug:event_slug>/register/', views.create_rsvp, name='create_rsvp'),
    path('my-registrations/', views.my_rsvps, name='my_rsvps'),
    path('<int:rsvp_id>/', views.rsvp_detail, name='rsvp_detail'),
    path('<int:rsvp_id>/cancel/', views.cancel_rsvp, name='cancel_rsvp'),
    path('<int:rsvp_id>/download-ticket/', views.download_ticket, name='download_ticket'),
    path('event/<slug:event_slug>/attendees/', views.event_attendees, name='event_attendees'),
]