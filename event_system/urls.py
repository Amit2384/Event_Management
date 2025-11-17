from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Module URLs
    path('', include('dashboard.urls')),
    path('auth/', include('authentication.urls')),
    path('events/', include('events.urls')),
    path('rsvp/', include('rsvp.urls')),
    path('checkin/', include('checkin.urls')),
    path('notifications/', include('notifications.urls')),
    path('search/', include('search.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "Event Management System Admin"
admin.site.site_title = "Event Management Admin"
admin.site.index_title = "Welcome to Event Management System"