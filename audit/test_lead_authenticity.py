import doctest
from unittest.mock import MagicMock

from django.test import TestCase

from audit import lead_authenticity
from audit.error import AuditError
from collector.models import FieldMapping, Lead
from collector.models.dictionaries import Field


def load_tests(loader, tests, ignore):
    tests.addTest(doctest.DocTestSuite(lead_authenticity))
    return tests


class LeadAuthenticityTestCase(TestCase):

    def test__parse_required_fields_should_return_empty_if_no_required_fields_mapping(self):
        res = sorted(lead_authenticity._parse_required_fields([], {}).items())
        self.assertEquals([], res)

    def test__parse_required_fields_should_raise_exception_if_need_req_field(self):
        req_fields_mapping = [
            FieldMapping(required=True, target_field=Field(id=3, name='email'))
        ]
        with self.assertRaises(AuditError) as cm:
            lead_authenticity._parse_required_fields(req_fields_mapping, {})
        self.assertEquals('Field "email" is required', str(cm.exception))

        req_fields_mapping = [
            FieldMapping(required=True, target_field=Field(id=3, name='email')),
            FieldMapping(required=True, target_field=Field(id=1, name='name'))
        ]
        with self.assertRaises(AuditError) as cm:
            lead_authenticity._parse_required_fields(req_fields_mapping, {'email': 'qwe@qwe.ru'})
        self.assertEquals('Field "name" is required', str(cm.exception))

        req_fields_mapping = [
            FieldMapping(required=True, target_field=Field(id=3, name='email')),
            FieldMapping(required=True, target_field=Field(id=1, name='name'))
        ]
        with self.assertRaises(AuditError) as cm:
            lead_authenticity._parse_required_fields(
                req_fields_mapping, {'email': 'qwe@qwe.ru', '111':'222'}
            )
        self.assertEquals('Field "name" is required', str(cm.exception))

    def test__parse_required_fields_should_return_only_required_fields(self):
        req_fields_mapping = [
            FieldMapping(required=True, target_field=Field(id=3, name='email')),
            FieldMapping(required=True, target_field=Field(id=1, name='name'))
        ]
        res = lead_authenticity._parse_required_fields(
            req_fields_mapping, {'email': 'qwe@qwe.ru', 'name': 'test', '111':'222'}
        )
        self.assertEquals([('email', 'qwe@qwe.ru'), ('name', 'test')], sorted(res.items()))

    def test__check_lead_authenticity_should_return_false_if_no_leads_found(self):
        check_fields = {'email': 'qwe@qwe.ru', 'name': 'test', '111':'222'}
        res = lead_authenticity._check_lead_authenticity([], check_fields)
        self.assertEquals((False,{}), res)

    def test__check_lead_authenticity_should_return_true_if_lead_found_and_fields_matched(self):
        check_fields = {'email': 'qwe@qwe.ru', 'name': 'test', '111':'222'}
        lead1 = Lead()
        lead1.fields_hash_map = MagicMock(return_value={
            'email': 'ab509c35c8d03398435cc9223a7e8c427cc08c76',
            'name': 'a94a8fe5ccb19ba61c4c0873d391e987982fbbd3',
            '111': '1c6637a8f2e1f75e06ff9984894d6bd16a3a36a9'
        })
        lead2 = Lead()
        lead2.fields_hash_map = MagicMock(return_value={
            'email': 'ab509c35c8d03398435cc9223a7e8c427cc08c76',
            'name': 'a94a8fe5ccb19ba61c4c0873d391e987982fbbd3',
            '111': '1c6637a8f2e1f75e06ff9984894d6bd16a3abbd3'
        })
        res = lead_authenticity._check_lead_authenticity([lead1, lead2], check_fields)
        self.assertEquals((True, {'111': True, 'email': True, 'name': True}), res)

        res = lead_authenticity._check_lead_authenticity([lead2, lead1], check_fields)
        self.assertEquals((True, {'111': True, 'email': True, 'name': True}), res)

    def test__check_lead_authenticity_should_return_false_if_lead_found_and_fields_not_matched(self):
        check_fields = {'email': 'qwe@qwe.ru', 'name': 'test', '111':'222'}
        lead1 = Lead()
        lead1.fields_hash_map = MagicMock(return_value={
            'email': 'ab509c35c8d03398435cc9223a7e8c427cc08c76',
            'name': 'a94a8fe5ccb19ba61c4c0873d391e987982fbbd3',
            '111': '1c6637a8f2e1f75e06ff9984894d6bd16a3abbd2'
        })
        lead2 = Lead()
        lead2.fields_hash_map = MagicMock(return_value={
            'email': 'ab509c35c8d03398435cc9223a7e8c427cc08c76',
            'name': 'a94a8fe5ccb19ba61c4c0873d391e987982fbbd3',
            '111': '1c6637a8f2e1f75e06ff9984894d6bd16a3abbd3'
        })
        res = lead_authenticity._check_lead_authenticity([lead1, lead2], check_fields)
        self.assertEquals((False, {'111': False, 'email': True, 'name': True}), res)

        res = lead_authenticity._check_lead_authenticity([lead2, lead1], check_fields)
        self.assertEquals((False, {'111': False, 'email': True, 'name': True}), res)

