# Generated by Django 5.1.4 on 2025-02-08 23:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server_side', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='clients',
            name='last_updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
