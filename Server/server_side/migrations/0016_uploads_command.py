# Generated by Django 5.1.4 on 2025-02-16 11:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server_side', '0015_rename_finished_downloads_is_finished_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploads',
            name='command',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='server_side.commands'),
        ),
    ]
