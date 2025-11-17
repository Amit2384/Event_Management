from django import forms
from .models import RSVP

class RSVPForm(forms.ModelForm):
    """Form for creating RSVP"""
    
    class Meta:
        model = RSVP
        fields = ['number_of_tickets', 'notes']
        widgets = {
            'number_of_tickets': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'min': '1',
                'value': '1'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Any special requests or notes (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
    
    def clean_number_of_tickets(self):
        """Validate ticket quantity"""
        number_of_tickets = self.cleaned_data.get('number_of_tickets')
        
        if number_of_tickets < 1:
            raise forms.ValidationError('You must book at least 1 ticket.')
        
        if self.event and number_of_tickets > self.event.available_seats:
            raise forms.ValidationError(
                f'Only {self.event.available_seats} seats available.'
            )
        
        return number_of_tickets