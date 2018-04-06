import graphene

from graphene_django.debug import DjangoDebug

import profiles.schema
import xflatpages.schema
import collector.schema
import audit.schema


class Queries(profiles.schema.Query, xflatpages.schema.Query,
              collector.schema.Query, audit.schema.Query,
              graphene.ObjectType):
    pass


class Mutations(collector.schema.Mutations, profiles.schema.Mutations, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Queries, mutation=Mutations)