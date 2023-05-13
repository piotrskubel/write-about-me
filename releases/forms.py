'''Django forms'''
from django import forms

class PlatformForm(forms.Form):
    '''Platform selection form'''
    PLATFORM_CHOICES = [
        ('', 'All Platforms'),
        ('NS', 'Nintendo Switch'),
        ('XSX', 'Xbox Series X/S'),
        ('PS5', 'PlayStation 5'),
        ('XBO', 'Xbox One'),
        ('PS4', 'PlayStation 4'),
        ('Win', 'PC')
    ]
    platform = forms.ChoiceField(choices=PLATFORM_CHOICES, required=False)
