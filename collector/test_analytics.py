import doctest

from django.contrib.auth import get_user_model
from django.test import TestCase

import collector.analytics

User = get_user_model()


def load_tests(loader, tests, ignore):
    tests.addTest(doctest.DocTestSuite(collector.analytics))
    return tests

