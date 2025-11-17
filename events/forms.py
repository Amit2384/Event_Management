from django import forms
from .models import Event #, Category
from django.utils import timezone

class EventForm(forms.ModelForm):
    """
    Form for creating and updating events.
    Includes validation for dates and seat capacity.
    """
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type', 'status',
            'start_date', 'end_date', 'venue_name', 'venue_address',
            'city', 'state', 'country', 'zip_code', 'total_seats',
            'ticket_price', 'banner_image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Event Title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Event Description',
                'rows': 5
            }),

            # Category to comment out
            # 'category': forms.Select(attrs={
            #     'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            # }),
            'event_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'datetime-local'
            }),
            'venue_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Venue Name'
            }),
            'venue_address': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Venue Address',
                'rows': 3
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'State'
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Country'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'ZIP Code'
            }),
            'total_seats': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Total Seats',
                'min': '1'
            }),
            'ticket_price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Ticket Price (0.00 for free)',
                'step': '0.01',
                'min': '0'
            }),
            'banner_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'accept': 'image/*'
            })
        }
    
    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        event_type = cleaned_data.get('event_type')
        ticket_price = cleaned_data.get('ticket_price')
        
        # Validate dates
        if start_date and end_date:
            if end_date <= start_date:
                raise forms.ValidationError('End date must be after start date.')
            
            if start_date < timezone.now():
                raise forms.ValidationError('Start date cannot be in the past.')
        
        # Validate ticket price for paid events
        if event_type == 'paid' and (not ticket_price or ticket_price <= 0):
            raise forms.ValidationError('Paid events must have a ticket price greater than 0.')
        
        return cleaned_data

# class CategoryForm(forms.ModelForm):
#     """Form for creating event categories"""
    
#     class Meta:
#         model = Category
#         fields = ['name', 'description', 'icon']
#         widgets = {
#             'name': forms.TextInput(attrs={
#                 'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
#                 'placeholder': 'Category Name'
#             }),

#             'icon': forms.TextInput(attrs={
#                 'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
#                 'placeholder': 'Font Awesome Icon (e.g., fa-calendar)'
#             }),
#         }