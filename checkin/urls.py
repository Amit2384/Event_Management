from django.urls import path
from . import views

app_name = 'checkin'

urlpatterns = [
    path('<slug:event_slug>/dashboard/', views.checkin_dashboard, name='checkin_dashboard'),
    path('<slug:event_slug>/perform/', views.perform_checkin, name='perform_checkin'),
    path('<slug:event_slug>/list/', views.checkin_list, name='checkin_list'),
    path('undo/<int:checkin_id>/', views.undo_checkin, name='undo_checkin'),
]