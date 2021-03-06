# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-11-22 13:07
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=512)),
                ('status', models.CharField(choices=[('advertiser', 'Advertiser'), ('moderator', 'Moderator'), ('admin', 'Admin')], max_length=20)),
                ('activation_code', models.CharField(blank=True, max_length=4, null=True)),
                ('activation_code_hash', models.CharField(blank=True, max_length=40, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
