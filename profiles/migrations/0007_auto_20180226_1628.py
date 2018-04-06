# Generated by Django 2.0.1 on 2018-02-26 16:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0006_auto_20180215_1558'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='company_name',
            field=models.CharField(default='unknown', max_length=512),
        ),
        migrations.AlterField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL),
        ),
    ]