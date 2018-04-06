import doctest
from collections import namedtuple
from unittest import mock
from unittest.mock import MagicMock, call

from django.contrib.auth import get_user_model
from django.test import TestCase

from audit import lead_duplication
from audit.error import AuditError
from audit.models import Audit
from collector.models.analytics import Lead
from collector.models.dictionaries import Field
from collector.models.projects import Project, Pixel
from utils.datetime import strptime

User = get_user_model()


def load_tests(loader, tests, ignore):
    tests.addTest(doctest.DocTestSuite(lead_duplication))
    return tests


class ManyRelatedManagerHelper():

    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class LeadDuplicationTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None

    def __check_input_required_fieldset_fields_helper(self, exp, input_fields, fields=None):
        if fields is None:
            fields = [
                Field(id=3, name='email'),
                Field(id=1, name='name')
            ]
        self.assertEquals(
            exp,
            lead_duplication._check_input_required_fieldset_fields(input_fields, fields)
        )

    def test__check_input_required_fieldset_fields_pass_if_all_required_fields_set(self):
        input_fields = {'email': 'qwe@qwe.ru', 'name': 'test', '111':'222'}
        self.__check_input_required_fieldset_fields_helper(True, input_fields)

    def test__check_input_required_fieldset_fields_fail_if_not_all_required_fields_set(self):
        input_fields = {'name': 'test', '111':'222'}
        self.__check_input_required_fieldset_fields_helper(False, input_fields)

    def test__check_input_required_fieldset_fields_fail_if_no_required_fields_set(self):
        input_fields = {'111':'222'}
        fields = [ Field(id=3, name='email') ]
        self.__check_input_required_fieldset_fields_helper(False, input_fields, fields)

    def test__check_input_required_fieldsets_raise_error_if_no_fieldset_passed(self):
        lead_duplication._check_input_required_fieldset_fields = MagicMock(return_value=False)
        Fieldset = namedtuple('req_fieldset', ('fields',))
        fs1 = [Field(name='email'), Field(name='name')]
        fs2 = [Field(name='name'), Field(name='phone'), Field(name='address')]
        fieldsets = [
            Fieldset(fields=ManyRelatedManagerHelper(fs1)),
            Fieldset(fields=ManyRelatedManagerHelper(fs2))
        ]
        input_fields = {'111': '222'}
        with self.assertRaises(AuditError) as cm:
            res = lead_duplication._check_input_required_fieldsets(input_fields, fieldsets)
        self.assertEquals(
            'Need minimal required fields (email, name) or (name, phone, address)',
            str(cm.exception)
        )
        lead_duplication._check_input_required_fieldset_fields.assert_has_calls(
            [call(input_fields, fs1), call(input_fields, fs2)]
        )

    def _check_input_required_fieldsets_helper(self, input_fields, fs1, fs2, exp_calls, returns):
        lead_duplication._check_input_required_fieldset_fields = MagicMock(side_effect=returns)
        Fieldset = namedtuple('req_fieldset', ('fields',))
        fieldsets = [
            Fieldset(fields=ManyRelatedManagerHelper(fs1)),
            Fieldset(fields=ManyRelatedManagerHelper(fs2))
        ]
        res = lead_duplication._check_input_required_fieldsets(input_fields, fieldsets)
        self.assertEquals(input_fields, res)
        lead_duplication._check_input_required_fieldset_fields.assert_has_calls(exp_calls)


    def test__check_input_required_fieldsets_pass_first_fieldset(self):
        input_fields = {'email': 'qwe@qwe.ru', 'name': 'test', '111': '222'}
        fs1 = [Field(name='email'), Field(name='name')]
        fs2 = [Field(name='name'), Field(name='phone'), Field(name='address')]
        self._check_input_required_fieldsets_helper(
            input_fields,
            fs1, fs2,
            [call(input_fields, fs1)],
            [True, False]
        )

    def test__check_input_required_fieldsets_pass_second_fieldset(self):
        input_fields = {'email': 'qwe@qwe.ru', 'name': 'test', '111': '222'}
        fs1 = [Field(name='email'), Field(name='name')]
        fs2 = [Field(name='name'), Field(name='phone'), Field(name='address')]
        self._check_input_required_fieldsets_helper(
            input_fields,
            fs1, fs2,
            [call(input_fields, fs1), call(input_fields, fs2)],
            [False, True]
        )


    def test__check_lead_duplication_fail_if_no_leads_found(self):
        you = User(id=1)
        leads = []
        res = lead_duplication._check_lead_duplication(you, leads)
        self.assertEquals({
            'success': False,
            'resolution': 'Lead was sold to you outside the system',
            'created': None,
            'your_audits': [],
            'duplicates': [],
            'sales': []
        }, res)

    def test__check_lead_duplication_success_if_one_your_lead_found(self):
        you = User(id=1)
        your_project = Project(user=you)
        your_pixel = Pixel(project=your_project)
        leads = [
            Lead(pixel=your_pixel, created=strptime('2018-02-26'))
        ]
        res = lead_duplication._check_lead_duplication(you, leads)
        self.assertEquals({
            'success': True,
            'resolution': 'New lead',
            'created': strptime('2018-02-26'),
            'your_audits': [],
            'duplicates': [],
            'sales': []
        }, res)

    def test__check_lead_duplication_success_if_one_your_lead_found_and_audited_by_you(self):
        you = User(id=1)
        your_project = Project(user=you)
        your_pixel = Pixel(project=your_project)
        your_audit = Audit(processed=strptime('2018-02-27'), user=you)
        your_lead = Lead(pixel=your_pixel, created=strptime('2018-02-26'))
        with mock.patch('collector.models.analytics.Lead.audits') as mock_manager:
            mock_manager.all.return_value = [your_audit]
            leads = [
                your_lead
            ]
            res = lead_duplication._check_lead_duplication(you, leads)
            self.assertEquals({
                'success': True,
                'resolution': 'You already audited this lead 1 times',
                'created': strptime('2018-02-26'),
                'your_audits': [strptime('2018-02-27')],
                'duplicates': [],
                'sales': []
            }, res)


    def test__check_lead_duplication_fail_if_only_others_leads_found(self):
        you = User(id=1)
        someone = User(id=2)
        someone_project = Project(user=someone)
        someone_pixel = Pixel(project=someone_project)
        someone1_lead = Lead(pixel=someone_pixel, created=strptime('2018-02-25'))
        someone2_lead = Lead(pixel=someone_pixel, created=strptime('2018-02-26'))
        leads = [
            someone2_lead,
            someone1_lead,
        ]
        res = lead_duplication._check_lead_duplication(you, leads)
        self.assertEquals({
            'success': False,
            'resolution': 'Lead was sold to you outside the system',
            'created': None,
            'your_audits': [],
            'duplicates': [],
            'sales': [strptime('2018-02-26')]
        }, res)

    def test__check_lead_duplication_fail_if_only_your_leads_found(self):
        you = User(id=1)
        your_project = Project(user=you)
        your_pixel = Pixel(project=your_project)
        your_lead1 = Lead(pixel=your_pixel, created=strptime('2018-02-24'))
        your_lead2 = Lead(pixel=your_pixel, created=strptime('2018-02-25'))
        your_lead3 = Lead(pixel=your_pixel, created=strptime('2018-02-26'))
        leads = [
            your_lead1,
            your_lead2,
            your_lead3,
        ]
        res = lead_duplication._check_lead_duplication(you, leads)
        self.assertEquals({
            'success': False,
            'resolution': 'Lead has 2 duplicates',
            'created': strptime('2018-02-26'),
            'your_audits': [],
            'duplicates': [strptime('2018-02-25'), strptime('2018-02-24')],
            'sales': []
        }, res)

    def test__check_lead_duplication_fail_if_only_your_leads_found_and_audited_by_you(self):
        you = User(id=1)
        your_project = Project(user=you)
        your_pixel = Pixel(project=your_project)
        your_audit = Audit(processed=strptime('2018-02-27'), user=you)
        your_lead1 = Lead(pixel=your_pixel, created=strptime('2018-02-24'))
        your_lead2 = Lead(pixel=your_pixel, created=strptime('2018-02-25'))
        your_lead3 = Lead(pixel=your_pixel, created=strptime('2018-02-26'))
        with mock.patch('collector.models.analytics.Lead.audits') as mock_manager:
            mock_manager.all.return_value = [your_audit]
            leads = [
                your_lead1,
                your_lead2,
                your_lead3,
            ]
            res = lead_duplication._check_lead_duplication(you, leads)
            self.assertEquals({
                'success': False,
                'resolution': 'Lead has 2 duplicates',
                'created': strptime('2018-02-26'),
                'your_audits': [strptime('2018-02-27')],
                'duplicates': [strptime('2018-02-25'), strptime('2018-02-24')],
                'sales': []
            }, res)

    def test__check_lead_duplication_fail_if_your_leads_found_and_audited_by_other(self):
        you = User(id=1)
        your_project = Project(user=you)
        your_pixel = Pixel(project=your_project)
        someone = User(id=2)
        someone_audit1 = Audit(processed=strptime('2018-02-26'), user=someone)
        someone_audit2 = Audit(processed=strptime('2018-02-27'), user=someone)
        your_lead1 = Lead(pixel=your_pixel, created=strptime('2018-02-24'))
        your_lead2 = Lead(pixel=your_pixel, created=strptime('2018-02-25'))
        your_lead3 = Lead(pixel=your_pixel, created=strptime('2018-02-26'))
        with mock.patch('collector.models.analytics.Lead.audits') as mock_manager:
            mock_manager.all.return_value = [someone_audit1, someone_audit2]
            leads = [
                your_lead1,
                your_lead2,
                your_lead3,
            ]
            res = lead_duplication._check_lead_duplication(you, leads)
            self.assertEquals({
                'success': False,
                'resolution': 'Lead was sold 1 times',
                'created': strptime('2018-02-26'),
                'your_audits': [],
                'duplicates': [strptime('2018-02-25'), strptime('2018-02-24')],
                'sales': [strptime('2018-02-27')]
            }, res)

    def test__check_lead_duplication_fail_if_your_leads_found_and_audited_by_others(self):
        you = User(id=1)
        your_project = Project(user=you)
        your_pixel = Pixel(project=your_project)
        someone = User(id=2)
        sometwo = User(id=3)
        someone_audit1 = Audit(processed=strptime('2018-02-26'), user=someone)
        sometwo_audit2 = Audit(processed=strptime('2018-02-27'), user=sometwo)
        your_lead1 = Lead(pixel=your_pixel, created=strptime('2018-02-24'))
        your_lead2 = Lead(pixel=your_pixel, created=strptime('2018-02-25'))
        your_lead3 = Lead(pixel=your_pixel, created=strptime('2018-02-26'))
        with mock.patch('collector.models.analytics.Lead.audits') as mock_manager:
            mock_manager.all.return_value = [someone_audit1, sometwo_audit2]
            leads = [
                your_lead1,
                your_lead2,
                your_lead3,
            ]
            res = lead_duplication._check_lead_duplication(you, leads)
            self.assertEquals({
                'success': False,
                'resolution': 'Lead was sold 2 times',
                'created': strptime('2018-02-26'),
                'your_audits': [],
                'duplicates': [strptime('2018-02-25'), strptime('2018-02-24')],
                'sales': [strptime('2018-02-27'), strptime('2018-02-26')]
            }, res)

    def test__check_lead_duplication_fail_if_your_and_over_leads_found_and_audited_by_others(self):
        you = User(id=1)
        your_project = Project(user=you)
        your_pixel = Pixel(project=your_project)
        someone = User(id=2)
        someone_project = Project(user=someone)
        someone_pixel = Pixel(project=someone_project)
        sometwo = User(id=3)
        sometwo_audit2 = Audit(processed=strptime('2018-02-27'), user=sometwo)
        your_lead1 = Lead(pixel=your_pixel, created=strptime('2018-02-24'))
        someone_lead2 = Lead(pixel=someone_pixel, created=strptime('2018-02-25'))
        your_lead3 = Lead(pixel=your_pixel, created=strptime('2018-02-26'))
        with mock.patch('collector.models.analytics.Lead.audits') as mock_manager:
            mock_manager.all.return_value = [sometwo_audit2]
            leads = [
                your_lead1,
                someone_lead2,
                your_lead3,
            ]
            res = lead_duplication._check_lead_duplication(you, leads)
            self.assertEquals({
                'success': False,
                'resolution': 'Lead was sold 2 times',
                'created': strptime('2018-02-26'),
                'your_audits': [],
                'duplicates': [strptime('2018-02-24')],
                'sales': [strptime('2018-02-27'), strptime('2018-02-25')]
            }, res)

    def test__find_your_last_lead_none_if_no_your_leads(self):
        you = User(id=1)
        someone = User(id=2)
        someone_project = Project(user=someone)
        someone_pixel = Pixel(project=someone_project)
        someone_lead1 = Lead(pixel=someone_pixel, created=strptime('2018-02-24'))
        someone_lead2 = Lead(pixel=someone_pixel, created=strptime('2018-02-25'))
        leads = [
            someone_lead1,
            someone_lead2,
        ]
        yll = lead_duplication._find_your_last_lead(you, leads)
        self.assertIsNone(yll)

    def test__find_your_last_lead_return_yll_if_your_and_other_leads(self):
        you = User(id=1)
        your_project = Project(user=you)
        your_pixel = Pixel(project=your_project)
        someone = User(id=2)
        someone_project = Project(user=someone)
        someone_pixel = Pixel(project=someone_project)
        your_lead1 = Lead(pixel=your_pixel, created=strptime('2018-02-25'))
        your_lead2 = Lead(pixel=your_pixel, created=strptime('2018-02-24'))
        someone_lead1 = Lead(pixel=someone_pixel, created=strptime('2018-02-26'))
        leads = [
            your_lead1,
            someone_lead1,
            your_lead2,
        ]
        yll = lead_duplication._find_your_last_lead(you, leads)
        self.assertEquals(your_lead1, yll)

    def test__find_duplicates_exclude_yll_and_alien_leads(self):
        you = User(id=1)
        your_project = Project(user=you)
        your_pixel = Pixel(project=your_project)
        your_lead1 = Lead(pixel=your_pixel, created=strptime('2018-02-24'))
        your_lead2 = Lead(pixel=your_pixel, created=strptime('2018-02-25'))
        yll = Lead(pixel=your_pixel, created=strptime('2018-02-26'))
        someone = User(id=2)
        someone_project = Project(user=someone)
        someone_pixel = Pixel(project=someone_project)
        someone_lead1 = Lead(pixel=someone_pixel, created=strptime('2018-02-26'))
        leads = [
            your_lead2,
            yll,
            someone_lead1,
            your_lead1,
        ]
        duplicates = lead_duplication._find_duplicates(yll, leads)
        self.assertEquals([strptime('2018-02-25'), strptime('2018-02-24')], duplicates)


    def test_check_lead_duplication(self):
        you = User(id=1)
        input_fields = {'email': 'qwe@qwe.ru', 'name': 'test', '111': '222'}

        lead_duplication.check_input_fields = MagicMock(return_value=input_fields)
        lead_duplication._check_input_required_fieldsets = MagicMock(return_value=input_fields)
        lead_duplication._load_leads_by_fields = MagicMock(return_value='array of leads')
        lead_duplication._check_lead_duplication = MagicMock(return_value='some result')
        Audit.log = MagicMock(return_value=None)
        res = lead_duplication.check_lead_duplication(you, input_fields)
        lead_duplication.check_input_fields.assert_called_once_with(input_fields)
        lead_duplication._check_input_required_fieldsets.assert_called_once_with(input_fields)
        lead_duplication._load_leads_by_fields.assert_called_once_with(input_fields)
        lead_duplication._check_lead_duplication.assert_called_once_with(you, 'array of leads')
        Audit.log.assert_called_once_with(you, 'lead_duplication', input_fields, 'array of leads')
        self.assertEquals('some result', res)




