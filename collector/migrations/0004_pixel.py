# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-11-14 07:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0003_auto_20171105_1222'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pixel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='collector.Project')),
            ],
        ),
    ]