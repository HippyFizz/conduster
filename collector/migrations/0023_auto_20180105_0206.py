# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-05 02:06
from __future__ import unicode_literals
import os

from django.conf import settings
from django.db import migrations
from pyexcel_xlsx import get_data


def fill_refs(apps, schema_editor):
	data = get_data("{0}/{1}.xlsx".format(os.path.join(settings.BASE_DIR, 'refs_data'),
		'res'))
	data = data['Отчет']

	ScreenResolution = apps.get_model('collector', 'ScreenResolution')

	for r in data[1:]:
		ScreenResolution.objects.create(width=r[1], height=r[2])


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0022_screenresolution'),
    ]

    operations = [
		migrations.RunPython(fill_refs),
    ]
