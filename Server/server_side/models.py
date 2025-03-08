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

    def last_online_str(self):
        time_in_minute = (now() - self.last_update).seconds / 60
        if time_in_minute > 60:
            return f'{round(time_in_minute / 60)} hr'
        else:
            return f'{round(time_in_minute)} min'

    def last_online(self):
        time_in_minute = (now() - self.last_update).seconds / 60
        return time_in_minute

    def __str__(self):
        return f'{self.name}, {self.ip_address}, {self.last_update}'


class Commands(models.Model):
    receiver = models.ForeignKey(Clients, on_delete=models.CASCADE)
    command = models.CharField(max_length=100)
    response = models.CharField(max_length=500, default='')
    is_executed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

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

