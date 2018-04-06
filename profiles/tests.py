import doctest

from django.contrib.auth import get_user_model
from django.test import TestCase
import profiles.models
from condust.schema import schema
from profiles.forms import RegistrationForm
from django.contrib.auth.models import Group
from django.db.models import Q
from graphene.test import Client

from profiles.models import Profile

User = get_user_model()


def load_tests(loader, tests, ignore):
    tests.addTest(doctest.DocTestSuite(profiles.models))
    return tests


# Create your tests here.
class RegistrationFormTestCase(TestCase):

    def setUp(self):
        username = 'exist@user.com'
        self.exists_user = User.objects.create_user(username, email=username, password='123')

    def tearDown(self):
        self.exists_user.delete()

    def _assert_clean_phone_helper(self, exp_is_valid, phone):
        data = {
            'phone': phone,
            'company_name': 'Company name',
            'username': 'test@test.com',
            'password': '123',
            'agreement': '1'
        }
        form = RegistrationForm(data)
        self.assertEquals(exp_is_valid, form.is_valid())
        if exp_is_valid:
            self.assertEquals(data['phone'], form.cleaned_data['phone'])
        else:
            self.assertEquals('Incorrect phone number', form.errors['phone'][0])

    def test_clean_phone_should_pass_then_correct_format(self):
        phone = '+7(132)-687-13-12'
        self._assert_clean_phone_helper(True, phone)

    def test_clean_phone_should_pass_then_empty_phone(self):
        phone = ''
        self._assert_clean_phone_helper(True, phone)

    def test_clean_phone_should_not_pass_then_incorrect_format(self):
        phone = '(132)-687-13-12'
        self._assert_clean_phone_helper(False, phone)

    def test_clean_phone_should_not_pass_then_incorrect_format2(self):
        phone = '+7(132)687-13-12'
        self._assert_clean_phone_helper(False, phone)

    def _assert_clean_username(self, exp_is_valid, username):
        data = {
            'phone': '+7(132)-687-13-12',
            'company_name': 'Company name',
            'username': username,
            'password': '123',
            'agreement': '1'
        }
        form = RegistrationForm(data)
        self.assertEquals(exp_is_valid, form.is_valid())
        if exp_is_valid:
            self.assertEquals(data['username'], form.cleaned_data['username'])
        else:
            self.assertEquals('User with this email elaready exists', form.errors['username'][0])

    def test_clean_username_should_pass_then_user_not_in_db(self):
        username = 'test@test.com'
        self._assert_clean_username(True, username)

    def test_clean_username_should_raise_duplicate_then_user_exists(self):
        username = self.exists_user.username
        self._assert_clean_username(False, username)


class RegisterUserMutationTestCase(TestCase):

    def test_mutate_save_all_entities_in_db(self):
        client = Client(schema)
        executed = client.execute('''
            mutation registerUser($companyName: String!, $username: String!, $password: String!, $agreement: Boolean!, $name: String, $phone: String) {
              registerUser(companyName: $companyName, username: $username, password: $password, agreement: $agreement, name: $name, phone: $phone) {
                user {
                  username
                }
              }
            }
        ''', variable_values={
            'phone': '+7(132)-687-13-12',
            'companyName': 'Company name',
            'username': 'test@test.com',
            'name': 'Test Testovich',
            'password': '123',
            'agreement': '1'
        })
        self.assertEquals({
            'data': {
                'registerUser': {
                    'user': {
                        'username': 'test@test.com'
                    }
                }
            }
        }, executed)
        user = User.objects.get(username='test@test.com')
        self.assertEquals('Test', user.first_name)
        self.assertEquals('Testovich', user.last_name)
        self.assertEquals(False, user.is_active)
        profile = user.profile
        # profile = Profile.objects.get(user_id=user.id)
        self.assertEquals('Company name', profile.company_name)
        self.assertEquals('+7(132)-687-13-12', profile.phone)
        advertisers_group = Group.objects.get(name='advertisers')
        self.assertIn(advertisers_group, profile.user.groups)
        base_group = Group.objects.get(name='base')
        self.assertIn(base_group, profile.user.groups)
        self.assertEquals('advertiser', profile.status)
        self.assertEquals(4, len(profile.activation_code))
        self.assertEquals(
            profile.make_code_hash(profile.activation_code),
            profile.activation_code_hash
        )


class CheckProfileCreateOnUserCreate(TestCase):
    """
    In this test case we create new user and check if it has one_to_one field profile
    """

    def test_create_profile_on_user_create(self):
        username = 'test_profile@user.com'
        User.objects.create_user(username=username, email=username, password='admin123456')
        user = User.objects.get(username=username)
        self.assertNotEqual(None, user.profile)
