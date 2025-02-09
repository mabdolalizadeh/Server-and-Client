from django.utils.timezone import now
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
import random
import string
from .models import *
from django.views.generic import View
import requests



def name_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip


def create_or_get_user(request):
    clients = Clients.objects.all()
    ip = get_client_ip(request)
    agent = clients.filter(address=ip).first()
    agent.last_updated = now()
    agent.save()
    if not clients.filter(address=ip).exists():
        Clients.objects.create(address=ip, name=name_generator())
        clients = Clients.objects.all()

    return clients


class IndexView(View):
    def get(self, request):
        clients = create_or_get_user(request)
        context = {
            'clients': clients,
        }

        return render(request, 'server_side/index.html', context)

    def post(self, request):
        clients = create_or_get_user(request)
        if self.request.POST.get('command'):
            clients = create_or_get_user(request).order_by('-last_updated')
            command = Commands.objects.create(receiver=clients[1], command=self.request.POST.get('command'))
            receiver = clients[1]

            requests.post(f'http://{receiver.address}', data={'command': command.command,
                                                              'id': command.id})
            return redirect('index')

        return render(request, 'server_side/index.html', context={
            'clients': clients,
        })



def logout_view(request):
    logout(request)
    return redirect('login')
