import uuid
import mmh3
from django.db import models
from django.contrib.postgres.fields.jsonb import JSONField
from django.db.models.deletion import PROTECT, CASCADE
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_bytes

from collector.models.dictionaries import BrowserVersion, Device, Font, ScreenResolution, City, OS, \
    Provider
from collector.models.projects import Pixel


class SessionStorage(models.Model):
    ORIENTATIONS = (
        ('landscape', 'landscape'),
        ('portrait', 'portrait')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pixel = models.ForeignKey(Pixel, on_delete=PROTECT)
    ip_addr = models.GenericIPAddressField(blank=True, null=True)
    provider = models.ForeignKey(Provider, blank=True, null=True, on_delete=PROTECT)
    domain = models.CharField(max_length=256, blank=True, null=True)
    get_params = models.CharField(max_length=512, blank=True, null=True)
    user_agent_string = models.CharField(max_length=2056, blank=True, null=True)
    os_version = models.ForeignKey(OS, blank=True, null=True, default=None, on_delete=PROTECT)
    browser = models.ForeignKey(BrowserVersion, blank=True, null=True,
                                default=None, on_delete=PROTECT)
    device = models.ForeignKey(Device, blank=True, null=True, default=None, on_delete=PROTECT)
    cookie_enabled = models.BooleanField(default=False)
    current_language = models.CharField(max_length=20, blank=True, null=True)
    languages = models.CharField(max_length=100, blank=True, null=True)
    geo = models.ForeignKey(City, blank=True, null=True, default=None, on_delete=PROTECT)
    java_enabled = models.BooleanField(default=False)
    online = models.BooleanField(default=False)
    fonts = models.ManyToManyField(Font, blank=True)
    plugin_list = models.CharField(max_length=3000, blank=True, null=True)
    canvas_byte_array = models.TextField(blank=True, null=True)
    webgl_vendor = models.CharField(max_length=512, blank=True, null=True)
    orientation = models.CharField(max_length=20, choices=ORIENTATIONS, blank=True, null=True)
    ad_block = models.BooleanField(default=False)
    has_ss = models.BooleanField(default=False)
    has_ls = models.BooleanField(default=False)
    has_idb = models.BooleanField(default=False)
    has_odb = models.BooleanField(default=False)
    timezone_offset = models.IntegerField(blank=True, null=True)
    screen = models.ForeignKey(ScreenResolution, blank=True, null=True,
                               default=None, on_delete=PROTECT)
    screen_color_depth = models.IntegerField(blank=True, null=True)
    viewport_height = models.IntegerField(blank=True, null=True)
    viewport_width = models.IntegerField(blank=True, null=True)
    available_height = models.IntegerField(blank=True, null=True)
    available_width = models.IntegerField(blank=True, null=True)
    location = models.CharField(max_length=512, blank=True, null=True)
    referrer = models.CharField(max_length=512, blank=True, null=True)
    page_total = models.IntegerField(blank=True, null=True)
    page_title = models.CharField(max_length=1024, blank=True, null=True)
    form_total_fields = models.IntegerField(blank=True, null=True)
    form_hidden_fields = models.IntegerField(blank=True, null=True)
    form_disabled_fields = models.IntegerField(blank=True, null=True)
    form_has_hidden_fields = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    submitted = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "{}: {} {} {}".format(self.pixel, self.created, self.domain, self.id)

    def save_fonts(self, font_names):
        """
        Add fonts to session. If font not in db create it.
        :param font_names: list of strings
        :return: None
        """
        fonts_map = dict(Font.objects.filter(name__in=font_names).values_list('name', 'id'))
        to_insert = [Font(name=font) for font in font_names if font not in fonts_map]
        if to_insert:
            Font.objects.bulk_create(to_insert)
        fonts = list(Font.objects.filter(name__in=font_names))
        self.fonts.add(*fonts)

    def get_fingerprint(self):
        """
        dummy fingerprint
        @todo make normal fingerprint
        :return:
        """
        signature_values = [
            self.user_agent_string,
            self.current_language,
            self.screen_color_depth,
            # self.deviceMemoryKey ???
            # self.pixelRatioKey ???
            # self.hardwareConcurrencyKey ???
            ';'.join((str(self.screen.width), str(self.screen.height))),
            ';'.join((str(self.available_width), str(self.available_height))),
            self.timezone_offset,
            self.has_ss,
            self.has_ls,
            self.has_idb,
            # self.addBehaviorKey
            self.has_odb,
            # self.cpuClassKey
            # self.platformKey
            # self.doNotTrackKey
            self.plugin_list,
            self.canvas_byte_array,
            # self.webglKey - like canvas byte array
            self.webgl_vendor,
            self.ad_block,
            # self.hasLiedLanguagesKey
            # self.hasLiedResolutionKey
            # self.hasLiedOsKey
            # self.hasLiedBrowserKey
            # self.touchSupportKey
            ";".join(self.fonts.values_list('name', flat=True))
        ]
        signature = '~~~'.join(map(str, signature_values))
        return format(mmh3.hash128(force_bytes(signature), 31), 'x')


class Event(models.Model):
    EVENT_TYPES = (
        ('field-filled', _('field-filled')),
        ('form-submitted', _('form-submitted'))
    )
    session = models.ForeignKey(SessionStorage, related_name='events', on_delete=CASCADE)
    event_type = models.CharField(choices=EVENT_TYPES, max_length=50)
    started = models.DateTimeField(db_index=True)
    finished = models.DateTimeField(db_index=True)
    duration = models.IntegerField(help_text=_('in milliseconds'))
    field_type = models.CharField(max_length=50, null=True, blank=True)
    field_tag = models.CharField(max_length=50, null=True, blank=True)
    field_number = models.IntegerField(null=True, blank=True)
    field_parent = models.ForeignKey('self', help_text=_('previous filled field'),
                                     null=True, blank=True, on_delete=CASCADE)
    field_parent_number = models.IntegerField(blank=True, null=True,
                                              help_text=_('previous filled field number'))
    field_hidden = models.BooleanField(default=False)
    field_checked = models.BooleanField(default=False)
    field_readonly = models.BooleanField(default=False)
    field_name = models.CharField(max_length=255, blank=True, null=True)
    field_id = models.CharField(max_length=255, blank=True, null=True)
    field_alt = models.CharField(max_length=255, blank=True, null=True)
    field_title = models.CharField(max_length=255, blank=True, null=True)
    field_data = JSONField(blank=True, null=True, help_text=_('data-... attrs'))
    field_accesskey = models.CharField(max_length=20, blank=True, null=True)
    field_class = models.CharField(max_length=255, blank=True, null=True,
                                   help_text=_('css class attr'))
    field_contenteditable = models.CharField(max_length=10, blank=True, null=True)
    field_contextmenu = models.CharField(max_length=100, blank=True, null=True)
    field_dir = models.CharField(max_length=20, blank=True, null=True,
                                 help_text=_('text direction attr'))
    field_lang = models.CharField(max_length=100, blank=True, null=True)
    field_spellcheck = models.CharField(max_length=10, blank=True, null=True)
    field_style = models.CharField(max_length=255, blank=True, null=True,
                                   help_text=_('css style attr'))
    field_tabindex = models.CharField(max_length=10, blank=True, null=True,
                                      help_text=_('tabindex attr'))
    field_required = models.CharField(max_length=10, blank=True, null=True,
                                      help_text=_('required attr'))
    field_pattern = models.CharField(max_length=100, blank=True, null=True,
                                     help_text=_('pattern attr'))
    field_list = models.CharField(max_length=50, blank=True, null=True, help_text=_('list attr'))
    correction_count = models.IntegerField(default=0, help_text=_('count of corrections by user'))
    keypress_count = models.IntegerField(default=0, help_text=_('count of keypress by user'))
    special_keypress_count = models.IntegerField(default=0,
                                                 help_text=_('count of keypress by user'))
    text_length = models.IntegerField(default=0)
    from_clipboard = models.BooleanField(default=False,
                                         help_text=_('is data pasted from clipboard?'))
    open_data = models.TextField(blank=True, null=True, help_text=_('entered data'))
    hash_data = models.CharField(blank=True, null=True, max_length=100,
                                 help_text=_('entered data hash'))

    def __str__(self):
        return "{}: {} {} {}".format(self.session, self.event_type,
                                     self.field_name or self.field_type, self.finished)
