# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-05 00:13
from __future__ import unicode_literals
import os

from django.conf import settings
from django.db import migrations
from pyexcel_xlsx import get_data


def fill_refs(apps, schema_editor):
	data = get_data("{0}/{1}.xlsx".format(os.path.join(settings.BASE_DIR, 'refs_data'),
		'devices'))
	data = data['Отчет']

	DeviceType = apps.get_model('collector', 'DeviceType')
	DeviceBrand = apps.get_model('collector', 'DeviceBrand')
	Device = apps.get_model('collector', 'Device')

	phone = DeviceType.objects.create(category=1)
	tablet = DeviceType.objects.create(category=2)
	other = DeviceType.objects.create(category=3)

	brand_other = DeviceBrand.objects.create(name="Other")

	device_types = {"Смартфоны": phone, "Планшеты": tablet}

	for d in data[1:]:
		brand = d[1].lower()
		if brand == "не определено":
			brand = brand_other


		if d[0] not in device_types.keys():
			continue
		device_type = device_types.get(d[0])

		brand, created = DeviceBrand.objects.get_or_create(name=brand)

		Device.objects.create(device_type=device_type, brand=brand, model=d[2].lower()[0:49])

	Device.objects.create(device_type=other, brand=brand_other, model="other")



class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0016_auto_20180105_0011'),
    ]

    operations = [
    	migrations.RunPython(fill_refs),
    ]