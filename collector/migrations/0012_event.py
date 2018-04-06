# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-12-21 14:50
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0011_auto_20171220_1513'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('even_type', models.CharField(choices=[('field-filled', 'field-filled'), ('form-submitted', 'form-submitted')], max_length=50)),
                ('started', models.DateTimeField()),
                ('finished', models.DateTimeField()),
                ('duration', models.IntegerField(help_text='in milliseconds')),
                ('field_type', models.CharField(max_length=50)),
                ('field_number', models.IntegerField()),
                ('field_parent_number', models.IntegerField(blank=True, help_text='previous filled field number', null=True)),
                ('field_hidden', models.BooleanField(default=False)),
                ('field_checked', models.BooleanField(default=False)),
                ('field_readonly', models.BooleanField(default=False)),
                ('field_name', models.CharField(blank=True, max_length=255, null=True)),
                ('field_id', models.CharField(blank=True, max_length=255, null=True)),
                ('field_alt', models.CharField(blank=True, max_length=255, null=True)),
                ('field_title', models.CharField(blank=True, max_length=255, null=True)),
                ('field_data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, help_text='data-... attrs', null=True)),
                ('field_accesskey', models.CharField(blank=True, max_length=20, null=True)),
                ('field_class', models.CharField(blank=True, help_text='css class attr', max_length=255, null=True)),
                ('field_contenteditable', models.CharField(blank=True, max_length=10, null=True)),
                ('field_contextmenu', models.CharField(blank=True, max_length=100, null=True)),
                ('field_dir', models.CharField(blank=True, help_text='text direction attr', max_length=20, null=True)),
                ('field_lang', models.CharField(blank=True, max_length=100, null=True)),
                ('field_spellcheck', models.CharField(blank=True, max_length=10, null=True)),
                ('field_style', models.CharField(blank=True, help_text='css style attr', max_length=255, null=True)),
                ('field_tabindex', models.CharField(blank=True, help_text='tabindex attr', max_length=10, null=True)),
                ('field_required', models.CharField(blank=True, help_text='required attr', max_length=10, null=True)),
                ('field_pattern', models.CharField(blank=True, help_text='pattern attr', max_length=100, null=True)),
                ('field_list', models.CharField(blank=True, help_text='list attr', max_length=50, null=True)),
                ('correction_count', models.IntegerField(default=0, help_text='count of corrections by user')),
                ('keypress_count', models.IntegerField(default=0, help_text='count of keypress by user')),
                ('special_keypress_count', models.IntegerField(default=0, help_text='count of keypress by user')),
                ('text_length', models.IntegerField(default=0)),
                ('from_clipboard', models.BooleanField(default=False, help_text='is data pasted from clipboard?')),
                ('open_data', models.TextField(blank=True, help_text='entered data', null=True)),
                ('hash_data', models.CharField(help_text='entered data hash', max_length=100)),
                ('field_parent', models.OneToOneField(help_text='previous filled field', on_delete=django.db.models.deletion.CASCADE, to='collector.Event')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='collector.SessionStorage')),
            ],
        ),
    ]
