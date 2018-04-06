import graphene
from django.utils.translation import ugettext as _
from graphene_django.types import DjangoObjectType

from collector.models import LEAD_AGE_GROUPS, LEAD_DURATION_GROUPS, CONSUMER_ORIGIN_GROUPS
from collector.analytics import lead_age_totals, leads_by_period, format_leads_period, \
    lead_duration_by_period, lead_duration_totals, consumer_origin_by_period, load_url_label_list, \
    get_leads, lead_browser_totals, lead_device_type_totals, lead_os_totals, \
    your_lead_lineage_by_period, other_lead_lineage_by_period, \
    total_visits, total_conversions, total_devices, get_scale_period
from collector.models.dictionaries import OSGroup, BrowserGroup, TrafficChannel
from collector.models.analytics import Lead
from utils.graphene import JSONDict


class LeadsGroup(graphene.ObjectType):
    group_name = graphene.String()
    group_title = graphene.String()
    leads_count = graphene.Int()


class LeadsPeriod(graphene.ObjectType):
    created = graphene.String()
    leads_count = graphene.Int()


class LeadsPeriodGroup(LeadsPeriod, LeadsGroup):
    pass


class SalesPeriodGroup(LeadsPeriod, LeadsGroup):
    leads_count = graphene.Float()


def _resolve_groups(info, groups_const):
    groups = []
    for group_id, group in groups_const.items():
        groups.append(LeadsGroup(
            group_name=group_id,
            group_title=group.title
        ))
    return groups


class OSGroupType(DjangoObjectType):
    class Meta:
        model = OSGroup


class BrowserGroupType(DjangoObjectType):
    class Meta:
        model = BrowserGroup


class SimpleNode(graphene.relay.Node):
    @staticmethod
    def to_global_id(type, id):
        return id


class LeadType(DjangoObjectType):
    os_group = graphene.String()
    device = graphene.String()
    city = graphene.String()
    country = graphene.String()
    class Meta:
        model = Lead
        only_fields = (
            'id', 'created', 'session_started',
            'pixel', 'os_group', 'device', 'city', 'country')



class TrafficChannelType(DjangoObjectType):
    class Meta:
        model = TrafficChannel


class LeadsPaginated(graphene.ObjectType):
    data = graphene.List(LeadType)
    total = graphene.Int()

class Query(graphene.ObjectType):
    lead_age_groups = graphene.List(LeadsGroup)
    lead_duration_groups = graphene.List(LeadsGroup)
    consumer_origin_groups = graphene.List(LeadsGroup)
    os_groups = graphene.List(OSGroupType)
    browser_groups = graphene.List(BrowserGroupType)
    traffic_channels = graphene.List(TrafficChannelType)
    leads = graphene.Field(
        LeadsPaginated,
        date_from=graphene.types.datetime.DateTime(required=True),
        date_to=graphene.types.datetime.DateTime(required=True),
        projects=graphene.List(graphene.UUID, required=False),
        label_type = graphene.String(required=False),
        label_values = JSONDict(required=False),
        os_groups=graphene.List(graphene.Int, required=False),
        browser_groups=graphene.List(graphene.Int, required=False),
        traffic_channels=graphene.List(graphene.Int, required=False),
        limit=graphene.Int(),
        offset=graphene.Int()
    )
    total_visits = graphene.Field(
        graphene.Int,
        date_from=graphene.types.datetime.DateTime(required=True),
        date_to=graphene.types.datetime.DateTime(required=True),
        projects=graphene.List(graphene.UUID, required=False),
        label_type=graphene.String(required=False),
        label_values=JSONDict(required=False),
        os_groups=graphene.List(graphene.Int, required=False),
        browser_groups=graphene.List(graphene.Int, required=False),
        traffic_channels=graphene.List(graphene.Int, required=False)
    )
    total_conversions = graphene.Field(
        graphene.Int,
        date_from=graphene.types.datetime.DateTime(required=True),
        date_to=graphene.types.datetime.DateTime(required=True),
        projects=graphene.List(graphene.UUID, required=False),
        label_type=graphene.String(required=False),
        label_values=JSONDict(required=False),
        os_groups=graphene.List(graphene.Int, required=False),
        browser_groups=graphene.List(graphene.Int, required=False),
        traffic_channels=graphene.List(graphene.Int, required=False)
    )
    total_devices = graphene.Field(
        graphene.Int,
        date_from=graphene.types.datetime.DateTime(required=True),
        date_to=graphene.types.datetime.DateTime(required=True),
        projects=graphene.List(graphene.UUID, required=False),
        label_type=graphene.String(required=False),
        label_values=JSONDict(required=False),
        os_groups=graphene.List(graphene.Int, required=False),
        browser_groups=graphene.List(graphene.Int, required=False),
        traffic_channels=graphene.List(graphene.Int, required=False)
    )
    leads_by_period = graphene.List(
        LeadsPeriod,
        date_from=graphene.types.datetime.DateTime(required=True),
        date_to=graphene.types.datetime.DateTime(required=True),
        projects=graphene.List(graphene.UUID, required=False),
        label_type = graphene.String(required=False),
        label_values = JSONDict(required=False),
        os_groups=graphene.List(graphene.Int, required=False),
        browser_groups=graphene.List(graphene.Int, required=False),
        traffic_channels = graphene.List(graphene.Int, required=False)
    )
    lead_age_totals = graphene.List(
        LeadsGroup,
        date_from=graphene.types.datetime.DateTime(required=True),
        date_to=graphene.types.datetime.DateTime(required=True),
        groups=graphene.List(graphene.String, required=False),
        projects=graphene.List(graphene.UUID, required=False),
        label_type=graphene.String(required=False),
        label_values=JSONDict(required=False),
        os_groups=graphene.List(graphene.Int, required=False),
        browser_groups=graphene.List(graphene.Int, required=False),
        traffic_channels=graphene.List(graphene.Int, required=False)
    )
    lead_duration_by_period = graphene.List(
        LeadsPeriodGroup,
        date_from=graphene.types.datetime.DateTime(required=True),
        date_to=graphene.types.datetime.DateTime(required=True),
        groups=graphene.List(graphene.String, required=False),
        projects=graphene.List(graphene.UUID, required=False),
        label_type=graphene.String(required=False),
        label_values=JSONDict(required=False),
        os_groups=graphene.List(graphene.Int, required=False),
        browser_groups=graphene.List(graphene.Int, required=False),
        traffic_channels=graphene.List(graphene.Int, required=False)
    )
    lead_duration_totals = graphene.List(
        LeadsGroup,
        date_from=graphene.types.datetime.DateTime(required=True),
        date_to=graphene.types.datetime.DateTime(required=True),
        groups=graphene.List(graphene.String, required=False),
        projects=graphene.List(graphene.UUID, required=False),
        label_type=graphene.String(required=False),
        label_values=JSONDict(required=False),
        os_groups=graphene.List(graphene.Int, required=False),
        browser_groups=graphene.List(graphene.Int, required=False),
        traffic_channels=graphene.List(graphene.Int, required=False)
    )
    consumer_origin_by_period = graphene.List(
        LeadsPeriodGroup,
        date_from=graphene.types.datetime.DateTime(required=True),
        date_to=graphene.types.datetime.DateTime(required=True),
        groups=graphene.List(graphene.String, required=False),
        projects=graphene.List(graphene.UUID, required=False),
        by_subnet=graphene.Boolean(required=False, default_value=False),
        label_type=graphene.String(required=False),
        label_values=JSONDict(required=False),
        os_groups=graphene.List(graphene.Int, required=False),
        browser_groups=graphene.List(graphene.Int, required=False),
        traffic_channels=graphene.List(graphene.Int, required=False)
    )
    lead_lineage_by_period = graphene.List(
        SalesPeriodGroup,
        date_from=graphene.types.datetime.DateTime(required=True),
        date_to=graphene.types.datetime.DateTime(required=True),
        projects=graphene.List(graphene.UUID, required=False),
        label_type=graphene.String(required=False),
        label_values=JSONDict(required=False),
        os_groups=graphene.List(graphene.Int, required=False),
        browser_groups=graphene.List(graphene.Int, required=False),
        traffic_channels=graphene.List(graphene.Int, required=False),
        lead_owner=graphene.String(required=False) #'you','other','all'
    )
    url_label_list = graphene.List(
        graphene.String,
        label_type=graphene.String(required=True),
        label_name=graphene.String(required=True),
        search=graphene.String(required=False)
    )

    lead_browser_totals = graphene.List(
        LeadsGroup,
        date_from=graphene.types.datetime.DateTime(required=True),
        date_to=graphene.types.datetime.DateTime(required=True),
        projects=graphene.List(graphene.UUID, required=False),
        label_type=graphene.String(required=False),
        label_values=JSONDict(required=False),
        os_groups=graphene.List(graphene.Int, required=False),
        browser_groups=graphene.List(graphene.Int, required=False),
        traffic_channels=graphene.List(graphene.Int, required=False)
    )

    lead_device_type_totals = graphene.List(
        LeadsGroup,
        date_from=graphene.types.datetime.DateTime(required=True),
        date_to=graphene.types.datetime.DateTime(required=True),
        projects=graphene.List(graphene.UUID, required=False),
        label_type=graphene.String(required=False),
        label_values=JSONDict(required=False),
        os_groups=graphene.List(graphene.Int, required=False),
        browser_groups=graphene.List(graphene.Int, required=False),
        traffic_channels=graphene.List(graphene.Int, required=False)
    )

    lead_os_totals = graphene.List(
        LeadsGroup,
        date_from=graphene.types.datetime.DateTime(required=True),
        date_to=graphene.types.datetime.DateTime(required=True),
        is_mobile=graphene.Boolean(required=True),
        projects=graphene.List(graphene.UUID, required=False),
        label_type=graphene.String(required=False),
        label_values=JSONDict(required=False),
        os_groups=graphene.List(graphene.Int, required=False),
        browser_groups=graphene.List(graphene.Int, required=False),
        traffic_channels=graphene.List(graphene.Int, required=False)
    )

    def resolve_lead_age_groups(self, info):
        return _resolve_groups(info, LEAD_AGE_GROUPS)

    def resolve_lead_duration_groups(self, info):
        return _resolve_groups(info, LEAD_DURATION_GROUPS)

    def resolve_consumer_origin_groups(self, info):
        return _resolve_groups(info, CONSUMER_ORIGIN_GROUPS)

    def resolve_url_label_list(self, info, label_type, label_name, search):
        if not info.context.user.is_authenticated:
            return None
        user = info.context.user
        return load_url_label_list(user, label_type, label_name, search)

    def resolve_traffic_channels(self, info):
        if not info.context.user.is_authenticated:
            return None
        return TrafficChannel.objects.all()

    def resolve_total_visits(self, info, date_from, date_to, projects=None,
                                label_type=None, label_values=None,
                                os_groups=None, browser_groups=None, traffic_channels=None):
        if not info.context.user.is_authenticated:
            return None
        user = info.context.user
        return total_visits(user, date_from, date_to, projects, label_type,
                                 label_values, os_groups, browser_groups, traffic_channels)

    def resolve_total_conversions(self, info, date_from, date_to, projects=None,
                                label_type=None, label_values=None,
                                os_groups=None, browser_groups=None, traffic_channels=None):
        if not info.context.user.is_authenticated:
            return None
        user = info.context.user
        return total_conversions(user, date_from, date_to, projects, label_type,
                                 label_values, os_groups, browser_groups, traffic_channels)

    def resolve_total_devices(self, info, date_from, date_to, projects=None,
                                label_type=None, label_values=None,
                                os_groups=None, browser_groups=None, traffic_channels=None):
        if not info.context.user.is_authenticated:
            return None
        user = info.context.user
        return total_devices(user, date_from, date_to, projects, label_type,
                                 label_values, os_groups, browser_groups, traffic_channels)

    def resolve_leads(self, info, date_from, date_to, projects=None,
                      label_type=None, label_values=None,
                      os_groups=None, browser_groups=None, traffic_channels=None,
                      limit=10, offset=0):
        if not info.context.user.is_authenticated:
            return None
        user = info.context.user
        leads_qs = get_leads(user, date_from, date_to, projects,
                        label_type, label_values, os_groups, browser_groups, traffic_channels)
        total = leads_qs.count()
        leads = leads_qs[offset:offset+limit]
        for lead in leads:
            if lead.geo:
                lead.country = lead.geo.country.name
        return LeadsPaginated(
            total=total,
            data=leads
        )

    def resolve_lead_age_totals(self, info, date_from, date_to, groups=None, projects=None,
                                label_type=None, label_values=None,
                                os_groups=None, browser_groups=None, traffic_channels=None):
        if not info.context.user.is_authenticated:
            return None
        user = info.context.user
        totals = lead_age_totals(user, date_from, date_to, groups, projects, label_type,
                                 label_values, os_groups, browser_groups, traffic_channels)
        groups = []
        for total in totals:
            try:
                title = LEAD_AGE_GROUPS[total['group_name']].title
            except KeyError:
                title = _('Others')
            groups.append(LeadsGroup(
                group_name=total['group_name'],
                group_title=title,
                leads_count=total['leads_count']
            ))
        return groups

    def resolve_leads_by_period(self, info, date_from, date_to, projects=None,
                                label_type=None, label_values=None,
                                os_groups=None, browser_groups=None, traffic_channels=None):
        if not info.context.user.is_authenticated:
            return None

        user = info.context.user
        periods = leads_by_period(user, date_from, date_to, projects,
                                  label_type, label_values, os_groups,
                                  browser_groups, traffic_channels)
        scale_period = get_scale_period(date_from, date_to)
        res = []
        for period in periods:
            res.append(LeadsPeriod(
                created=format_leads_period(period['created_period'], scale_period),
                leads_count=period['leads_count']
            ))
        return res

    def resolve_lead_duration_by_period(self, info, date_from, date_to, groups=None, projects=None,
                                        label_type=None, label_values=None,
                                        os_groups=None, browser_groups=None, traffic_channels=None):
        if not info.context.user.is_authenticated:
            return None
        user = info.context.user
        data = lead_duration_by_period(user, date_from, date_to, groups, projects,
                                       label_type, label_values, os_groups,
                                       browser_groups, traffic_channels)
        scale_period = get_scale_period(date_from, date_to)
        res = []
        for row in data:
            group_title = LEAD_DURATION_GROUPS[row['group_name']].title
            res.append(LeadsPeriodGroup(
                created=format_leads_period(row['created_period'], scale_period),
                group_name=row['group_name'],
                group_title=group_title,
                leads_count=row['leads_count']
            ))
        return res

    def resolve_lead_duration_totals(self, info, date_from, date_to, groups=None, projects=None,
                                     label_type=None, label_values=None,
                                     os_groups=None, browser_groups=None, traffic_channels=None):
        if not info.context.user.is_authenticated:
            return None
        user = info.context.user
        totals = lead_duration_totals(user, date_from, date_to, groups, projects,
                                      label_type, label_values, os_groups,
                                      browser_groups, traffic_channels)
        groups = []
        for total in totals:
            try:
                title = LEAD_DURATION_GROUPS[total['group_name']].title
            except KeyError:
                title = _('Others')
            groups.append(LeadsGroup(
                group_name=total['group_name'],
                group_title=title,
                leads_count=total['leads_count']
            ))
        return groups

    def resolve_consumer_origin_by_period(self, info, date_from, date_to,
                                          groups=None, projects=None, by_subnet=False,
                                          label_type=None, label_values=None,
                                          os_groups=None, browser_groups=None, traffic_channels=None):
        if not info.context.user.is_authenticated:
            return None
        user = info.context.user
        device_field = 'subnet' if by_subnet else 'device_id'
        groups_by_period = consumer_origin_by_period(user, date_from, date_to, groups, projects,
                                                    device_field, label_type, label_values,
                                                    os_groups, browser_groups, traffic_channels)
        res = []
        for created_period, sections in groups_by_period.items():
            for group_name, device_frequency in sections.items():
                if device_frequency > 0:
                    group_title = CONSUMER_ORIGIN_GROUPS[group_name].title
                    res.append(LeadsPeriodGroup(
                        created=created_period,
                        group_name=group_name,
                        group_title=group_title,
                        leads_count=device_frequency
                    ))
        return res

    def resolve_os_groups(self, info):
        if not info.context.user.is_authenticated:
            return None
        return OSGroup.objects.all()

    def resolve_browser_groups(self, info):
        if not info.context.user.is_authenticated:
            return None
        return BrowserGroup.objects.all()

    def resolve_lead_lineage_by_period(self, info, date_from, date_to, projects=None,
                                       label_type=None, label_values=None,
                                       os_groups=None, browser_groups=None, traffic_channels=None,
                                       lead_owner='all'):
        if not info.context.user.is_authenticated:
            return None
        user = info.context.user

        data = []
        if lead_owner in ('you','all'):
            data += list(your_lead_lineage_by_period(user, date_from, date_to, projects,
                                                    label_type, label_values,
                                                    os_groups, browser_groups, traffic_channels))
        if lead_owner in ('other', 'all'):
            data += list(other_lead_lineage_by_period(user, date_from, date_to,
                                                      label_type, label_values,
                                                      os_groups, browser_groups, traffic_channels))
        data = sorted(data, key=lambda d: d['created_period'])
        scale_period = get_scale_period(date_from, date_to)
        res = [
            SalesPeriodGroup(
                created=format_leads_period(l['created_period'], scale_period),
                group_name='{}_leads'.format(l['lead_type']),
                group_title=_('{} leads'.format(l['lead_type'].capitalize())),
                leads_count=round(l['sales_count'] / l['leads_count'], 2)
            ) for l in data
        ]
        return res

    def resolve_lead_browser_totals(self, info, date_from, date_to, projects=None,
                                     label_type=None, label_values=None,
                                     os_groups=None, browser_groups=None, traffic_channels=None):
        if not info.context.user.is_authenticated:
            return None
        user = info.context.user
        totals = lead_browser_totals(user, date_from, date_to, projects, label_type,
                                 label_values, os_groups, browser_groups, traffic_channels)
        groups = []
        for total in totals:
            groups.append(LeadsGroup(
                group_name=total['group_name'],
                group_title=total['group_name'],
                leads_count=total['leads_count']
            ))
        return groups

    def resolve_lead_device_type_totals(self, info, date_from, date_to, projects=None,
                                     label_type=None, label_values=None,
                                     os_groups=None, browser_groups=None, traffic_channels=None):
        if not info.context.user.is_authenticated:
            return None
        user = info.context.user
        totals = lead_device_type_totals(user, date_from, date_to, projects, label_type,
                                         label_values, os_groups, browser_groups, traffic_channels)
        groups = []
        for total in totals:
            groups.append(LeadsGroup(
                group_name=total['group_name'],
                group_title=total['group_name'],
                leads_count=total['leads_count']
            ))
        return groups

    def resolve_lead_os_totals(self, info, date_from, date_to, is_mobile, projects=None,
                                     label_type=None, label_values=None,
                                     os_groups=None, browser_groups=None, traffic_channels=None):
        if not info.context.user.is_authenticated:
            return None
        user = info.context.user
        totals = lead_os_totals(user, date_from, date_to, is_mobile, projects, label_type,
                                 label_values, os_groups, browser_groups, traffic_channels)
        groups = []
        for total in totals:
            groups.append(LeadsGroup(
                group_name=total['group_name'],
                group_title=total['group_name'],
                leads_count=total['leads_count']
            ))
        return groups
