import json

import graphene

from graphene_django import DjangoObjectType

from xflatpages.models import XFlatPage


class XFlatPageType(DjangoObjectType):
    class Meta:
        model = XFlatPage


class Query(graphene.ObjectType):
    xflatpage = graphene.Field(XFlatPageType, url=graphene.String())
    all_xflatpages = graphene.List(XFlatPageType)

    def resolve_all_xflatpages(self, info, **kwargs):
        return XFlatPage.objects.all()

    def resolve_xflatpage(self, info, **kwargs):
        url = kwargs.get('url')
        if url is not None:
            try:
                return XFlatPage.objects.get(url=url)
            except XFlatPage.DoesNotExist:
                return None
        return None