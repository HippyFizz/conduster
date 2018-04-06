from audit.error import AuditError
from audit.models import Audit, DuplicationRequiredFieldSet
from audit.utils import check_input_fields, load_leads_by_fields
from collector.models.analytics import LeadField, Lead
from django.utils.translation import ugettext as _


def check_lead_duplication(user, fields):
    """
    Finds leads by fields and check duplications and sales
    # Провалено, Лид <дата создания=None> не существует в системе
    # Успешно, Лид <дата создания> никому не продавался
    # Успешно, Лид <дата создания> никому не продавался, аудировался вами
    # Провалено, Лид <дата создания> был продан N раз
    # Провалено, Лид <дата создания> был продан вам вне системы
    # Провалено, Лид <дата создания> не продавался, имеет N дубликатов
    # Провалено, Лид <дата создания> не продавался, имеет N дубликатов, аудировался вами
    # Провалено, Лид <дата создания> был продан N раз, имеет N дубликатов, аудировался вами
    :param check_fields: поля для проверки на подмену
    :type check_fields: dict {f_name: f_value, f_name: f_value}
    :raise: audit.audit.AuditError
    :return: {
        'success': bool,
        'resolution': str,
        'created': DateTime,
        'your_audits': list of DateTime,
        'duplicates': list of DateTime,
        'sales': list of DateTime,
    }
    """
    fields = check_input_fields(fields)
    fields = _check_input_required_fieldsets(fields)
    leads = _load_leads_by_fields(fields)
    res = _check_lead_duplication(user, leads)
    Audit.log(user, 'lead_duplication', fields, leads)
    return res


def _load_leads_by_fields(fields):
    lqs = load_leads_by_fields(fields)
    lqs = lqs.prefetch_related('audits')
    lqs = lqs.prefetch_related('audits__user')
    return lqs


def _check_input_required_fieldsets(input_fields, fieldsets=None):
    """
    check that input_fields has all fields of at least one required duplication fieldset
    :param input_fields: {f_name: f_value_hash}
    :type input_fields: dict
    :return:
    """
    if fieldsets is None:
        fieldsets = DuplicationRequiredFieldSet.objects.prefetch_related('fields')

    for fieldset in fieldsets:
        if _check_input_required_fieldset_fields(input_fields, fieldset.fields.all()):
            return input_fields

    msg = _(" or ").join(
        ["(" + (", ".join((field.name  for field in fieldset.fields.all()))) + ")"
         for fieldset in fieldsets]
    )
    raise AuditError(_('Need minimal required fields {}'.format(msg)))


def _check_input_required_fieldset_fields(input_fields, fields):
    """
    check that input_fields has all required fields of fieldset
    :param input_fields:
    :param fields:
    :return:
    """
    for field in fields:
        if field.name not in input_fields:
            return False
    return True

def _check_lead_duplication(user, leads):
    """
    check lead duplications and sales
    # Провалено, Лид <дата создания=None> не существует в системе
    # Успешно, Лид <дата создания> никому не продавался
    # Успешно, Лид <дата создания> никому не продавался, аудировался вами
    # Провалено, Лид <дата создания> был продан N раз
    # Провалено, Лид <дата создания> был продан вам вне системы
    # Провалено, Лид <дата создания> не продавался, имеет N дубликатов
    # Провалено, Лид <дата создания> не продавался, имеет N дубликатов, аудировался вами
    # Провалено, Лид <дата создания> был продан N раз, имеет N дубликатов, аудировался вами
    :param check_fields: поля для проверки на подмену
    :type check_fields: dict {f_name: f_value, f_name: f_value}
    :raise: audit.audit.AuditError
    :return: {
        'success': bool,
        'resolution': str,
        'created': DateTime,
        'your_audits': list of DateTime,
        'duplicates': list of DateTime,
        'sales': list of DateTime,
    }
    """
    yll = _find_your_last_lead(user, leads)
    res = {
        'success': False,
        'resolution': None,
        'created': yll.created if yll else None,
        'your_audits': _find_your_audits(user, leads),
        'duplicates': _find_duplicates(yll, leads),
        'sales': _find_sales(user, leads)
    }
    res['success'] = _get_success(res)
    res['resolution'] = _get_resolution(res)
    return res


def _find_your_last_lead(user, leads):
    your_last_lead = None
    for lead in leads:
        if lead.pixel.project.user == user and \
                (your_last_lead is None or your_last_lead.created < lead.created):
            your_last_lead = lead
    return your_last_lead


def _find_duplicates(yll, leads):
    if yll is None:
        return []
    duplicates = []
    for lead in leads:
        if lead != yll and lead.pixel.project.user == yll.pixel.project.user:
            duplicates.append(lead.created)
    return sorted(duplicates, reverse=True)


def _find_your_audits(user, leads):
    your_audits = set()
    for lead in leads:
        audits = lead.audits.all()
        for audit in audits:
            if audit.user == user:
                your_audits.add(audit.processed)
    return sorted(your_audits, reverse=True)


def _find_sales(user, leads):
    sales = {}
    for lead in leads:
        if lead.pixel.project.user != user:
            sales[lead.pixel.project.user.id] = max(lead.created, sales.get(lead.pixel.project.user.id, lead.created))
        audits = lead.audits.all()
        for audit in audits:
            if audit.user != user:
                sales[audit.user.id] = max(audit.processed, sales.get(audit.user.id, audit.processed))
    return sorted(sales.values(), reverse=True)


def _get_success(res):
    return bool(res['created'] and not res['sales'] and not res['duplicates'])

def _get_resolution(res):
    if not res['created']:
        return _('Lead was sold to you outside the system')
    elif res['sales']:
        return _('Lead was sold {} times').format(len(res['sales']))
    elif res['duplicates']:
        return _('Lead has {} duplicates').format(len(res['duplicates']))
    elif res['your_audits']:
        return _('You already audited this lead {} times').format(len(res['your_audits']))
    else:
        return _('New lead')


















