# Generated by Django 2.0.1 on 2018-03-15 13:59

from django.db import migrations, models
import django.db.models.deletion

from django.db import migrations, models
import django.db.models.deletion

from utils.ua import get_os_group_by_family


def forwards_func(apps, schema_editor):
    OSGroup = apps.get_model("collector", "OSGroup")
    db_alias = schema_editor.connection.alias
    groups = (
        'Windows', 'Google Android', 'iOS', 'Mac OS', 'GNU/Linux', 'Tizen',
        'Google Chrome OS', 'BlackBerry OS', 'SymbianOS', 'BSD', 'Other'
    )
    groups_map = {}
    for name in groups:
        group, _ = OSGroup.objects.using(db_alias).get_or_create(name=name)
        groups_map[name] = group

    OSFamily = apps.get_model("collector", "OSFamily")
    families = OSFamily.objects.using(db_alias).all()
    for family in families:
        group_name = get_os_group_by_family(family.name)
        family.group = groups_map[group_name]
        family.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0038_fill_test_leads'),
    ]

    operations = [
        migrations.CreateModel(
            name='OSGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.AlterModelOptions(
            name='os',
            options={'verbose_name': 'Os', 'verbose_name_plural': 'Os versions'},
        ),
        migrations.AlterModelOptions(
            name='osfamily',
            options={'verbose_name_plural': 'Os families'},
        ),
        migrations.AddField(
            model_name='lead',
            name='browser',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='collector.BrowserVersion'),
        ),
        migrations.AddField(
            model_name='lead',
            name='device_model',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='collector.Device'),
        ),
        migrations.AddField(
            model_name='lead',
            name='os_version',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='collector.OS'),
        ),
        migrations.AlterField(
            model_name='os',
            name='family',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='os_versions', to='collector.OSFamily'),
        ),
        migrations.AddField(
            model_name='osfamily',
            name='group',
            field=models.ForeignKey(null=True, blank=True,
                                    on_delete=django.db.models.deletion.PROTECT,
                                    to='collector.OSGroup'),
            preserve_default=False,
        ),
        migrations.RunPython(forwards_func, reverse_func),
        migrations.AlterField(
            model_name='osfamily',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                    to='collector.OSGroup'),
            preserve_default=False,
        ),
    ]
