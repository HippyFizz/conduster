from django.core import management
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Reset and compile django .po and .mo files and compile their'

    def handle(self, *args, **options):
        opts = {
            'ignore': ['*venv/lib/*'],
            'all': True,
            'settings': 'condust.settings'
        }
        management.call_command("makemessages", **opts)
        # management.call_command("makemessages", all=True, domain='djangojs', **opts)
        management.call_command("compilemessages", settings='condust.settings')