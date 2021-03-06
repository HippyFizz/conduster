# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-01-25 14:25
from __future__ import unicode_literals

from django.contrib.auth.hashers import make_password
from django.db import migrations

from collector.management.commands.fill_test_leads import fill_test_leads


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    User = apps.get_model("auth", "User")
    db_alias = schema_editor.connection.alias
    user, _ = User.objects.using(db_alias).get_or_create(
        username='root@conduster.com',
        defaults={
            'password': make_password('random64'),
            'email': 'root@conduster.com',
            'is_superuser': True,
            'is_staff': True,
            'is_active': True
        }
    )
    Profile = apps.get_model("profiles", "Profile")
    profile, _ = Profile.objects.using(db_alias).get_or_create(
        user=user,
        defaults = {'company_name': 'Conduster'}
    )
    Project = apps.get_model("collector", "Project")
    project, _ = Project.objects.using(db_alias).get_or_create(
        user=user,
        title='Тестовый проект'
    )
    Pixel = apps.get_model("collector", "Pixel")
    pixel, _ = Pixel.objects.using(db_alias).get_or_create(
        project=project,
        title='Тестовая форма'
    )
    # Lead = apps.get_model("collector", "Lead")
    # fill_test_leads(pixel.id, Lead.objects.using(db_alias), Lead)


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0029_auto_20180124_0845'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
