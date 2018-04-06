# Generated by Django 2.0.1 on 2018-02-22 13:57

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('collector', '0034_fill_test_leads'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Audit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('processed', models.DateTimeField(auto_created=True)),
                ('method', models.CharField(max_length=60)),
                ('input_data', django.contrib.postgres.fields.jsonb.JSONField()),
                ('leads', models.ManyToManyField(related_name='audits', to='collector.Lead')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]