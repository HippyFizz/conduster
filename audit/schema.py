import graphene
from django.utils.translation import ugettext as _

from audit.error import AuditError
from audit.lead_authenticity import check_lead_authenticity
from audit.lead_duplication import check_lead_duplication
from collector.models import Pixel
from utils.graphene import JSONDict


class LeadAuthenticity(graphene.ObjectType):
    authentic = graphene.Boolean()
    fields = JSONDict()
    error = graphene.String()


class LeadDuplication(graphene.ObjectType):
    # Провалено, Лид <дата создания=None> не существует в системе
    # Успешно, Лид <дата создания> никому не продавался
    # Успешно, Лид <дата создания> никому не продавался, аудировался вами
    # Провалено, Лид <дата создания> был продан N раз
    # Провалено, Лид <дата создания> был продан вам вне системы
    # Провалено, Лид <дата создания> не продавался, имеет N дубликатов
    # Провалено, Лид <дата создания> не продавался, имеет N дубликатов, аудировался вами
    # Провалено, Лид <дата создания> был продан N раз, имеет N дубликатов, аудировался вами
    success = graphene.Boolean()
    # словесное описание состояния лида
    resolution = graphene.String()
    # дата создания лида
    created = graphene.types.datetime.DateTime()
    # массив дат ваших аудирования лида
    your_audits = graphene.List(graphene.types.datetime.DateTime)
    # массив дат дубликатов лида с ваших пикселей
    duplicates = graphene.List(graphene.types.datetime.DateTime)
    # массив дат продаж лида - 1 дата на 1-го проверявшего или создавшего лид пользователя
    # [max(даты аудирования другим покупателем, даты создания если лид с чужого пикселя)]
    sales = graphene.List(graphene.types.datetime.DateTime)
    error = graphene.String()


class Query(graphene.ObjectType):
    lead_authenticity = graphene.Field(
        LeadAuthenticity,
        pixel_id=graphene.String(required=True),
        data=JSONDict(required=True)
    )

    lead_duplication = graphene.Field(
        LeadDuplication,
        data=JSONDict(required=True)
    )

    def resolve_lead_authenticity(self, info, pixel_id, data):
        user = info.context.user

        res = LeadAuthenticity()
        res.authentic = None
        res.fields = None
        res.error = None

        if not user.is_authenticated:
            res.error = _('Authentication required')
            return res

        try:
            pixel = Pixel.objects\
                .prefetch_related('fields_mapping')\
                .get(id=pixel_id, project__user=user)
        except Pixel.DoesNotExist:
            res.error = _('Permission denied')
            return res

        try:
            res.authentic, res.fields = check_lead_authenticity(pixel, data)
        except AuditError as e:
            res.error = str(e)

        return res

    def resolve_lead_duplication(self, info, data):
        user = info.context.user

        res = LeadDuplication()
        res.success = None
        res.resolution = None
        res.created = None
        res.your_audits = None
        res.duplicates = None
        res.sales = None
        res.error = None

        if not user.is_authenticated:
            res.error = _('Authentication required')
            return res

        try:
            res_dict = check_lead_duplication(user, data)
            for attr, value in res_dict.items():
                setattr(res, attr, value)
        except AuditError as e:
            res.error = str(e)

        return res