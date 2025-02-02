from django import forms
from .models import User


class UserLoginForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'password')
        labels = {'username': '', 'password': ''}
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        }

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password != self.cleaned_data.get('password'):
            raise forms.ValidationError("Password must match")
