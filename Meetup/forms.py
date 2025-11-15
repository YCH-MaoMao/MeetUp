from django import forms
from .models import Activity

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['title', 'location', 'date_time', 'category', 'max_participants', 'description']
        
