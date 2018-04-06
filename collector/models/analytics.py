# -*- coding: utf-8 -*-
import binascii
import uuid
from datetime import timedelta, time

import hashlib
from collections import OrderedDict, namedtuple
from django.db import models
from django.db.models.deletion import CASCADE, PROTECT
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField

from collector.models.dictionaries import City, Provider, BrowserVersion, Device, OS, TrafficChannel
from collector.models.projects import Pixel
from utils.ad import parse_url_utms, parse_url_openstat


class Lead(models.Model):
    """
    Main statistic table for analytics
    Cron script should fill this table by groupping and enriching raw data from sessions and events
    """
    # id is session id. Do not use foreign key here because in future sessions will be in files
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pixel = models.ForeignKey(Pixel, related_name="leads", on_delete=PROTECT)
    session_started = models.DateTimeField(db_index=True)
    # some device fingerprint
    device_id = models.CharField(max_length=255, null=True, blank=True)
    # ip
    ip_addr = models.GenericIPAddressField(blank=True, null=True)
    # subnet of ip (ip address with zero last octet)
    subnet = models.GenericIPAddressField(blank=True, null=True)
    provider = models.ForeignKey(Provider, blank=True, null=True, on_delete=PROTECT)
    geo = models.ForeignKey(City, blank=True, null=True, default=None, on_delete=PROTECT)
    os_version = models.ForeignKey(OS, blank=True, null=True, default=None, on_delete=PROTECT)
    browser = models.ForeignKey(BrowserVersion, blank=True, null=True, default=None, on_delete=PROTECT)
    device_model = models.ForeignKey(Device, blank=True, null=True, default=None, on_delete=PROTECT)
    traffic_channel = models.ForeignKey(TrafficChannel, blank=True, null=True, default=None, on_delete=PROTECT)
    last_event_time = models.DateTimeField(null=True, blank=True, db_index=True)
    created = models.DateTimeField(null=True, blank=True, db_index=True)
    metrik_lead_duration = models.IntegerField(blank=True, null=True, default=None)
    metrik_lead_salecount = models.IntegerField(default=0)

    def __str__(self):
        # pixel_title = self.pixel.title if self.pixel else None
        return "Pixel {0}: Id: {1} SessionStarted {2}".format(self.pixel_id, self.id, self.session_started)

    def fields_hash_map(self, field_names):
        if not field_names:
            return {}
        return dict(
            self.fields.filter(field_name__in=tuple(field_names))
                .values_list('field_name', 'field_hash')
        )

    def set_metrik_lead_duration(self):
        session_end = self.created or self.last_event_time
        if self.created and self.last_event_time:
            session_end = max(self.created, self.last_event_time)
        if session_end:
            self.metrik_lead_duration = (session_end - self.session_started).total_seconds()


class LeadField(models.Model):
    """
    Form data for lead
    Cron script should fill this table by groupping and enriching raw data from sessions and events
    """
    lead = models.ForeignKey(Lead, related_name='fields', on_delete=CASCADE)
    field_name = models.CharField(max_length=100)
    field_hash = models.CharField(max_length=100)
    field_data = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{0}: {1} = {2}".format(self.lead, self.field_name,
                                       self.field_data or self.field_hash)

    class Meta:
        index_together = ('field_name', 'field_hash')

    @staticmethod
    def normalize_field_data(field_data):
        return str(field_data).strip().lower()

    @classmethod
    def make_field_data_hash(cls, field_data):
        field_data = cls.normalize_field_data(field_data)
        return hashlib.sha1(force_bytes(field_data)).hexdigest()


class LeadUtm(models.Model):
    lead = models.ForeignKey(Lead, related_name='utm', on_delete=CASCADE)
    utm_source = models.CharField(max_length=255, db_index=True)
    utm_medium = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    utm_campaign = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    utm_term = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    utm_content = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    @classmethod
    def parse_url(cls, url):
        labels = parse_url_utms(url)
        if labels is None:
            return None
        obj = cls()
        obj.utm_source, obj.utm_medium, obj.utm_campaign, obj.utm_term, obj.utm_content = labels
        return obj


class LeadOpenstat(models.Model):
    lead = models.ForeignKey(Lead, related_name='openstat', on_delete=CASCADE)
    service = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    campaign = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    ad = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    source = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    @classmethod
    def parse_url(cls, url):
        labels = parse_url_openstat(url)
        if labels is None:
            return None
        obj = cls()
        obj.service, obj.campaign, obj.ad, obj.source = labels
        return obj


LeadGroup = namedtuple('LeadGroup', ('title', 'operator', 'val1', 'val2'))

LEAD_AGE_GROUPS = OrderedDict((
    # id, label, operator (lt,gt,lte,gte, range (right exclusive))
    # , val in seconds, val2 in seconds if range
    ('less_5_minutes', LeadGroup(_('less than 5 minutes'), 'range', 5 * 60 - 1, 0)),
    ('5_to_30_minutes', LeadGroup(_('from 5 to 30 minutes'), 'range', 30 * 60 - 1, 5 * 60)),
    ('30_to_60_minutes', LeadGroup(_('from 30 to 60 minutes'), 'range', 60 * 60 - 1, 30 * 60)),
    ('1_to_4_hours', LeadGroup(_('from 1 to 4 hours'), 'range', 4 * 60 * 60 - 1, 60 * 60)),
    ('4_to_12_hours', LeadGroup(_('from 4 to 12 hours'), 'range', 12 * 60 * 60 - 1, 4 * 60 * 60)),
    (
        '12_to_24_hours',
        LeadGroup(_('from 12 to 24 hours'), 'range', 24 * 60 * 60 - 1, 12 * 60 * 60)
    ),
    ('1_to_2_days', LeadGroup(_('from 1 to 2 days'), 'range', 2 * 24 * 60 * 60 - 1, 24 * 60 * 60)),
    (
        '2_days_to_1_week',
        LeadGroup(_('from 2 days to 1 week'), 'range', 7 * 24 * 60 * 60 - 1, 2 * 24 * 60 * 60)
    ),
    (
        '1_week_to_1_month',
        LeadGroup(_('from 1 week to 1 month'), 'range', 30 * 24 * 60 * 60 - 1, 7 * 24 * 60 * 60)
    ),
    (
        '1_month_to_1_year',
        LeadGroup(_('from 1 month to 1 year'), 'range', 365 * 24 * 60 * 60 - 1, 30 * 24 * 60 * 60)
    ),
    ('more_1_year', LeadGroup(_('more than 1 year'), 'lte', 365 * 24 * 60 * 60, None)),
))

LEAD_DURATION_GROUPS = OrderedDict((
    # id, label, operator (lt,gt,lte,gte, range (right exclusive))
    # , val in seconds, val2 in seconds if range
    ('less_5_seconds', LeadGroup(_('less than 5 seconds'), 'range', 0, 5 - 1)),
    ('5_to_30_seconds', LeadGroup(_('from 5 to 30 seconds'), 'range', 5, 30 - 1)),
    ('30_to_60_seconds', LeadGroup(_('from 30 to 60 seconds'), 'range', 30, 60 - 1)),
    ('1_to_5_minutes', LeadGroup(_('from 1 to 5 minutes'), 'range', 60, 5 * 60 - 1)),
    ('5_to_30_minutes', LeadGroup(_('from 5 to 30 minutes'), 'range', 5 * 60, 30 * 60 - 1)),
    ('30_to_60_minutes', LeadGroup(_('from 30 to 60 minutes'), 'range', 30 * 60, 60 * 60 - 1)),
    ('more_1_hour', LeadGroup(_('more than 1 hour'), 'gte', 60 * 60, None)),
))

ConsumerOriginGroup = namedtuple('ConsumerOriginGroup', ('title', 'delta'))

CONSUMER_ORIGIN_GROUPS = OrderedDict((
    ('5_minutes', ConsumerOriginGroup(_('5 minutes'), timedelta(minutes=5))),
    ('1_hour', ConsumerOriginGroup(_('1 hour'), timedelta(hours=1))),
    ('3_hours', ConsumerOriginGroup(_('3 hours'), timedelta(hours=3))),
    ('12_hours', ConsumerOriginGroup(_('12 hours'), timedelta(hours=12))),
    ('1_day', ConsumerOriginGroup(_('1 day'), timedelta(hours=24)))
))


class IpStat(models.Model):
    IP_STATE_CHOICES = (
        ('low risk', 'low risk'),
        ('middle risk', 'middle risk'),
        ('high risk', 'high risk')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(db_index=True)
    ip = models.GenericIPAddressField(db_index=True)
    cl_type = models.CharField(max_length=255, null=True, blank=True, help_text=_('Client type'))
    s_cnt = models.IntegerField(help_text=_('Total amount of sessions'), default=0)
    s_time = models.DurationField(help_text=_('Total duration of sessions'), default=timedelta(0))
    s0_cnt = models.IntegerField(help_text=_('Total amount of unfinished sessions'), default=0)
    s_cnt30 = models.IntegerField(help_text=_('Amount of sessions in last 30 days'), default=0)
    s_time30 = models.DurationField(help_text=_('Duration of sessions in last 30 days'),
                                    default=timedelta(0))
    s0_cnt30 = models.IntegerField(help_text=_('Amount of unfinished sessions in last 30 days'),
                                   default=0)
    s_cnt10 = models.IntegerField(help_text=_('Amount of sessions in last 10 days'), default=0)
    s_time10 = models.DurationField(help_text=_('Duration of sessions in last 10 days'),
                                    default=timedelta(0))
    s0_cnt10 = models.IntegerField(help_text=_('Amount of unfinished sessions in last 10 days')
                                   , default=0)
    s_cnt3 = models.IntegerField(help_text=_('Amount of sessions in last 3 days'), default=0)
    s_time3 = models.DurationField(help_text=_('Duration of sessions in last 3 days'),
                                   default=timedelta(0))
    s0_cnt3 = models.IntegerField(help_text=_('Amount of unfinished sessions in last 3 days')
                                  , default=0)
    s_beg30 = models.TimeField(help_text=_('Avg time session start in last 30'),
                               default=time(0))
    s_beg10 = models.TimeField(help_text=_('Avg time session start in last 10'),
                               default=time(0))
    s_beg3 = models.TimeField(help_text=_('Avg time session start in last 3'),
                              default=time(0))
    ip_state = models.CharField(max_length=10, choices=IP_STATE_CHOICES, null=True, blank=True)
    country = CountryField(blank=True, null=True)
    city = models.ForeignKey(City, blank=True, null=True, on_delete=PROTECT)
    index = models.CharField(max_length=12, blank=True, null=True, help_text=_('Postal code'))
    provider = models.ForeignKey(Provider, blank=True, null=True,
                                 help_text=_('Inet provider'), on_delete=PROTECT)
    cnt_dev30 = models.IntegerField(help_text=_('Amount of devices in last 30 days'), default=0)
    cnt_dev10 = models.IntegerField(help_text=_('Amount of devices in last 10 days'), default=0)
    cnt_dev3 = models.IntegerField(help_text=_('Amount of devices in last 3 days'), default=0)
