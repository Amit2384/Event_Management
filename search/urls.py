from django.urls import path
from . import views
from django.shortcuts import get_object_or_404
# from events.models import Category

app_name = 'search'

urlpatterns = [
    path('', views.search_events, name='search'),
    path('advanced/', views.advanced_search, name='advanced_search'),
    # path('category/<int:category_id>/', views.filter_by_category, name='filter_by_category'),
]