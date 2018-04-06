# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-11-27 08:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0004_pixel'),
    ]

    operations = [
        migrations.AddField(
            model_name='pixel',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pixel',
            name='removed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='pixel',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='project',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='pixel',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pixels', to='collector.Project'),
        ),
    ]