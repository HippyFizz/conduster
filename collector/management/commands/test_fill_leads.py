import uuid
from unittest.mock import MagicMock

from django.test import TestCase

from collector.management.commands import fill_leads
from collector.models import Lead, Event, FieldMapping, SessionStorage, Pixel
from collector.models.dictionaries import Field
from utils.datetime import strptime


class FileLeadsTestCase(TestCase):

    fixtures = [
        'pixel_session_event.json'
    ]

    def setUp(self):
        pass
        # username = 'exist@user.com'
        # self.exists_user = User.objects.create_user(username, email=username, password='123')

    def tearDown(self):
        pass
        # self.exists_user.delete()

    def test__load_session_ids_must_return_session_with_5_minutes_events_old(self):
        # in db we have session with last event "2018-01-18T09:43:.."
        now = strptime('2018-01-18 09:45', '%Y-%m-%d %H:%M')
        cmd = fill_leads.Command()
        session_ids = list(cmd._load_session_ids(now))
        self.assertEquals([uuid.UUID('99a9086a-94b7-4807-a1a6-67614b8afaec')], session_ids)

    def test__load_session_ids_must_not_return_session_with_events_older_than_5_minutes(self):
        # in db we have session with last event "2018-01-18T09:43"
        now = strptime('2018-01-18 09:49', '%Y-%m-%d %H:%M')
        cmd = fill_leads.Command()
        session_ids = list(cmd._load_session_ids(now))
        self.assertEquals([], session_ids)

    def test__load_session_ids_must_return_session_with_events_between_from_and_to(self):
        # in db we have session with last event "2018-01-18T09:43:.."
        now = strptime('2018-01-19 09:50', '%Y-%m-%d %H:%M')
        cmd = fill_leads.Command()
        session_ids = list(cmd._load_session_ids(now, '2018-01-18', '2018-01-18'))
        self.assertEquals([uuid.UUID('99a9086a-94b7-4807-a1a6-67614b8afaec')], session_ids)

    def test__load_session_ids_must_not_return_session_without_events_between_from_and_to(self):
        # in db we have session with last event "2018-01-18T09:43:.."
        now = strptime('2018-01-18 09:45', '%Y-%m-%d %H:%M')
        cmd = fill_leads.Command()
        session_ids = list(cmd._load_session_ids(now, '2017-01-17', '2017-01-18'))
        self.assertEquals([], session_ids)

    # 2. _fill_form_fields на то что самые главные поля с fields mapping не перетираются
    def test__fill_form_fields_do_not_override_fieldsMappingData_and_FormData_from_techData(self):
        fields_mapping = [
            FieldMapping(
                target_field=Field.objects.get(id=3), required=True, html_tag='input',
                html_attr_name='name', html_attr_value='email',
            ),
            FieldMapping(
                target_field=Field.objects.get(id=1), required=True, html_tag='input',
                html_attr_name='name', html_attr_value='username'
            ),
            FieldMapping(
                target_field=Field.objects.get(id=6), required=False, html_tag='input',
                html_attr_name='id', html_attr_value='id-middle-name'
            )
        ]
        fill_leads.Command._load_pixel_fields_mapping = MagicMock(return_value=fields_mapping)

        events = [
            Event(event_type='field-filled', field_tag='input', field_name='email', hash_data='last@email.ru'),
            Event(event_type='field-filled', field_tag='input', field_name='username', hash_data='username'),
            Event(event_type='field-filled', field_tag='input', field_name='name', hash_data='other-name'),
            Event(event_type='field-filled', field_tag='input', field_id = 'id-middle-name', field_name='middle-name', hash_data='form-middle-name'),
            Event(event_type='field-filled', field_tag='input', field_name='name', hash_data='usern'),
            Event(event_type='field-filled', field_tag='input', field_name='ip', hash_data='ip-from-events'),
        ]
        fill_leads.Command._load_session_events = MagicMock(return_value=events)
        session_id = 'session_id'
        session = SessionStorage(id=session_id, ip_addr='ip-from-tech-data', domain='tech-domain')
        session.pixel = Pixel()
        lead = Lead(id=session_id)
        lead.pixel = Pixel()
        cmd = fill_leads.Command()
        res = cmd._fill_lead_fields(session, lead)

        self.assertEquals('last@email.ru', res['email'].field_hash)
        self.assertEquals('username', res['name'].field_hash)
        self.assertEquals('username', res['username'].field_hash)
        self.assertEquals('form-middle-name', res['middle-name'].field_hash)
        self.assertEquals('ip-from-events', res['ip'].field_hash)
        self.assertEquals('tech-domain', res['domain'].field_data)

    # 3. _get_session_form_data на оставление только последних евентов
    def test__get_session_form_data_leave_only_last_events(self):
        """
        events already sorted on -finished
        :return:
        """
        session = None
        events = [
            Event(event_type='form-submitted', field_name='', open_data='submit'),
            Event(event_type='field-filled', field_name='email', open_data='last@email.ru'),
            Event(event_type='field-filled', field_name='name', open_data='username'),
            Event(event_type='field-filled', field_name='email', open_data='l'),
            Event(event_type='field-filled', field_name='name', open_data='usern'),
        ]
        fill_leads.Command._load_session_events = MagicMock(return_value=events)
        cmd = fill_leads.Command()
        res = cmd._get_session_form_data(session)
        res = sorted([(v.event_type, v.field_name, v.open_data) for k, v in res.items()])
        exp = [('field-filled', 'email', 'last@email.ru'), ('field-filled', 'name', 'username')]
        self.assertEquals(exp, res)

    # 3. _get_session_form_data на оставление только последних евентов
    def test___save_lead_url_labels(self):
        """
        events already sorted on -finished
        :return:
        """
        session = SessionStorage.objects.get(id='99a9086a-94b7-4807-a1a6-67614b8afaec')
        lead = Lead.objects.get(id='99a9086a-94b7-4807-a1a6-67614b8afaec')
        cmd = fill_leads.Command()
        lead_utms, lead_openstat = cmd._save_lead_url_labels(session, lead)
        self.assertEquals('utm-source-from-location', lead_utms.utm_source)
        self.assertEquals('openstat-service-from-referrer', lead_openstat.service)
