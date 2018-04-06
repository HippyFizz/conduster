# Generated by Django 2.0.1 on 2018-03-21 11:44

from django.db import migrations


def forwards_func(apps, schema_editor):
    channel_map = {}
    TrafficChannel = apps.get_model("collector", "TrafficChannel")
    channel_map['display'] = TrafficChannel.objects.create(name='display')
    channel_map['paid'] = TrafficChannel.objects.create(name='paid')
    channel_map['affiliate'] = TrafficChannel.objects.create(name='affiliate')
    channel_map['social'] = TrafficChannel.objects.create(name='social')
    channel_map['email'] = TrafficChannel.objects.create(name='email')
    channel_map['organic'] = TrafficChannel.objects.create(name='organic')
    channel_map['direct'] = TrafficChannel.objects.create(name='direct')
    channel_map['internal'] = TrafficChannel.objects.create(name='internal')
    channel_map['referral'] = TrafficChannel.objects.create(name='referral')


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0043_auto_20180321_1112'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
