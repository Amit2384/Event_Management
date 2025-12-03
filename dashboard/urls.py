from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('organizer/', views.organizer_dashboard, name='organizer_dashboard'),
    path('attendee/', views.attendee_dashboard, name='attendee_dashboard'),
    path('analytics/', views.analytics, name='analytics'),
]