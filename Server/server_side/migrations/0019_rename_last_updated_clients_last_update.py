# Generated by Django 5.1.4 on 2025-03-08 19:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server_side', '0018_clients_id_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='clients',
            old_name='last_updated',
            new_name='last_update',
        ),
    ]
