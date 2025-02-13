from django import forms
from .models import Uploads

class UploadsForm(forms.ModelForm):
    class Meta:
        model = Uploads
        fields = ['file']
