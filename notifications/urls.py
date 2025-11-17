from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('event/<slug:event_slug>/send/', views.send_event_notification, name='send_notification'),
]