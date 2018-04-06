import csv
import os
from datetime import timedelta, datetime, date, time
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.db.models.aggregates import Count, Sum, Avg
from django.db.models.expressions import ExpressionWrapper, F, Case, When
from django.db.models.fields import DurationField, UUIDField, TimeField
from django.db.models.functions.base import Coalesce, Cast
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db.transaction import atomic
from logging import getLogger

from collector.models.analytics import IpStat, Lead
from django.conf import settings
from profiles.models import Profile
from utils.datetime import strptime

logger = getLogger(__name__)

# all statistic we calc from this leads age
IP_STAT_MAX_PERIOD = timedelta(days=365)


class Command(BaseCommand):

    help = 'ip_stat table from leads data'

    def add_arguments(self, parser):
        parser.add_argument('--date', type=str, dest='fill_date')

    @atomic()
    def handle(self, fill_date=None, *args, **options):
        now = timezone.now()
        started = now
        if fill_date is None:
            fill_date = (now - timedelta(days=1)).date()
        else:
            fill_date = strptime(fill_date).date()

        IpStat.objects.filter(date=fill_date).delete()

        ip_stat_total = self._load_period_ipstat(fill_date, IP_STAT_MAX_PERIOD)
        ip_stat_30days = self._load_period_ipstat(fill_date, timedelta(days=30))
        ip_stat_10days = self._load_period_ipstat(fill_date, timedelta(days=10))
        ip_stat_3days = self._load_period_ipstat(fill_date, timedelta(days=3))

        res = {}
        res = self._collect_period_ipstat(res, fill_date, ip_stat_total, '')
        res = self._collect_period_ipstat(res, fill_date, ip_stat_30days, '30')
        res = self._collect_period_ipstat(res, fill_date, ip_stat_10days, '10')
        res = self._collect_period_ipstat(res, fill_date, ip_stat_3days, '3')
        if res:
            IpStat.objects.bulk_create(res.values())

        self._save_csv(res.values(), fill_date)

        logger.info('Fill {} ip_stats in {}s'.format(
            len(res), (timezone.now() - started).total_seconds()))

    @staticmethod
    def _load_period_ipstat(fill_date: date, period: timedelta):
        end_time = timezone.make_aware(time(hour=23, minute=59, second=59, microsecond=999999))
        end_date = datetime.combine(fill_date, end_time)
        start_date = (end_date - period).replace(hour=0, minute=0, second=0, microsecond=0)
        return Lead.objects \
            .filter(session_started__range=(start_date, end_date)) \
            .filter(ip_addr__isnull=False) \
            .values('ip_addr', 'geo', 'geo__country', 'geo__postal_code', 'provider') \
            .annotate(s_cnt=Count('id')) \
            .annotate(s_time=Sum(ExpressionWrapper(
                Coalesce('created', 'last_event_time') - F('session_started'),
                output_field=DurationField()))) \
            .annotate(s0_cnt=Count(Case(
                When(created__isnull=True, then=F('id')),
                default=None, output_field=UUIDField()))) \
            .annotate(s_beg=Cast(Avg(
                Cast(F('session_started'), output_field=TimeField())
            ), output_field=TimeField())) \
            .annotate(user_ids=ArrayAgg('pixel__project__user__id', distinct=True))\
            .annotate(cnt_dev=Count('device_id'))

    def _collect_period_ipstat(self, res, fill_date, period_ip_stat, suffix=''):

        cl_types = self._load_cl_types(period_ip_stat)

        for stat in period_ip_stat:
            if stat['ip_addr'] not in res:
                res[stat['ip_addr']] = self._init_ip_stat(fill_date, stat, cl_types)
            ip_stat = res[stat['ip_addr']]
            setattr(ip_stat, 's_cnt' + suffix, stat['s_cnt'] or 0)
            setattr(ip_stat, 's_time' + suffix, stat['s_time'] or timedelta(0))
            setattr(ip_stat, 's0_cnt' + suffix, stat['s0_cnt'] or 0)
            if hasattr(ip_stat, 's_beg' + suffix):
                setattr(ip_stat, 's_beg' + suffix, stat['s_beg'] or time(0))
            if hasattr(ip_stat, 'cnt_dev' + suffix):
                setattr(ip_stat, 'cnt_dev' + suffix, stat['cnt_dev'] or 0)
        return res

    @staticmethod
    def _load_cl_types(period_ip_stat):
        user_ids = set()
        for stat in period_ip_stat:
            user_ids.update(stat['user_ids'])
        if not user_ids:
            return {}
        cl_types = dict(
            Profile.objects.values_list('user_id', 'business').filter(user_id__in=tuple(user_ids))
        )
        return cl_types

    @staticmethod
    def _init_ip_stat(fill_date, stat, cl_types):
        ip_stat = IpStat()
        ip_stat.date = fill_date
        ip_stat.ip = stat['ip_addr']
        if len(stat['user_ids']) == 1:
            ip_stat.cl_type = cl_types.get(stat['user_ids'][0])
        else:
            ip_stat.cl_type = 'Others'
        ip_stat.country = stat['geo__country']
        ip_stat.city_id = stat['geo']
        ip_stat.index = stat['geo__postal_code']
        ip_stat.provider_id = stat['provider']
        # ip_state = None
        return ip_stat

    @staticmethod
    def _save_csv(ip_stats: list, fill_date: datetime):
        """
        :param ip_stats:
        :type ip_stats: [IpStat]
        :param fill_date:
        :return:
        """
        if not os.path.exists(settings.META_STAT_ROOT):
            os.mkdir(settings.META_STAT_ROOT)
        filename = os.path.join(
            settings.META_STAT_ROOT,
            'meta_{}.csv'.format(fill_date.strftime('%Y-%m-%d'))
        )
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            header = [
                'ip', 'cl_type',
                's_cnt', 's_time', 's0_cnt',
                's_cnt30', 's_time30', 's0_cnt30',
                's_cnt10', 's_time10', 's0_cnt10',
                's_cnt3', 's_time3', 's0_cnt3',
                's_beg30', 's_beg10', 's_beg3',
                'ip_state',
                'country', 'city', 'index', 'provider',
                'cnt_dev30', 'cnt_dev10', 'cnt_dev3'
            ]
            writer.writerow(header)

            for s in ip_stats:
                row = [
                    s.ip, s.cl_type,
                    s.s_cnt, s.s_time.total_seconds(), s.s0_cnt,
                    s.s_cnt30, s.s_time30.total_seconds(), s.s0_cnt30,
                    s.s_cnt10, s.s_time10.total_seconds(), s.s0_cnt10,
                    s.s_cnt3, s.s_time3.total_seconds(), s.s0_cnt3,
                    s.s_beg30.strftime("%H:%M:%S"),
                    s.s_beg10.strftime("%H:%M:%S"),
                    s.s_beg3.strftime("%H:%M:%S"),
                    s.ip_state,
                    s.country,
                    s.city.name if s.city else '',
                    s.index,
                    s.provider.asn if s.provider else '',
                    s.cnt_dev30, s.cnt_dev10, s.cnt_dev3
                ]
                writer.writerow(row)
