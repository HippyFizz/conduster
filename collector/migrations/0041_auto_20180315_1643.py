# Generated by Django 2.0.1 on 2018-03-15 16:15

import django.db.models.deletion
from django.db import migrations, models

from utils.ua import get_browser_gp_group_by_family


def create_groups(apps, schema_editor):
    BrowserGroup = apps.get_model("collector", "BrowserGroup")
    db_alias = schema_editor.connection.alias

    groups = (
        'Google Chrome',
        'Firefox',
        'Яндекс.Браузер',
        'Safari Mobile',
        'Chrome Mobile',
        'Opera',
        'MSIE', 'Edge',
        'Samsung Internet',
        'Safari',
        'Other'
    )

    groups_map = {}
    for name in groups:
        group, _ = BrowserGroup.objects.using(db_alias).get_or_create(name=name)
        groups_map[name] = group


def fill_groups(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    BrowserGroup = apps.get_model("collector", "BrowserGroup")
    BrowserFamily = apps.get_model("collector", "BrowserFamily")

    families = BrowserFamily.objects.using(db_alias).all()
    for family in families:
        group_name = get_browser_gp_group_by_family(family.name)
        group = BrowserGroup.objects.get(name=group_name)
        family.group = group
        family.save()


class Migration(migrations.Migration):
    dependencies = [
        ('collector', '0040_fill_test_leads'),
    ]

    operations = [
        migrations.CreateModel(
            name='BrowserGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
            options={'ordering': ('name',)},
        ),
        migrations.AlterModelOptions(
            name='browserfamily',
            options={'verbose_name_plural': 'browser families'},
        ),
        migrations.AlterModelOptions(
            name='os',
            options={'verbose_name': 'OS', 'verbose_name_plural': 'Os versions'},
        ),
        migrations.AlterModelOptions(
            name='osfamily',
            options={'verbose_name_plural': 'OS families'},
        ),
        migrations.RunPython(create_groups),
        migrations.AddField(
            model_name='browserfamily',
            name='group',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT,
                                    to='collector.BrowserGroup'),
            preserve_default=False,
        ),
        migrations.RunPython(fill_groups),
    ]
