import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.transaction import atomic
from django.utils import timezone

from audit.models import Audit
from collector.models import Lead
from collector.models.analytics import LeadUtm, LeadOpenstat
from collector.models.dictionaries import City, Provider, OSFamily, OS, BrowserVersion, \
    TrafficChannel, Device
from utils.network import int2ip, ip_int2subnet, ip_int2subnet_int

DAY_MAX_LEADS = 150 # max leads generated per day
DEVICE_POOL = 300 # max device count
IP_MAX = 4294967296 # for more beautifull ips

AD_NETWORKS = [
    "ActionTeaser", "AdHub", "AdKeeper", "AdLabs", "AdvertLink", "BodyClick", "ClicksCloud",
    "DirectAdvert", "DriveNetwork", "Etarg", "GlobalTeaser", "Gnezdo", "Kadam", "MarketGid",
    "MediaVenus", "MegaTizer", "Mpay69", "Oblivochki", "OctoBird", "PGold", "ReCreativ",
    "RedClick", "RedTram", "Smi2", "TeaserMedia", "TeaserNet", "ThorMedia", "Tovarro",
    "VisitWeb", "Yottos"
]

MAX_PARTNERS = 300


def fill_test_leads(pixel_id, leadQuerySet, leadModel, sales_users=None, auditModel=Audit):
    now = timezone.now()
    date_from = now - timedelta(days=90)
    date_from.replace(hour=0, minute=0, second=0, microsecond=0)
    date_to = now

    leadQuerySet.filter(created__range=(date_from, date_to), pixel__id=pixel_id).delete()

    os_versions = OS.objects.all()
    browser_versions = BrowserVersion.objects.all()
    traffic_channels = TrafficChannel.objects.all()
    device_models = Device.objects.all()

    leads = []
    fill_date = date_from
    while fill_date <= date_to:
        leads_count = random.randint(0, DAY_MAX_LEADS)
        for i in range(leads_count):
            seconds_started = random.randint(0, 86399)
            session_started = fill_date + timedelta(seconds=seconds_started)
            seconds = random.randint(seconds_started, 86399)
            created = fill_date + timedelta(seconds=seconds)
            lead = leadModel(
                pixel_id=pixel_id,
                session_started=session_started,
                last_event_time=created,
                created=created
            )

            cren = random.randint(1, 2)  # с вероятностью 1/2 будут появляться id из суженого дипазона
            if (cren) == 1:
                device_id_raw = random.randint(DEVICE_POOL // 2 - 15, DEVICE_POOL // 2 + 15)
            else:
                device_id_raw = random.randint(1, DEVICE_POOL)
            ip_pool = DEVICE_POOL // 2
            device_ip_int = IP_MAX // 2 // DEVICE_POOL * (device_id_raw%ip_pool) + 150 + IP_MAX // 2
            lead.device_id = str(device_id_raw)
            lead.ip_addr = int2ip(device_ip_int)
            geo = City.get_or_create_by_ip(lead.ip_addr)
            if geo:
                lead.geo_id = geo.id
            lead.subnet = ip_int2subnet(device_ip_int)
            if lead.geo and lead.geo.name:
                provider, created = Provider.objects.get_or_create(
                    asn=str(ip_int2subnet_int(device_ip_int)),
                    defaults={'asn_description': lead.geo.name + ' Net.'}
                )
                if provider:
                    lead.provider_id = provider.id

            lead.os_version_id = random.choice(os_versions).id
            lead.browser_id = random.choice(browser_versions).id
            lead.traffic_channel_id = random.choice(traffic_channels).id
            lead.device_model_id = random.choice(device_models).id
            leads.append(lead)

        fill_date += timedelta(1)

    if len(leads):
        leadQuerySet.bulk_create(leads)

    _fill_url_labels(leads)

    _fill_leads_sales(leads, sales_users, auditModel)


def _fill_url_labels(leads):
    utms = []
    openstats = []
    for lead in leads:
        if random.randint(1, 3) < 3:
            ad_network = random.choice(AD_NETWORKS)
            utm = LeadUtm(lead_id=lead.id, utm_source=ad_network)
            if random.randint(1, 3) < 3:
                utm.utm_content = str(random.randint(1, MAX_PARTNERS))
            utms.append(utm)
        if random.randint(1, 3) < 3:
            ad_network = random.choice(AD_NETWORKS)
            openstat = LeadOpenstat(lead_id=lead.id, service=ad_network)
            if random.randint(1, 3) < 3:
                openstat.source = str(random.randint(1, MAX_PARTNERS))
            openstats.append(openstat)
    if utms:
        LeadUtm.objects.bulk_create(utms)
    if openstats:
        LeadOpenstat.objects.bulk_create(openstats)


def _fill_leads_sales(leads, sales_users, auditModel):
    if not sales_users:
        return
    for lead in leads:
        # probability of sale is 1/3
        if random.randint(0, 2) == 2:
            sales_count = random.randint(1, len(sales_users))
            users = random.sample(sales_users, sales_count)
            for user in users:
                _audit_log(
                    auditModel,
                    user,
                    'test_sale',
                    {},
                    [lead],
                    lead.created + timedelta(days=random.randint(0, 5))
                )


##### some copypaste because we CAN'T USE NORMAL MODELS IN MIGRATIONS
def _audit_log(auditModel, user, method, input_data, leads, processed=None):
    _inc_leads_salecount(user, leads)
    audit = auditModel.objects.create(
        user_id=user.id,
        method=method,
        input_data=input_data,
        processed=processed
    )
    for lead in leads:
        auditModel.leads.through.objects.create(audit_id=audit.id, lead_id=lead.id)


##### some copypaste because we CAN'T USE NORMAL MODELS IN MIGRATIONS
def _inc_leads_salecount(user, leads):
    for lead in leads:
        if lead.pixel.project.user.id != user.id and not _did_user_audit_lead(user, lead):
            lead.metrik_lead_salecount += 1
            lead.save(force_update=True, update_fields=('metrik_lead_salecount',))


##### some copypaste because we CAN'T USE NORMAL MODELS IN MIGRATIONS
def _did_user_audit_lead(user, lead):
    for audit in lead.audits.all():
        if user.id == audit.user.id:
            return True
    return False



class Command(BaseCommand):

    help = 'fill leads table with test data'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('pixel_id', type=str)

    @atomic()
    def handle(self, pixel_id, *args, **options):
        fill_test_leads(pixel_id, Lead.objects, Lead)