# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-11-28 11:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0006_pixel_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pixel',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pixels', to='collector.Project'),
        ),
    ]
