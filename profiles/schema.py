import graphene
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import ugettext as _
from django_countries import countries
from graphene_django import DjangoObjectType

from profiles.models import PageFilters
from profiles.register import RegisterService, RegisterError
from .models import Profile, Message

User = get_user_model()


class UserType(DjangoObjectType):
    class Meta:
        model = User
        interfaces = (graphene.Node,)


class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile


class MessageType(DjangoObjectType):
    class Meta:
        model = Message
        only_fields = (
            'id',
            'author',
            'm_type',
            'title',
            'text',
            'create_at'
        )


class Query(graphene.ObjectType):
    user = graphene.Field(UserType)
    user_profile = graphene.Field(ProfileType)
    user_messages = graphene.List(
        MessageType,
        seen_only=graphene.Boolean(required=False),
        new_only=graphene.Boolean(required=False)
    )
    user_unread_messages_count = graphene.Int()
    countries = graphene.List(graphene.types.json.JSONString)
    page_filters = graphene.String(
        page=graphene.String(required=True)
    )

    def resolve_user(self, info):
        if info.context.user.is_authenticated:
            return info.context.user
        return None

    def resolve_user_profile(self, info):
        if info.context.user.is_authenticated:
            return info.context.user.profile
        return None

    def resolve_user_messages(self, info, **kwargs):
        if not info.context.user.is_authenticated:
            return None
        message_qs = info.context.user.profile.all_messages
        if kwargs.get('seen_only'):
            return info.context.user.profile.user.seen_messages.all()
        return info.context.user.profile.all_messages.all()

    def resolve_user_unread_messages_count(self, info):
        if not info.context.user.is_authenticated:
            return None
        message_qs = info.context.user.profile.all_messages.all()
        message_qs = message_qs.difference(info.context.user.seen_messages.all())
        return message_qs.count()

    def resolve_countries(self, info):
        return [{'key': c[0], 'full_name': c[1]} for c in countries]

    def resolve_page_filters(self, info, page):
        user = info.context.user
        if user.is_authenticated:
            return PageFilters.objects.filter(user=user, page=page).values_list('filters', flat=True).first()
        return None


class UpdateUserProfile(graphene.Mutation):
    class Arguments:
        company_name = graphene.String(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
        position = graphene.String()
        phone = graphene.String()
        address = graphene.String()
        country = graphene.String()
        site = graphene.String()
        industry = graphene.String()
        business = graphene.String()

    profile = graphene.Field(ProfileType)
    error = graphene.String()

    @staticmethod
    def mutate(root, info, **kwargs):
        if info.context.user.is_authenticated:
            user = info.context.user
            profile = Profile.objects.get(user=user)
            profile.phone = kwargs.get('phone')
            profile.address = kwargs.get('address')
            profile.position = kwargs.get('position')
            profile.company_name = kwargs.get('company_name')
            profile.country = kwargs.get('country')
            profile.site = kwargs.get('site')
            profile.industry = kwargs.get('industry')
            profile.business = kwargs.get('business')
            user.first_name = kwargs.get('first_name')
            user.last_name = kwargs.get('last_name')
            profile.save()
            user.save()
            return UpdateUserProfile(profile=profile, error=None)
        return UpdateUserProfile(profile=None, error=_('Authentication required'))


class RegisterUserMutation(graphene.Mutation):
    class Arguments:
        company_name = graphene.String(required=True)
        name = graphene.String(required=False)
        password = graphene.String(required=True)
        username = graphene.String(required=True)
        phone = graphene.String(required=False)
        agreement = graphene.Boolean(required=True)

    user = graphene.Field(UserType)
    error = graphene.String()

    @staticmethod
    def mutate(root, info, **kwargs):
        try:
            service = RegisterService()
            user = service.register_user(**kwargs)
            return RegisterUserMutation(user=user, error=None)
        except RegisterError as e:
            return RegisterUserMutation(user=None, error=str(e))


class ConfirmByCodeMutation(graphene.Mutation):
    class Arguments:
        code = graphene.String(required=True)

    user = graphene.Field(UserType)
    token = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, **kwargs):
        try:
            service = RegisterService()
            user, token = service.confirm_by_code(**kwargs)
            return ConfirmByCodeMutation(user=user, token=token, error=None)
        except RegisterError as e:
            return ConfirmByCodeMutation(user=None, token=None, error=str(e))


class ConfirmByCodeHashMutation(graphene.Mutation):
    class Arguments:
        code_hash = graphene.String(required=True)

    user = graphene.Field(UserType)
    token = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, **kwargs):
        try:
            service = RegisterService()
            user, token = service.confirm_by_code_hash(**kwargs)
            return ConfirmByCodeHashMutation(user=user, token=token, error=None)
        except RegisterError as e:
            return ConfirmByCodeHashMutation(user=None, token=None, error=str(e))


class RecoveryMutation(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, **kwargs):
        try:
            service = RegisterService()
            success = service.recover(**kwargs)
            return RecoveryMutation(success=success, error=None)
        except RegisterError as e:
            return RecoveryMutation(success=None, error=str(e))


class UpdatePasswordMutation(graphene.Mutation):
    class Arguments:
        current_password = graphene.String(required=True)
        password = graphene.String(required=True)
        confirm_password = graphene.String()

    success = graphene.Boolean()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, **kwargs):
        if kwargs.get('password') != kwargs.get('confirm_password'):
            return UpdatePasswordMutation(success=False,
                                          error=_("Password and password confirmation are not the same"))

        user = authenticate(username=info.context.user.username,
                            password=kwargs.get('current_password'))
        if user:
            user.set_password(kwargs.get('password'))
            user.save()
            return UpdatePasswordMutation(success=True, error=None)
        return UpdatePasswordMutation(success=False, error=_("Current password mismatch"))


class RecoverByCodeMutation(graphene.Mutation):
    class Arguments:
        code = graphene.String(required=True)
        password = graphene.String()
        confirm_password = graphene.String()

    user = graphene.Field(UserType)
    token = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, **kwargs):
        try:
            service = RegisterService()
            user, token = service.recover_by_code(**kwargs)
            return RecoverByCodeMutation(user=user, token=token, error=None)
        except RegisterError as e:
            return RecoverByCodeMutation(user=None, token=None, error=str(e))


class RecoverByCodeHashMutation(graphene.Mutation):
    class Arguments:
        code_hash = graphene.String(required=True)
        password = graphene.String()
        confirm_password = graphene.String()

    user = graphene.Field(UserType)
    token = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, **kwargs):
        try:
            service = RegisterService()
            user, token = service.recover_by_code_hash(**kwargs)
            return RecoverByCodeHashMutation(user=user, token=token, error=None)
        except RegisterError as e:
            return RecoverByCodeHashMutation(user=None, token=None, error=str(e))


class SavePageFilters(graphene.Mutation):
    class Arguments:
        page = graphene.String(required=True)
        filters = graphene.String(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, page, filters):
        user = info.context.user
        if user.is_authenticated:
            PageFilters.objects.update_or_create(
                user=user,
                page=page,
                defaults={'filters': filters}
            )
            return SavePageFilters(success=True, error=None)
        return SavePageFilters(success=False, error=_('Authentication required'))


class ReadMessageByUser(graphene.Mutation):
    class Arguments:
        message_id = graphene.Int(required=True)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, info, message_id):
        if not info.context.user.is_authenticated:
            return None
        try:
            message = Message.objects.get(id=message_id)
            message.read_by_profile(info.context.user.profile)
        except Profile.DoesNotExist:
            message = False
        return ReadMessageByUser(success=message if not message else True)


class Mutations(graphene.ObjectType):
    register_user = RegisterUserMutation.Field()
    confirm_by_code = ConfirmByCodeMutation.Field()
    confirm_by_code_hash = ConfirmByCodeHashMutation.Field()
    recovery = RecoveryMutation.Field()
    recover_by_code = RecoverByCodeMutation.Field()
    recover_by_code_hash = RecoverByCodeHashMutation.Field()
    update_password = UpdatePasswordMutation.Field()
    update_user_profile = UpdateUserProfile.Field()
    save_page_filters = SavePageFilters.Field()
    read_message_by_user = ReadMessageByUser.Field()
