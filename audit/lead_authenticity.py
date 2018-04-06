from audit.models import Audit
from audit.utils import check_input_fields, load_leads_by_fields
from collector.models import LeadField
from django.utils.translation import ugettext as _
from audit.error import AuditError


def check_lead_authenticity(pixel, check_fields):
    """
    :param pixel: пиксел для которого проверяем лиды
    :type pixel: collector.models.Pixel
    :param check_fields: поля для проверки на подмену
    :type check_fields: dict {f_name: f_value}
    :raise: audit.error.AuditError
    :rtype: tuple
    :return: (authentic: bool, fields: dict) -
        authentic: bool - если все поля совпали то true, иначе false
        fields: {
            field-name1: bool true - совпало, false - не совпало
            ip: bool,
            created: bool,
            confirm: bool,
            field-name2: bool
        } список полей : совпало / не совпало, если ни один лид не найден пустой объект

    1. Делим все поля на те что обязательные в мэппинге и остальные
    2. Ищем лиды по тем что в мэппинге
    3. сравниваем и остальные поля
    4. в филдс в ответе выводим все совпало/несовпало
    5. Нужен интерфейс вызова данного апи
    5.1 В нем должны требоваться все поля из меппинга
    5.2 Также должна быть возможность добавить поля неописанные в меппинге
    """
    req_fields_mapping = pixel.fields_mapping.filter(required=True).select_related('target_field')
    required_fields = _parse_required_fields(req_fields_mapping, check_fields)
    check_fields = check_input_fields(check_fields)
    leads = load_leads_by_fields(required_fields, pixel)
    res = _check_lead_authenticity(leads, check_fields)
    Audit.log(pixel.project.user, 'lead_authenticity', check_fields, leads)
    return res


def _parse_required_fields(req_fields_mapping, check_fields):
    """

    :param req_fields_mapping:
    :param check_fields:
    :return:
    """
    try:
        return {fm.target_field.name: check_fields[fm.target_field.name]
                for fm in req_fields_mapping}
    except KeyError as e:
        raise AuditError(_('Field "{}" is required').format(e.args[0]))


def _check_lead_authenticity(leads, check_fields):
    """

    :param leads: found leads
    :type leads: list
    :param check_fields: поля для проверки на подмену
    :type check_fields: dict {f_name: f_value}
    :return:
    """
    if len(leads) == 0:
        return False, {}

    check_field_names = check_fields.keys()
    fields = {}
    for lead in leads:
        fields = {}
        all_fields_match = True
        lead_fields = lead.fields_hash_map(check_field_names)
        for field_name, exp_field_data in check_fields.items():
            exp_field_hash = LeadField.make_field_data_hash(exp_field_data)
            lead_field_hash = lead_fields.get(field_name)
            fields[field_name] = exp_field_hash == lead_field_hash
            if not fields[field_name]:
                all_fields_match = False

        if lead_fields and all_fields_match:
            return True, fields

    return False, fields
