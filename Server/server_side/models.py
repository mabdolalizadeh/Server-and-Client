from django.db import models
from django.utils.timezone import now


class Clients(models.Model):
    name = models.CharField(max_length=100)
    address = models.GenericIPAddressField(unique=True)
    last_updated = models.DateTimeField(auto_now=True)

    def is_online(self):
        return (now() - self.last_updated).seconds < 30

    def __str__(self):
        return f'{self.name}, {self.address}, {self.last_updated}'


class Commands(models.Model):
    receiver = models.ForeignKey(Clients, on_delete=models.CASCADE)
    command = models.CharField(max_length=100)
    command_response = models.CharField(max_length=500, default='')
    is_executed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.receiver}, {self.command}, {self.timestamp}'


class Uploads(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.client}, {self.timestamp}'
