from datetime import timedelta
from logging import getLogger

from django.core.management.base import BaseCommand
from django.db.transaction import atomic
from django.utils import timezone

from collector.models import Lead, SessionStorage, LeadField, Event, Pixel, LeadUtm, LeadOpenstat
from collector.models.dictionaries import TrafficChannel
from utils.ad import parse_traffic_channel
from utils.datetime import strptime
from utils.network import ip2subnet

logger = getLogger(__name__)

# we load sessions which last event younger than DEFAULT_PERIOD
DEFAULT_PERIOD = timedelta(minutes=5)


class Command(BaseCommand):
    help = 'fill leads table from raw session and events data'

    def add_arguments(self, parser):
        # # Positional arguments
        # parser.add_argument('pixel_id', type=str)
        parser.add_argument('--date-from', dest='date_from', type=str)
        parser.add_argument('--date-to', dest='date_to', type=str)

    @atomic()
    def handle(self, date_from=None, date_to=None, *args, **options):
        now = timezone.now()
        started = now

        session_ids = self._load_session_ids(now, date_from, date_to)
        sessions = self._load_sessions(session_ids)

        exist_leads = {lead.pk: lead for lead in Lead.objects.filter(id__in=session_ids)}

        traffic_channel_map = { channel.name: channel for channel in TrafficChannel.objects.all() }

        for session in sessions:
            channel = parse_traffic_channel(session.referrer, session.location)
            lead = exist_leads.get(session.id, Lead(
                id=session.id,
                pixel=session.pixel,
                device_id=session.get_fingerprint(),
                ip_addr=session.ip_addr,
                subnet=ip2subnet(session.ip_addr),
                provider=session.provider,
                geo=session.geo,
                device_model=session.device,
                browser=session.browser,
                os_version=session.os_version,
                traffic_channel=traffic_channel_map[channel],
                session_started=session.created,
            ))
            lead.created = session.submitted
            last_event = session.events.order_by('-finished').first()
            lead.last_event_time = last_event.finished if last_event else None
            lead.set_metrik_lead_duration()
            lead.save()

            if session.id not in exist_leads:
                self._save_lead_url_labels(session, lead)

            lead.fields.all().delete()
            self._save_lead_fields(session, lead)

        logger.info('Fill {} leads complete in {}s'.format(
            len(sessions), (timezone.now() - started).total_seconds()))

    @staticmethod
    def fill_session_field(src: str, session: SessionStorage, lead: Lead, target: str = None):
        if target is None:
            target = src
        val = getattr(session, src)
        return LeadField(
            lead=lead,
            field_name=target,
            field_hash=LeadField.make_field_data_hash(val),
            field_data=val
        )

    @classmethod
    def _fill_session_fields(cls, session: SessionStorage, lead: Lead, lead_fields=None):
        """
        fill LeadField table with tech data from session
        :param session: SessionStorage
        :param lead: Lead
        :return:
        """
        fields = {
            'ip_addr': 'ip', 'domain': 'domain', 'get_params': 'get_params',
            'user_agent_string': 'user_agent', 'cookie_enabled': 'cookie_enabled',
            'current_language': 'language', 'languages': 'languages',
            'java_enabled': 'java_enabled', 'online': 'online', 'orientation': 'orientation',
            'ad_block': 'ad_block', 'has_ss': 'has_ss', 'has_ls': 'has_ls', 'has_idb': 'has_idb',
            'has_odb': 'has_odb', 'timezone_offset': 'timezone_offset',
            'screen_color_depth': 'screen_color_depth', 'location': 'location',
            'referrer': 'referrer', 'page_title': 'page_title',
            'form_has_hidden_fields': 'form_has_hidden_fields',
            'viewport_width': 'viewport_width', 'viewport_height': 'viewport_height',
            'available_width': 'available_width', 'available_height': 'available_height',
            'page_total': 'page_total', 'form_total_fields': 'form_total_fields',
            'form_hidden_fields': 'form_hidden_fields',
            'form_disabled_fields': 'form_disabled_fields'
        }
        # os_version=os_version,
        # device=device,
        # browser=browser_version,
        # screen=screen,
        # geo=city,

        # plugin_list=data.get('pluginList'),
        # canvas_byte_array = data.get('canvas'),
        # webgl_vendor = data.get('webglVendor'),
        if lead_fields is None:
            lead_fields = {}
        for f_src, f_dst in fields.items():
            if f_dst in lead_fields:
                continue
            lead_fields[f_dst] = cls.fill_session_field(f_src, session, lead, f_dst)
        return lead_fields

    @staticmethod
    def _load_pixel_fields_mapping(pixel):
        return pixel.fields_mapping.all().select_related('target_field')

    @classmethod
    def _fill_form_fields_from_mappings(cls, form_data, lead, lead_fields=None):
        """

        :param form_data:
        :param lead:
        :param lead_fields:
        :return: Dict of LeadFields objects to create { target_field.name: LeadField}
        """
        if lead_fields is None:
            lead_fields = {}

        # fill_fields_from_mappings
        fields_mapping = cls._load_pixel_fields_mapping(lead.pixel)
        for field_mapping in fields_mapping:
            if field_mapping.target_field.name in lead_fields:
                continue
            event = field_mapping.find_event(form_data)
            if event:
                lead_field = LeadField(
                    lead=lead,
                    field_name=field_mapping.target_field.name,
                    field_hash=event.hash_data if event else None,
                    field_data=event.open_data if event else None
                )
                lead_fields[field_mapping.target_field.name] = lead_field
        return lead_fields

    @staticmethod
    def _fill_other_form_fields(form_data, lead, lead_fields):
        # fill over fields witch not in mappings
        for event in form_data.values():
            if not event.field_name or event.field_name in lead_fields:
                continue
            lead_field = LeadField(
                lead=lead,
                field_name=event.field_name,
                field_hash=event.hash_data,
                field_data=event.open_data
            )
            lead_fields[event.field_name] = lead_field
        return lead_fields

    @classmethod
    def _fill_form_fields(cls, form_data, lead, lead_fields=None):
        """
        fill LeadField table with last events values
        :param form_data: Dict
        :param lead: Lead
        :return:
        """
        if lead_fields is None:
            lead_fields = {}
        lead_fields = cls._fill_form_fields_from_mappings(form_data, lead, lead_fields)
        lead_fields = cls._fill_other_form_fields(form_data, lead, lead_fields)
        return lead_fields

    @staticmethod
    def _load_session_events(session):
        return session.events.order_by('-finished')

    @classmethod
    def _get_session_form_data(cls, session):
        """
        returns only last events to accumulate form data
        :param session:
        :return: []
        """
        events = cls._load_session_events(session)
        lead_fields = {}
        for event in events:
            if event.event_type != 'field-filled':
                continue
            if event.field_name in lead_fields:
                continue
            lead_fields[event.field_name] = event
        return lead_fields

    def _load_session_ids(self, now, date_from=None, date_to=None):
        """
        by default we load sessions which last event younger than DEFAULT_PERIOD
        else when events exists between date_from and date_to
        :param now:
        :param date_from:
        :param date_to:
        :return:
        """
        date_from = strptime(date_from) if date_from else now - DEFAULT_PERIOD
        if date_to:
            date_to = strptime(date_to).replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            date_to = now

        session_ids = Event.objects. \
            filter(finished__range=(date_from, date_to)) \
            .values_list('session_id', flat=True).distinct()

        return session_ids

    def _load_sessions(self, session_ids):
        return SessionStorage.objects \
            .filter(id__in=session_ids) \
            .prefetch_related('events') \
            .order_by('pixel_id', 'created')

    def _fill_lead_type_field(self, pixel, lead, lead_fields):
        if pixel.lead_type and 'lead_type' not in lead_fields:
            val = dict(Pixel.LEAD_TYPES).get(pixel.lead_type)
            if val:
                lead_fields['lead_type'] = LeadField(
                    lead=lead,
                    field_name='lead_type',
                    field_hash=LeadField.make_field_data_hash(val),
                    field_data=val
                )
        return lead_fields

    def _fill_lead_fields(self, session, lead):
        lead_fields = {}
        lead_fields = self._fill_lead_type_field(lead.pixel, lead, lead_fields)
        form_data = self._get_session_form_data(session)
        lead_fields = self._fill_form_fields(form_data, lead, lead_fields)
        lead_fields = self._fill_session_fields(session, lead, lead_fields)
        return lead_fields

    def _save_lead_fields(self, session, lead):
        # order sensitive, because form-data more important when tech data
        lead_fields = self._fill_lead_fields(session, lead)
        LeadField.objects.bulk_create(lead_fields.values())

    def _save_lead_url_labels(self, session, lead):
        """

        :param session: source session
        :type session: collector.models.SessionStorage
        :param lead:  target lead
        :type lead: collector.models.Lead
        :return: (collector.models.LeadUtm, collector.models.LeadOpenstat)
        :rtype: (collector.models.LeadUtm, collector.models.LeadOpenstat)
        """
        lead_utms = self._save_lead_url_label(LeadUtm, session.location, lead)
        if lead_utms is None:
            lead_utms = self._save_lead_url_label(LeadUtm, session.referrer, lead)

        lead_openstat = self._save_lead_url_label(LeadOpenstat, session.location, lead)
        if lead_openstat is None:
            lead_openstat = self._save_lead_url_label(LeadOpenstat, session.referrer, lead)

        return lead_utms, lead_openstat

    def _save_lead_url_label(self, modelClass, url, lead):
        lead_label = modelClass.parse_url(url)
        if lead_label:
            lead_label.lead = lead
            lead_label.save()
        return lead_label