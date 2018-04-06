from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models.deletion import PROTECT

from collector.models.analytics import Lead
from collector.models.dictionaries import Field

User = get_user_model()


class Audit(models.Model):
    """
    Log of user audits
    """
    processed = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=PROTECT)
    method = models.CharField(max_length=60)
    input_data = JSONField()
    leads = models.ManyToManyField(Lead, related_name='audits')

    @classmethod
    def log(cls, user, method, input_data, leads, processed=None):
        cls._inc_leads_salecount(user, leads)
        audit = cls.objects.create(
            user=user,
            method=method,
            input_data=input_data,
            processed=processed
        )
        audit.leads.add(*leads)

    @classmethod
    def _inc_leads_salecount(cls, user, leads):
        for lead in leads:
            if lead.pixel.project.user != user and not cls._did_user_audit_lead(user, lead):
                lead.metrik_lead_salecount += 1
                lead.save(force_update=True, update_fields=('metrik_lead_salecount',))

    @staticmethod
    def _did_user_audit_lead(user, lead):
        for audit in lead.audits.all():
            if user == audit.user:
                return True
        return False

    def __str__(self):
        return "{} {} {}".format(self.processed, self.user, self.method)


class DuplicationRequiredFieldSet(models.Model):
    name = models.CharField(max_length=100)
    fields = models.ManyToManyField(Field, related_name='duplication_required_fieldsets')

    def __str__(self):
        return self.name
