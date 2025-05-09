# Generated by Django 5.1.4 on 2025-02-14 00:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server_side', '0006_commands_command_response_commands_is_executed'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploads',
            name='is_downloaded',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='uploads',
            name='file',
            field=models.FileField(upload_to='uploads/'),
        ),
    ]
