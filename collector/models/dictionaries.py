# -*- coding: utf-8 -*-
from django.contrib.gis import geoip2
from django.db import models
from django.db.models.deletion import PROTECT
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from geoip2.errors import AddressNotFoundError

from utils.ad import parse_traffic_channel
from utils.network import ip_provider


class Font(models.Model):
    name = models.CharField(max_length=256, unique=True)

    def __str__(self):
        return self.name


class DeviceType(models.Model):
    PHONE, TABLET, DESKTOP = range(1, 4)

    TYPES = (
        (PHONE, _("Phone")),
        (TABLET, _("Tablet")),
        (DESKTOP, _("Desktop")),
    )

    category = models.PositiveSmallIntegerField(choices=TYPES)

    def __str__(self, *args, **kwargs):
        return str(dict(self.TYPES).get(self.category))


class DeviceBrand(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self, *args, **kwargs):
        return self.name


class Device(models.Model):
    device_type = models.ForeignKey(DeviceType, on_delete=PROTECT)
    brand = models.ForeignKey(DeviceBrand, on_delete=PROTECT)
    model = models.CharField(max_length=50)

    def __str__(self, *args, **kwargs):
        return '{} {} {}'.format(self.device_type, self.brand.name, self.model)


class BrowserGroup(models.Model):
    class Meta:
        ordering = ('name',)

    name = models.CharField(max_length=50, unique=True)

    def __str__(self, *args, **kwargs):
        return self.name


class BrowserFamily(models.Model):
    class Meta:
        verbose_name_plural = "browser families"

    name = models.CharField(max_length=50)
    group = models.ForeignKey(BrowserGroup, on_delete=PROTECT)

    def __str__(self, *args, **kwargs):
        return '{0}'.format(self.name)


class BrowserVersion(models.Model):
    family = models.ForeignKey(BrowserFamily, on_delete=PROTECT)
    version = models.CharField(max_length=50)

    def __str__(self, *args, **kwargs):
        return '{0}'.format(self.version)


class OSGroup(models.Model):
    class Meta:
        ordering = ('name',)

    name = models.CharField(max_length=50, unique=True)
    is_mobile=models.BooleanField(default=False, db_index=True)

    def __str__(self, *args, **kwargs):
        return self.name


class OSFamily(models.Model):
    class Meta:
        verbose_name_plural = "OS families"

    group = models.ForeignKey(OSGroup, on_delete=PROTECT)
    name = models.CharField(max_length=50)

    def __str__(self, *args, **kwargs):
        return '{0}'.format(self.name)


class OS(models.Model):
    class Meta:
        verbose_name = "OS"
        verbose_name_plural = "Os versions"

    family = models.ForeignKey(OSFamily, on_delete=PROTECT)
    name = models.CharField(max_length=50)

    def __str__(self, *args, **kwargs):
        return '{0}'.format(self.name)


class ScreenResolution(models.Model):
    width = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField()

    def __str__(self, *args, **kwargs):
        return '{0}x{1}'.format(self.width, self.height)


class City(models.Model):
    class Meta:
        verbose_name_plural = "cities"

    country = CountryField()
    name = models.CharField(max_length=100, blank=True, null=True)
    name_ru = models.CharField(max_length=100, blank=True, null=True, default="")
    region = models.CharField(max_length=10, blank=True, null=True)
    region_ru = models.CharField(max_length=10, blank=True, null=True, default="")
    postal_code = models.CharField(max_length=12, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    def __str__(self, *args, **kwargs):
        return '{0}: {1}({2})'.format(self.country.name, self.name, self.name_ru)

    @classmethod
    def get_or_create_by_ip(cls, ip_addr):
        geo = geoip2.GeoIP2()
        try:
            geo = geo.city(ip_addr)
            city, created = cls.objects.get_or_create(
                country=geo.get("country_code"),
                name=geo.get("city"),
                region=geo.get("region"),
                postal_code=geo.get("postal_code"),
                latitude=geo.get("latitude"),
                longitude=geo.get("longitude")
            )
        except AddressNotFoundError:
            city = None
        return city


class Provider(models.Model):
    """
    get by ipwhois
    """
    asn = models.CharField(max_length=255, db_index=True)
    asn_description = models.CharField(max_length=255)

    @classmethod
    def get_or_create_by_ip(cls, ip_addr):
        provider_info = ip_provider(ip_addr)
        provider = None
        if provider_info:
            provider, created = cls.objects.get_or_create(
                asn=provider_info['asn'],
                defaults={'asn_description': provider_info['asn_description']}
            )
        return provider

    def __str__(self, *args, **kwargs):
        return '{}: {}'.format(self.asn, self.asn_description)


class Field(models.Model):
    """
    Dictionary of form field names in system.
    Used in FieldMapping
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self, *args, **kwargs):
        return self.name


class TrafficChannel(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self, *args, **kwargs):
        return self.name

    @classmethod
    def parse(cls, referrer, url):
        return parse_traffic_channel(referrer, url)









