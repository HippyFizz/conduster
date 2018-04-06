from collections import OrderedDict

from django.template.defaultfilters import date as _date
from django.db.models.functions.base import Coalesce, Concat
from django.db.models.functions.datetime import TruncHour, TruncDay, TruncMonth, Trunc, TruncYear
from django.db.models import Q
from django.utils import timezone
from datetime import date, datetime, timedelta
from django.contrib.auth import get_user_model
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import When, Value, Case, F, ExpressionWrapper
from django.db.models.fields import CharField, DurationField
from django.utils.translation import ugettext as _, get_language

from collector.models import LEAD_AGE_GROUPS, Lead, LEAD_DURATION_GROUPS, CONSUMER_ORIGIN_GROUPS
from collector.models.analytics import LeadUtm, LeadOpenstat
from collector.models.dictionaries import DeviceType


User = get_user_model()


class AnalyticsError(Exception):
    pass


def total_visits(user: User, date_from: date, date_to: date,
                    projects: list = None,
                    label_type=None, label_values=None,
                    os_groups=None, browser_groups=None,
                    traffic_channels=None, now: datetime=None):
    """
    returns total leads count with session started or created in range
    :param user: User
    :param date_from: Date
    :param date_to: Date
    :param groups: List of String - filter by groups
    :param projects: List of String - filter by project ids
    :param label_type: type of url labels (utm | openstat)
    :param label_values: dict of url labels values
    :param now:
    :return:
    """
    leads_qs = Lead.objects.filter(pixel__project__user=user)
    leads_qs = leads_qs.filter(
        Q(session_started__range=(date_from, date_to)) | Q(created__range=(date_from, date_to))
    )
    if projects:
        leads_qs = leads_qs.filter(pixel__project__in=tuple(projects))
    if os_groups:
        leads_qs = leads_qs.filter(os_version__family__group__in=tuple(os_groups))
    if browser_groups:
        leads_qs = leads_qs.filter(browser__family__group__in=tuple(browser_groups))
    if traffic_channels:
        leads_qs = leads_qs.filter(traffic_channel__in=tuple(traffic_channels))
    leads_qs = _set_url_label_filter(leads_qs, label_type, label_values)
    return leads_qs.count()


def total_conversions(user: User, date_from: date, date_to: date,
                    projects: list = None,
                    label_type=None, label_values=None,
                    os_groups=None, browser_groups=None,
                    traffic_channels=None, now: datetime=None):
    """
    returns total leads count with created in range
    :param user: User
    :param date_from: Date
    :param date_to: Date
    :param groups: List of String - filter by groups
    :param projects: List of String - filter by project ids
    :param label_type: type of url labels (utm | openstat)
    :param label_values: dict of url labels values
    :param now:
    :return:
    """
    leads_qs = Lead.objects.filter(pixel__project__user=user)
    leads_qs = _apply_lead_common_filters(leads_qs, date_from, date_to, projects,
                                          label_type, label_values, os_groups,
                                          browser_groups, traffic_channels)
    return leads_qs.count()


def total_devices(user: User, date_from: date, date_to: date,
                    projects: list = None,
                    label_type=None, label_values=None,
                    os_groups=None, browser_groups=None,
                    traffic_channels=None, now: datetime=None):
    """
    returns total leads count with created in range
    :param user: User
    :param date_from: Date
    :param date_to: Date
    :param groups: List of String - filter by groups
    :param projects: List of String - filter by project ids
    :param label_type: type of url labels (utm | openstat)
    :param label_values: dict of url labels values
    :param now:
    :return:
    """
    leads_qs = Lead.objects.filter(pixel__project__user=user)
    leads_qs = _apply_lead_common_filters(leads_qs, date_from, date_to, projects,
                                          label_type, label_values, os_groups,
                                          browser_groups, traffic_channels)
    return leads_qs.aggregate(Count('device_id',distinct=True)).get('device_id__count')


def _lead_age_boundary(now, seconds):
    """
    :param now: dateime
    :param seconds: int
    :return: datetime - boundary for lead age group
    """
    return now - timedelta(seconds=seconds)


def _lead_age_groups_case(groups: list = None, now: datetime = None):
    """
    returns Case object for time groups
    Case (
        when created__range=(5,30), then='5 to 30 mins'
        when created__range=(1,4), then='1 to 4 hours'
        ...
        default='Others'
    )
    :param groups:
    :param now:
    :return:
    """
    if now is None:
        now = timezone.now()
    if not groups:
        groups = LEAD_AGE_GROUPS.keys();

    group_whens = []
    for group_id in groups:
        try:
            group = LEAD_AGE_GROUPS[group_id]
        except KeyError:
            raise AnalyticsError(_('Invalid group parameter'))
        if group.operator == 'range':
            expr_value = (_lead_age_boundary(now, group.val1), _lead_age_boundary(now, group.val2))
        else:
            expr_value = _lead_age_boundary(now, group.val1)
        group_whens.append(
            When(**{'created__' + group.operator: expr_value, 'then': Value(group_id)})
        )

    return Case(*group_whens, default=Value('Others'), output_field=CharField())


def _apply_lead_common_filters(leads_qs, date_from: date, date_to: date,
                               projects: list = None, label_type=None, label_values=None,
                               os_groups=None, browser_groups=None, traffic_channels=None):
    leads_qs = leads_qs.filter(created__range=(date_from, date_to))
    if projects:
        leads_qs = leads_qs.filter(pixel__project__in=tuple(projects))
    if os_groups:
        leads_qs = leads_qs.filter(os_version__family__group__in=tuple(os_groups))
    if browser_groups:
        leads_qs = leads_qs.filter(browser__family__group__in=tuple(browser_groups))
    if traffic_channels:
        leads_qs = leads_qs.filter(traffic_channel__in=tuple(traffic_channels))
    leads_qs = _set_url_label_filter(leads_qs, label_type, label_values)
    return leads_qs


def lead_age_totals(user: User, date_from: date, date_to: date,
                    groups: list = None, projects: list = None,
                    label_type=None, label_values=None,
                    os_groups=None, browser_groups=None,
                    traffic_channels=None, now: datetime=None):
    """
    returns data for piechart of lead_age
    :param user: User
    :param date_from: Date
    :param date_to: Date
    :param groups: List of String - filter by groups
    :param projects: List of String - filter by project ids
    :param label_type: type of url labels (utm | openstat)
    :param label_values: dict of url labels values
    :param now:
    :return:
    """
    leads_qs = Lead.objects.filter(pixel__project__user=user)
    leads_qs = _apply_lead_common_filters(leads_qs, date_from, date_to, projects,
                                          label_type, label_values, os_groups,
                                          browser_groups, traffic_channels)
    leads_qs = leads_qs.annotate(
        group_name=_lead_age_groups_case(groups, now)
    ).values('group_name').annotate(leads_count=Count('id'))
    return leads_qs


def _set_url_label_filter(leads_qs, label_type, label_values):
    if label_type and label_values:
        label_filter = _get_url_label_filter(label_type, label_values)
        if label_filter:
            leads_qs = leads_qs.filter(**label_filter)
    return leads_qs


def _get_url_label_filter(label_type, label_values):
    if label_type not in ['utm', 'openstat']:
        return None
    label_type_fields = {
        'utm': ('utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'),
        'openstat': ('service', 'campaign', 'ad', 'source')
    }
    label_names = label_type_fields[label_type]
    for label_name, label_value in label_values.items():
        if label_name not in label_names:
            return None

    label_filter = {}
    for label_name, label_value in label_values.items():
        label_filter[label_type + '__' + label_name + '__iexact'] = label_value
    return label_filter


def _leads_period_unit_expr(period):
    """
    :param period: - 'hour', 'day', 'week', 'moth', 'year'
    :param date_to:
    :return:
    >>> _leads_period_unit_expr('hour')
    TruncHour(F(created))
    >>> _leads_period_unit_expr('day')
    TruncDay(F(created))
    >>> _leads_period_unit_expr('week')
    Trunc(F(created))
    >>> _leads_period_unit_expr('month')
    TruncMonth(F(created))
    >>> _leads_period_unit_expr('year')
    TruncYear(F(created))
    """
    if period == 'hour':
        return TruncHour('created')
    elif period == 'day':
        return TruncDay('created')
    elif period == 'week':
        return Trunc('created', 'week')
    elif period == 'month':
        return TruncMonth('created')
    else:
        return TruncYear('created')


def format_leads_period(lead_date: datetime, period):
    """
    format leads period
    :param lead_date: - scale period begining date
    :param period: - 'hour', 'day', 'week', 'moth', 'year'
    :return:
    >>> format_leads_period(datetime(2017, 1, 1, 2), 'hour')
    '01, 02'
    >>> format_leads_period(datetime(2017, 1, 1), 'day')
    '01 Jan.'
    >>> format_leads_period(datetime(2017, 1, 1), 'week')
    '26 Dec. - 01 Jan.'
    >>> format_leads_period(datetime(2017, 1, 2), 'week')
    '02-08 Jan.'
    >>> format_leads_period(datetime(2017, 1, 1), 'month')
    'Jan. 2017'
    >>> format_leads_period(datetime(2017, 1, 1), 'year')
    '2017'
    """
    if period == 'hour':
        created_format =  'd, H'
    elif period == 'day':
        created_format = 'd N'
    elif period == 'week':
        created_format = 'd N'
        date_start = lead_date - timedelta(days=lead_date.weekday())
        date_end = date_start + timedelta(days=6)
        month_start = _date(date_start, 'N')
        month_end = _date(date_end, 'N')
        if month_start == month_end:
            day_start = _date(date_start, 'd')
            day_end = _date(date_end, 'd')
            return '{}-{} {}'.format(day_start, day_end, month_start)
        return '{} - {}'.format(_date(date_start, created_format), _date(date_end, created_format))
    elif period == 'month':
        created_format = 'N Y'
    else:
        created_format = 'Y'
    return _date(lead_date, created_format)


def get_scale_period(date_from: date, date_to: date):
    """
    :param date_from:
    :param date_to:
    :return:
    >>> get_scale_period(datetime(2017, 1, 1), datetime(2017, 1, 1, 23, 59, 59))
    'hour'
    >>> get_scale_period(datetime(2017, 1, 1), datetime(2017, 1, 3))
    'day'
    >>> get_scale_period(datetime(2017, 1, 1), datetime(2017, 1, 31, 23, 59, 59))
    'day'
    >>> get_scale_period(datetime(2017, 1, 1), datetime(2017, 2, 1, 23, 59, 59))
    'week'
    >>> get_scale_period(datetime(2017, 1, 1), datetime(2017, 3, 31, 23, 59, 59))
    'week'
    >>> get_scale_period(datetime(2017, 1, 1), datetime(2017, 4, 5, 23, 59, 59))
    'month'
    >>> get_scale_period(datetime(2017, 1, 1), datetime(2019, 12, 31, 23, 59, 59))
    'month'
    >>> get_scale_period(datetime(2017, 1, 1), datetime(2020, 1, 1, 23, 59, 59))
    'year'

    """
    period = date_to - date_from
    if period <= timedelta(days=1):
        return 'hour'
    elif period <= timedelta(days=31):
        return 'day'
    elif period <= timedelta(days=92):
        return 'week'
    elif period <= timedelta(days=3 * 365):
        return 'month'
    else:
        return 'year'


def get_leads(user: User, date_from: date, date_to: date, projects: list = None,
              label_type=None, label_values=None, os_groups=None, browser_groups=None,
              traffic_channels=None):
    leads_qs = Lead.objects.filter(pixel__project__user=user)
    leads_qs = _apply_lead_common_filters(leads_qs, date_from, date_to, projects,
                                          label_type, label_values, os_groups,
                                          browser_groups, traffic_channels)
    leads_qs = leads_qs.order_by('-created')
    leads_qs = leads_qs.annotate(os_group=F('os_version__family__group__name'))
    device_types = dict(DeviceType.TYPES)
    leads_qs = leads_qs.annotate(
        device=Concat(
            Case(
                When(
                    device_model__device_type__category=DeviceType.PHONE,
                    then=Value(str(device_types[DeviceType.PHONE]))
                ),
                When(
                    device_model__device_type__category=DeviceType.TABLET,
                    then=Value(str(device_types[DeviceType.TABLET]))
                ),
                When(
                    device_model__device_type__category=DeviceType.DESKTOP,
                    then=Value(str(device_types[DeviceType.DESKTOP]))
                ),
                default=Value('Unknown')
            ),
            Value(' '),
            F('device_model__brand__name'), Value(' '),
            F('device_model__model')
        )
    )
    cur_language = get_language()
    if cur_language == 'ru-ru':
        leads_qs = leads_qs.annotate(city=Coalesce(
            Case(
                When(geo__name_ru__exact='', then=None),
                When(geo__name_ru__isnull=False, then='geo__name_ru'),
                default=None
            ), F('geo__name')
        ))
    else:
        leads_qs = leads_qs.annotate(city=F('geo__name'))
    leads_qs = leads_qs.select_related('geo')
    return leads_qs


def leads_by_period(user: User, date_from: date, date_to: date, projects: list = None,
                    label_type=None, label_values=None, os_groups=None, browser_groups=None,
                    traffic_channels=None):
    leads_qs = Lead.objects.filter(pixel__project__user=user)
    leads_qs = _apply_lead_common_filters(leads_qs, date_from, date_to, projects,
                                          label_type, label_values, os_groups,
                                          browser_groups, traffic_channels)
    scale_period = get_scale_period(date_from, date_to)
    leads_qs = leads_qs.annotate(
        created_period= _leads_period_unit_expr(scale_period)
    ).values('created_period').annotate(leads_count=Count('id')).order_by('created_period')

    return leads_qs


def _lead_duration_groups_case(groups=None):
    """
    returns Case object for time groups
    Case (
        when lead_duration__range=(5,30), then='5 to 30 mins'
        when lead_duration__range=(1,4), then='1 to 4 hours'
        ...
        default='Others'
    )
    :param groups:
    :param now:
    :return:
    """
    if not groups:
        groups = LEAD_DURATION_GROUPS.keys();

    group_whens = []
    for group_id in groups:
        try:
            group = LEAD_DURATION_GROUPS[group_id]
        except KeyError:
            raise AnalyticsError(_('Invalid group parameter'))
        if group.operator == 'range':
            expr_value = (timedelta(seconds=group.val1), timedelta(seconds=group.val2))
        else:
            expr_value = timedelta(seconds=group.val1)
        group_whens.append(
            When(**{'lead_duration__' + group.operator: expr_value, 'then': Value(group_id)})
        )
    return Case(*group_whens, default=Value('Others'), output_field=CharField())


def lead_duration_by_period(user: User, date_from: date, date_to: date,
                            groups: list = None, projects: list = None,
                            label_type=None, label_values=None, os_groups=None, browser_groups=None,
                            traffic_channels=None):
    leads_qs = Lead.objects.filter(pixel__project__user=user)
    leads_qs = _apply_lead_common_filters(leads_qs, date_from, date_to, projects,
                                          label_type, label_values, os_groups,
                                          browser_groups, traffic_channels)
    leads_qs = leads_qs.annotate(lead_duration=ExpressionWrapper(
        F('created') - F('session_started'), output_field=DurationField()
    ))
    leads_qs = leads_qs.annotate(group_name=_lead_duration_groups_case())
    if groups:
        leads_qs = leads_qs.filter(group_name__in=groups)
    scale_period = get_scale_period(date_from, date_to)
    leads_qs = leads_qs.annotate(created_period=_leads_period_unit_expr(scale_period))
    leads_qs = leads_qs.values('group_name', 'created_period')
    leads_qs = leads_qs.annotate(leads_count=Count('id'))
    leads_qs = leads_qs.order_by('created_period', 'group_name')
    return leads_qs


def lead_duration_totals(user: User, date_from: date, date_to: date,
                         groups: list = None, projects: list = None,
                         label_type=None, label_values=None, os_groups=None, browser_groups=None,
                         traffic_channels=None):
    leads_qs = Lead.objects.filter(pixel__project__user=user)
    leads_qs = leads_qs.filter(created__range=(date_from, date_to))
    leads_qs = _apply_lead_common_filters(leads_qs, date_from, date_to, projects,
                                          label_type, label_values, os_groups,
                                          browser_groups, traffic_channels)
    leads_qs = leads_qs.annotate(lead_duration=ExpressionWrapper(
        F('created') - F('session_started'), output_field=DurationField()
    ))
    leads_qs = leads_qs.annotate(group_name=_lead_duration_groups_case(groups))
    leads_qs = leads_qs.values('group_name')
    leads_qs = leads_qs.annotate(leads_count=Count('id'))
    leads_qs = leads_qs.order_by('group_name')
    return leads_qs


def consumer_origin_by_period(user: User, date_from: date, date_to: date,
                              groups: list = None, projects: list = None,
                              device_field='device_id',
                              label_type=None, label_values=None, os_groups=None,
                              browser_groups=None, traffic_channels=None):
    leads_qs = Lead.objects.filter(pixel__project__user=user)
    leads_qs = _apply_lead_common_filters(leads_qs, date_from, date_to, projects,
                                          label_type, label_values, os_groups,
                                          browser_groups, traffic_channels)
    leads_qs = leads_qs.annotate(created_date=TruncDay('created'))
    leads_qs = leads_qs.order_by('created')

    groups_by_dates = _collect_device_frequency_groups_by_dates(leads_qs, groups, device_field)
    scale_period = get_scale_period(date_from, date_to)
    return _collect_device_frequerncy_groups_by_period(groups_by_dates, scale_period)


def _collect_device_frequency_groups_by_dates(leads, groups=None, device_field='device_id'):
    """
    group leads to sections (5min,1hour...) per date
    and count sum of device_frequency for each section
    :param leads: leads from db
    :type leads: collections.Iterable
    :rtype: collections.OrderedDict
    :return: {created_date: { section_name: {'device_last' : {}, 'device_frequency': 0}}}
    """
    if not groups:
        groups = CONSUMER_ORIGIN_GROUPS.keys()

    res = OrderedDict()
    for lead in leads:
        device = getattr(lead, device_field)
        if lead.created_date not in res:
            res[lead.created_date] = {}
        res_date = res[lead.created_date]
        for group_name in groups:
            try:
                group = CONSUMER_ORIGIN_GROUPS[group_name]
            except KeyError:
                raise AnalyticsError(_('Invalid group parameter'))
            if group_name not in res_date:
                res_date[group_name] = {'device_last': {}, 'device_frequency': 0}
            section = res_date[group_name]
            if device in section['device_last'] \
                    and lead.created - section['device_last'][device] < group.delta:
                section['device_frequency'] += 1 if section['device_frequency'] else 2
            section['device_last'][device] = lead.created
    return res


def _collect_device_frequerncy_groups_by_period(groups_by_dates, scale_period):
    groups_by_period = OrderedDict()
    for created_date, sections in groups_by_dates.items():
        created_period = format_leads_period(created_date, scale_period)
        if created_period not in groups_by_period:
            groups_by_period[created_period] = {}
        for group_name, section in sections.items():
            if group_name not in groups_by_period[created_period]:
                groups_by_period[created_period][group_name] = 0
            groups_by_period[created_period][group_name] += section['device_frequency']
    return groups_by_period


def load_url_label_list(user, label_type, label_name, search):
    model_class = None
    field_name = None
    if label_type == 'utm':
        model_class = LeadUtm
        if label_name in ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']:
            field_name = label_name
    elif label_type == 'openstat':
        model_class = LeadOpenstat
        if label_name in ['service', 'campaign', 'ad', 'source']:
            field_name = label_name
    if model_class is None or field_name is None:
        return []
    qs = model_class.objects.filter(lead__pixel__project__user=user)
    qs = qs.exclude(**{field_name + '__isnull': True})
    qs = qs.exclude(**{field_name + '': ''})
    if search and len(search) >= 2:
        qs = qs.filter(**{field_name + '__istartswith': search})
    qs = qs.values_list(field_name, flat=True).distinct()
    qs = qs.order_by(field_name)
    return qs


def your_lead_lineage_by_period(user: User, date_from: date, date_to: date, projects: list = None,
                           label_type=None, label_values=None, os_groups=None,
                           browser_groups=None, traffic_channels=None):
    your_leads_qs = Lead.objects.filter(pixel__project__user=user)
    your_leads_qs = _apply_lead_common_filters(your_leads_qs, date_from, date_to, projects,
                                               label_type, label_values, os_groups,
                                               browser_groups, traffic_channels)
    your_leads_qs = _apply_lineage_qs(your_leads_qs, date_from, date_to)
    your_leads_qs = your_leads_qs.annotate(lead_type=Value('your', output_field=CharField()))
    return your_leads_qs


def other_lead_lineage_by_period(user: User, date_from: date, date_to: date,
                           label_type=None, label_values=None, os_groups=None,
                           browser_groups=None, traffic_channels=None):
    other_leads_qs = Lead.objects.exclude(pixel__project__user=user)
    other_leads_qs = _apply_lead_common_filters(other_leads_qs, date_from, date_to, None,
                                                label_type, label_values, os_groups,
                                                browser_groups, traffic_channels)
    other_leads_qs = _apply_lineage_qs(other_leads_qs, date_from, date_to)
    other_leads_qs = other_leads_qs.annotate(lead_type=Value('other', output_field=CharField()))
    return other_leads_qs



def _apply_lineage_qs(leads_qs, date_from, date_to):
    scale_period = get_scale_period(date_from, date_to)
    leads_qs = leads_qs.annotate(created_period=_leads_period_unit_expr(scale_period))
    leads_qs = leads_qs.values('created_period')
    leads_qs = leads_qs.annotate(leads_count=Count('id'))
    leads_qs = leads_qs.annotate(sales_count=Sum('metrik_lead_salecount'))
    # other_leads_qs = other_leads_qs.annotate(avg_sales_count=ExpressionWrapper(
    #     Sum('metrik_lead_salecount') / Count('id'), output_field=FloatField()
    # ))
    leads_qs = leads_qs.order_by('created_period')
    return leads_qs


def lead_browser_totals(user: User, date_from: date, date_to: date,
                         projects: list = None, label_type=None, label_values=None,
                         os_groups=None, browser_groups=None, traffic_channels=None):
    leads_qs = Lead.objects.filter(pixel__project__user=user)
    leads_qs = _apply_lead_common_filters(leads_qs, date_from, date_to, projects,
                                          label_type, label_values, os_groups,
                                          browser_groups, traffic_channels)
    leads_qs = leads_qs.annotate(
        group_name=Coalesce(F('browser__family__group__name'), Value(_('Unknown')))
    )
    leads_qs = leads_qs.values('group_name')
    leads_qs = leads_qs.annotate(leads_count=Count('id'))
    leads_qs = leads_qs.order_by('group_name')
    return leads_qs


def lead_device_type_totals(user: User, date_from: date, date_to: date,
                         projects: list = None, label_type=None, label_values=None,
                         os_groups=None, browser_groups=None, traffic_channels=None):
    leads_qs = Lead.objects.filter(pixel__project__user=user)
    leads_qs = _apply_lead_common_filters(leads_qs, date_from, date_to, projects,
                                          label_type, label_values, os_groups,
                                          browser_groups, traffic_channels)
    leads_qs = leads_qs.annotate(lead_duration=ExpressionWrapper(
        F('created') - F('session_started'), output_field=DurationField()
    ))
    leads_qs = leads_qs.annotate(group_name=Case(
        When(device_model__device_type__category__in=(DeviceType.PHONE,DeviceType.TABLET),
             then=Value('Mobile')),
        When(device_model__device_type__category=(DeviceType.DESKTOP),
             then=Value('Desktop')),
        default=Value(_('Unknown')),
        output_field=CharField()
    ))
    leads_qs = leads_qs.values('group_name')
    leads_qs = leads_qs.annotate(leads_count=Count('id'))
    leads_qs = leads_qs.order_by('group_name')
    return leads_qs


def lead_os_totals(user: User, date_from: date, date_to: date, is_mobile,
                         projects: list = None, label_type=None, label_values=None,
                         os_groups=None, browser_groups=None, traffic_channels=None):
    leads_qs = Lead.objects.filter(pixel__project__user=user)
    leads_qs = _apply_lead_common_filters(leads_qs, date_from, date_to, projects,
                                          label_type, label_values, os_groups,
                                          browser_groups, traffic_channels)
    leads_qs = leads_qs.filter(os_version__family__group__is_mobile=is_mobile)
    leads_qs = leads_qs.annotate(lead_duration=ExpressionWrapper(
        F('created') - F('session_started'), output_field=DurationField()
    ))
    leads_qs = leads_qs.annotate(
        group_name=Coalesce(F('os_version__family__group__name'), Value(_('Unknown')))
    )
    leads_qs = leads_qs.values('group_name')
    leads_qs = leads_qs.annotate(leads_count=Count('id'))
    leads_qs = leads_qs.order_by('group_name')
    return leads_qs
