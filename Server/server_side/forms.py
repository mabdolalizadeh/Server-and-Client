from django import forms
from .models import Uploads


class UploadsForm(forms.ModelForm):
    class Meta:
        model = Uploads
        fields = ['file', 'command']

        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'command': forms.TextInput(attrs={'class': 'form-control',
                                              'placeholder': 'Command and place'}),
        }
