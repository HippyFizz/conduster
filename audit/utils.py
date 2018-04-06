from audit.error import AuditError

# min count fields to process lead checking if pixel fieldMapping is empty
from collector.models.analytics import LeadField, Lead

MIN_FIELDS_COUNT = 3


def check_input_fields(fields):
    """

    :param check_fields:
    :return:
    >>> check_input_fields({'email':'asd@asd.ru'})
    Traceback (most recent call last):
    ...
    audit.error.AuditError: Minimum 3 fields required
    >>> check_input_fields({'email':'asd@asd.ru', 'name': 'test', 'phone': '123456'}) == {'email':'asd@asd.ru', 'name': 'test', 'phone': '123456'}
    True
    """
    if len(fields) < MIN_FIELDS_COUNT:
        raise AuditError(_('Minimum {} fields required').format(MIN_FIELDS_COUNT))
    return fields


def load_leads_by_fields(fields, pixel=None):
    qs = None
    for field_name, field_data in fields.items():
        field_hash = LeadField.make_field_data_hash(field_data)
        fqs = LeadField.objects
        if pixel is not None:
            fqs = fqs.filter(lead__pixel=pixel)
        fqs = fqs.filter(field_name=field_name, field_hash=field_hash)
        fqs = fqs.values_list('lead_id', flat=True)
        fqs = fqs.distinct()
        qs = qs.intersection(fqs) if qs else fqs

    lqs = Lead.objects
    if pixel is not None:
        lqs = lqs.filter(pixel = pixel)
    lqs = lqs.filter(id__in=qs)
    lqs = lqs.select_related('pixel')
    lqs = lqs.select_related('pixel__project')
    lqs = lqs.select_related('pixel__project__user')
    lqs = lqs.prefetch_related('fields')
    return lqs