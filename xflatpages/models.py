from django.utils.translation import ugettext_lazy as _
from django.contrib.flatpages.models import FlatPage
from django.db import models

# Create your models here.


class XFlatPage(FlatPage):
    title_ru = models.CharField(_('title_ru'), blank=True, max_length=200)
    content_ru = models.TextField(_('content_ru'), blank=True)
