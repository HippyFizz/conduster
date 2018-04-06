from django import forms
from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.forms import FlatpageForm
from django.contrib.flatpages.models import FlatPage
from ckeditor.widgets import CKEditorWidget

from xflatpages.models import XFlatPage


class XFlatPageForm(FlatpageForm):
    content = forms.CharField(widget=CKEditorWidget())
    content_ru = forms.CharField(widget=CKEditorWidget())
    class Meta:
        model = XFlatPage
        fields = '__all__'


class XFlatPageAdmin(FlatPageAdmin):
    form = XFlatPageForm
    fieldsets = (
        (None, {'fields': ('url', 'title', 'content', 'sites', 'title_ru', 'content_ru')}),
    )
    list_display = ('url', 'title', 'title_ru')
    search_fields = ('url', 'title', 'title_ru')


admin.site.unregister(FlatPage)
admin.site.register(XFlatPage, XFlatPageAdmin)