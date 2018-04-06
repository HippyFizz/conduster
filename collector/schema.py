import graphene

from collector.projects_schema import Query as ProjectsQuery, Mutations as ProjectsMutations
from collector.analytics_schema import Query as AnalyticsQuery


class Query(ProjectsQuery, AnalyticsQuery, graphene.ObjectType):
    pass


class Mutations(ProjectsMutations, graphene.ObjectType):
    pass