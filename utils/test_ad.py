import doctest

from django.test import TestCase
from utils import ad


def load_tests(loader, tests, ignore):
    tests.addTest(doctest.DocTestSuite(ad))
    return tests
