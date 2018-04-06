import doctest

from django.test import TestCase
from collector.models import analytics


def load_tests(loader, tests, ignore):
    tests.addTest(doctest.DocTestSuite(analytics))
    return tests
