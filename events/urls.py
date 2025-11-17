from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('create/', views.event_create, name='event_create'),
    path('my-events/', views.my_events, name='my_events'),
    # path('categories/', views.category_list, name='category_list'),
    path('<slug:slug>/', views.event_detail, name='event_detail'),
    path('<slug:slug>/edit/', views.event_update, name='event_update'),
    path('<slug:slug>/delete/', views.event_delete, name='event_delete'),
]