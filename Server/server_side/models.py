from django.db import models
from django.utils.timezone import now


class Clients(models.Model):
    name = models.CharField(max_length=100)
    id_name = models.CharField(max_length=100, default='')
    ip_address = models.GenericIPAddressField(unique=True)
    last_update = models.DateTimeField(auto_now=True)
    username = models.CharField(max_length=100, default='')
    password = models.CharField(max_length=100, default='')
    domain = models.CharField(max_length=100, default='')
    interval = models.IntegerField(default=5)

    def last_online_str(self):
        now_time = now()
        delta = now_time - self.last_update

        seconds = int(delta.total_seconds())
        minutes = seconds // 60
        hours = minutes // 60
        days = hours // 24

        if seconds < 60:
            return f'{seconds} sec'
        elif minutes < 60:
            return f'{minutes} min'
        elif hours < 24:
            return f'{hours} hour'
        elif days == 1 or (now_time.day - self.last_update.day == 1 and now_time.month == self.last_update.month):
            return self.last_update.strftime("Yesterday at %H:%M")
        elif now_time.year == self.last_update.year:
            return self.last_update.strftime("%d %b at %H:%M")
        else:
            return self.last_update.strftime("%d.%m.%Y %H:%M")

    def last_online(self):
        time_in_minute = (now() - self.last_update).seconds / 60
        return time_in_minute

    def __str__(self):
        return f'{self.id_name}, {self.ip_address}, {self.last_update}'


class Commands(models.Model):
    receiver = models.ForeignKey(Clients, on_delete=models.CASCADE)
    command = models.CharField(max_length=100)
    response = models.CharField(max_length=500, default='')
    is_executed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def time_passed(self):
        time_in_minute = (now() - self.timestamp).seconds / 60
        if time_in_minute > 60:
            return f'{round(time_in_minute / 60)} hr'
        else:
            return f'{round(time_in_minute)} min'

    def __str__(self):
        return f'{self.receiver}, {self.command}, {self.timestamp}'


class Uploads(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    command = models.ForeignKey(Commands, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to='uploads/')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.client}, {self.timestamp}'

    def get_file_size(self):
        return self.file.size


class HexForDownload(models.Model):
    file = models.ForeignKey(Uploads, on_delete=models.CASCADE)
    hex = models.TextField()
    sent_count = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        self.hex = self.file.file.read().hex()
        super().save(*args, **kwargs)


class Downloads(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=100, default='')
    is_finished = models.BooleanField(default=False)


class FileManager(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=False)
    parent_name = models.CharField(max_length=100, null=False)
    files = models.JSONField(default=list)
    folders = models.JSONField(default=list)

    def __str__(self):
        return f'{self.name} .. {self.parent_name}'

    def set_files_folders(self, answer):
        lines = answer.strip().split('\n')
        files = []
        folders = []

        for line in lines:
            line = line.strip()
            if line:
                if '<DIR>' in line:
                    folders.append(line[-1])
                else:
                    files.append(line[-1])

        self.files = files
        self.folders = folders
