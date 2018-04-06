import os

from datetime import timedelta
from django.utils import timezone
from logging import getLogger
from django.conf import settings
from django.core.management.base import BaseCommand

from utils.datetime import fromtimestamp

logger = getLogger(__name__)


class Command(BaseCommand):

    help = 'clear old ip_stat csv files'

    def handle(self, *args, **options):
        now = timezone.now()
        started = now
        if not os.path.exists(settings.META_STAT_ROOT):
            os.mkdir(settings.META_STAT_ROOT)
        deleted_count = 0
        for filename in os.listdir(settings.META_STAT_ROOT):
            if filename.startswith('meta_'):
                file = os.path.join(settings.META_STAT_ROOT, filename)
                stat = os.lstat(file)
                created_time = fromtimestamp(stat.st_ctime)
                if created_time < now - timedelta(days=30):
                    os.remove(file)
                    deleted_count += 1

        logger.info('Clear {} ip_stats files in {}s'.format(
            deleted_count, (timezone.now() - started).total_seconds()))
