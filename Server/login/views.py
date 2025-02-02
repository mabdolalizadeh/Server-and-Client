from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import UserLoginForm  # Ensure this form exists


def login_view(request):
    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect("server")

        else:
            print(form.errors)

    else:
        form = UserLoginForm()
    return render(request, "login/login.html", {"form": form})
