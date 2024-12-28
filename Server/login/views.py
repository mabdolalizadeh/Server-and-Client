from django.shortcuts import redirect
from django.views import View
from django.views.generic import CreateView, FormView
from login import forms
from login.models import User


# Create your views here.
class LoginView(FormView):
    template_name = 'login/login.html'
    form_class = forms.UserLoginForm

    def form_valid(self, form):
        user = User.objects.get(username=form.cleaned_data['username'])
        if user and user.is_active and user.check_password(form.cleaned_data['password']):
            return redirect('server')
        else:
            form.add_error("Username or password incorrect")






