from django.contrib import admin

from audit.models import Audit, DuplicationRequiredFieldSet


class AuditAdmin(admin.ModelAdmin):
    ordering = ('-processed',)
    autocomplete_fields = ('leads',)
    search_fields = ('processed', 'method', 'user__username')


class DuplicationRequiredFieldSetAdmin(admin.ModelAdmin):
    ordering = ('name',)
    autocomplete_fields = ('fields',)


admin.site.register(Audit, AuditAdmin)
admin.site.register(DuplicationRequiredFieldSet, DuplicationRequiredFieldSetAdmin)