from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from collector.models import (Pixel, Font, Lead, Event, LeadField, Device, DeviceBrand,
                              BrowserVersion, BrowserFamily, OSFamily, OS, City, FieldMapping)
from collector.models.dictionaries import Field, Provider, OSGroup, BrowserGroup
from .models import SessionStorage, Project


class SessionAdmin(admin.ModelAdmin):
    autocomplete_fields = ('pixel',)


class ProjectAdmin(admin.ModelAdmin):
    search_fields = ('id', 'title')


class FieldMappingInline(admin.TabularInline):
    model = FieldMapping


class PixelAdmin(admin.ModelAdmin):
    search_fields = ('id', 'title')
    autocomplete_fields = ('project',)
    inlines = [FieldMappingInline]


class UntransListFilter(admin.SimpleListFilter):
    title = _('Untranslated')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'untrans'

    def lookups(self, request, model_admin):
        return (
            ('untrans', _('Untranslated')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'untrans':
            return queryset.filter(Q(name_ru="") | Q(name_ru=None))


class CityAdmin(admin.ModelAdmin):
    list_filter = (UntransListFilter,)


class FieldAdmin(admin.ModelAdmin):
    search_fields = ('name',)


class AuditInline(admin.TabularInline):
    model = Lead.audits.through
    autocomplete_fields = ('audit',)


class LeadAdmin(admin.ModelAdmin):
    search_fields = ('id',)
    ordering = ('-session_started',)
    autocomplete_fields = ('pixel', 'provider')
    inlines = (AuditInline,)


class LeadFieldAdmin(admin.ModelAdmin):
    autocomplete_fields = ('lead',)


class ProviderAdmin(admin.ModelAdmin):
    search_fields = ('asn', 'asn_description')


class OSInline(admin.TabularInline):
    model = OS
    extra = 1


class OSFamilyAdmin(admin.ModelAdmin):
    inlines = (OSInline,)
    list_filter = ('group',)


class OSAdmin(admin.ModelAdmin):
    list_filter = ('family',)


class OSFamilyInline(admin.TabularInline):
    model = OSFamily
    extra = 1


class OSGroupAdmin(admin.ModelAdmin):
    inlines = (OSFamilyInline,)


class BrowserVersionInline(admin.TabularInline):
    model = BrowserVersion
    extra = 1


class BrowserFamilyInline(admin.TabularInline):
    model = BrowserFamily


class BrowserVersionAdmin(admin.ModelAdmin):
    list_filter = ('family',)
    extra = 1


class BrowserFamilyAdmin(admin.ModelAdmin):
    inlines = (BrowserVersionInline,)
    list_filter = ('group',)


class BrowserGroupAdmin(admin.ModelAdmin):
    inlines = (BrowserFamilyInline,)


admin.site.register(SessionStorage, SessionAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Pixel, PixelAdmin)
admin.site.register(Event)
admin.site.register(Font)
admin.site.register(Field, FieldAdmin)
admin.site.register(Provider, ProviderAdmin)
admin.site.register(Lead, LeadAdmin)
admin.site.register(LeadField, LeadFieldAdmin)
admin.site.register(Device)
admin.site.register(DeviceBrand)
admin.site.register(BrowserVersion, BrowserVersionAdmin)
admin.site.register(BrowserFamily, BrowserFamilyAdmin)
admin.site.register(BrowserGroup, BrowserGroupAdmin)
admin.site.register(OS, OSAdmin)
admin.site.register(OSFamily, OSFamilyAdmin)
admin.site.register(OSGroup, OSGroupAdmin)
admin.site.register(City, CityAdmin)
