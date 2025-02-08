from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


@login_required(login_url='login')
def index(request):
    context = {
        'user': request.user,
    }
    return render(request, 'server_side/index.html', context=context)


def logout_view(request):
    logout(request)
    return redirect('login')