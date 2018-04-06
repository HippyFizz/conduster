import doctest

from django.test import TestCase
from utils import http


def load_tests(loader, tests, ignore):
    tests.addTest(doctest.DocTestSuite(http))
    return tests
