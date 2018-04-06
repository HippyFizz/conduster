import graphene
from django.conf import settings
from django.db.transaction import atomic
from django.utils.translation import ugettext as _
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from collector.models import Project, Pixel

User = get_user_model()


class ProjectType(DjangoObjectType):
    class Meta:
        model = Project
        only_fields = ('id','title', 'pixels')

    def resolve_pixels(self, info):
        return self.pixels.all().filter(removed=False)


class PixelType(DjangoObjectType):
    code = graphene.String()

    class Meta:
        model = Pixel

    def resolve_code(self, info):
        host = info.context.get_host() or 'dev-api.conduster.com'
        no_data = ', nodata: true' if not self.save_client_data else ''
        return """<script>window._cdrt = window._cdrt || {{ cid: '{pixel_id}'{no_data} }};</script>
<script async src="https://{host}/collector/conduster.js"></script>"""\
            .format(pixel_id=self.id, host=host, no_data=no_data)


class Query(graphene.ObjectType):
    all_projects = graphene.List(ProjectType)
    project = graphene.Field(ProjectType, id=graphene.String())

    def resolve_project(self, info, **args):
        if info.context.user.is_authenticated:
            return Project.objects.get(id=args.get('id'), user=info.context.user)

    def resolve_all_projects(self, info):
        if info.context.user.is_authenticated:
            return Project.objects.filter(user=info.context.user)


class EditProjectMutation(graphene.Mutation):
    class Arguments:
        id = graphene.String(required=True)
        title = graphene.String(required=True)

    project = graphene.Field(ProjectType)
    error = graphene.String()

    @staticmethod
    @atomic()
    def mutate(root, info, **kwargs):
        if info.context.user.is_authenticated:
            try:
                project = Project.objects.get(id=kwargs['id'], user=info.context.user)
                project.title = kwargs['title']
                project.save(force_update=True, update_fields=['title'])
                return EditProjectMutation(project=project, error=None)
            except Project.DoesNotExist:
                return EditProjectMutation(project=None, error=_('Project not found'))
        return EditProjectMutation(project=None, error=_('Authentication required'))


class CreateProjectMutation(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)

    project = graphene.Field(ProjectType)
    error = graphene.String()

    @staticmethod
    @atomic()
    def mutate(root, info, **kwargs):
        if info.context.user.is_authenticated:
            project = Project.objects.create(title=kwargs['title'], user=info.context.user)
            return CreateProjectMutation(project=project, error=None)
        return CreateProjectMutation(project=None, error=_('Authentication required'))


class DeleteProjectMutation(graphene.Mutation):
    class Arguments:
        id = graphene.String(required=True)

    id = graphene.String()
    error = graphene.String()

    @staticmethod
    @atomic()
    def mutate(root, info, **kwargs):
        if info.context.user.is_authenticated:
            try:
                project = Project.objects.get(id=kwargs['id'], user=info.context.user)
                project_id = project.id
                project.delete()
                return DeleteProjectMutation(id=project_id, error=None)
            except Project.DoesNotExist:
                return DeleteProjectMutation(id=None, error=_('Project not found'))
        return DeleteProjectMutation(id=None, error=_('Authentication required'))


class EditPixelMutation(graphene.Mutation):
    class Arguments:
        id = graphene.String(required=True)
        title = graphene.String(required=True)
        save_client_data = graphene.Boolean()

    pixel = graphene.Field(PixelType)
    error = graphene.String()

    @staticmethod
    @atomic()
    def mutate(root, info, **kwargs):
        if info.context.user.is_authenticated:
            try:
                pixel = Pixel.objects\
                    .select_related('project').get(id=kwargs['id'], project__user=info.context.user)
                pixel.title = kwargs['title']
                if 'save_client_data' in kwargs:
                    pixel.save_client_data = kwargs['save_client_data']
                pixel.save(force_update=True)
                return EditPixelMutation(pixel=pixel, error=None)
            except Pixel.DoesNotExist:
                return EditPixelMutation(pixel=None, error=_('Offer not found'))
        return EditPixelMutation(pixel=None, error=_('Authentication required'))


class CreatePixelMutation(graphene.Mutation):
    class Arguments:
        project_id = graphene.String(required=True)
        title = graphene.String(required=True)

    pixel = graphene.Field(PixelType)
    error = graphene.String()

    @staticmethod
    @atomic()
    def mutate(root, info, **kwargs):
        if info.context.user.is_authenticated:
            try:
                project = Project.objects.get(id=kwargs['project_id'], user=info.context.user)
                pixel = Pixel.objects.create(project=project, title=kwargs['title'])
                return CreatePixelMutation(pixel=pixel, error=None)
            except Project.DoesNotExist:
                return CreatePixelMutation(pixel=None, error=_('Project not found'))
        return CreatePixelMutation(pixel=None, error=_('Authentication required'))


class DeletePixelMutation(graphene.Mutation):
    class Arguments:
        id = graphene.String(required=True)

    id = graphene.String()
    error = graphene.String()

    @staticmethod
    @atomic()
    def mutate(root, info, **kwargs):
        if info.context.user.is_authenticated:
            try:
                pixel = Pixel.objects\
                    .select_related('project').get(id=kwargs['id'], project__user=info.context.user)
                pixel.removed = True
                pixel.save(force_update=True, update_fields=['removed'])
                return DeletePixelMutation(id=pixel.id, error=None)
            except (Pixel.DoesNotExist, Project.DoesNotExist):
                return DeletePixelMutation(id=None, error=_('Offer not found'))
        return DeletePixelMutation(id=None, error=_('Authentication required'))


class Mutations(graphene.ObjectType):
    edit_project = EditProjectMutation.Field()
    create_project = CreateProjectMutation.Field()
    delete_project = DeleteProjectMutation.Field()

    edit_pixel = EditPixelMutation.Field()
    create_pixel = CreatePixelMutation.Field()
    delete_pixel = DeletePixelMutation.Field()
