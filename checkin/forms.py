from django import forms

class CheckInForm(forms.Form):
    """Form for checking in attendees using ticket number or QR code"""
    
    ticket_number = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg',
            'placeholder': 'Enter Ticket Number or Scan QR Code',
            'autofocus': True
        })
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Check-in notes (optional)',
            'rows': 2
        })
    )