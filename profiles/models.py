import hashlib
import random

from ckeditor.fields import RichTextField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.deletion import CASCADE
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=CASCADE, related_name='profile')
    company_name = models.CharField(max_length=512, default='unknown')
    phone = models.CharField(max_length=50, null=True, blank=True)
    # TODO удалить и сделать группы по-человечески
    country = models.CharField(max_length=50, null=True, blank=True)
    position = models.CharField(max_length=50, null=True, blank=True)
    site = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=120, null=True, blank=True)
    industry = models.CharField(max_length=50, null=True, blank=True)
    business = models.CharField(max_length=50, null=True, blank=True, default=None)
    # some weird stuff here
    activation_code = models.CharField(max_length=4, null=True, blank=True, db_index=True)
    activation_code_hash = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    recovery_code = models.CharField(max_length=4, null=True, blank=True, db_index=True)
    recovery_hash = models.CharField(max_length=40, null=True, blank=True, db_index=True)

    def __str__(self):
        return "%s" % (self.user.username)

    @property
    def all_messages(self):
        message_qs = Message.objects.all()
        for group in self.user.groups.all():
            message_qs.filter(groups=group)
        return message_qs

    @classmethod
    def _generate_code(cls):
        """

        :return:

        >>> len(Profile._generate_code())
        4
        """
        code = str(random.randint(1, 10000))
        return cls._pad_code(code)

    @classmethod
    def generate_activation_code(cls):
        code = None
        while True:
            code = cls._generate_code()
            if not cls.objects.select_related('user').filter(activation_code=code, user__is_active=False).exists():
                break
        return code

    @classmethod
    def generate_recovery_code(cls):
        code = None
        while True:
            code = cls._generate_code()
            if not cls.objects.filter(recovery_code=code).exists():
                break
        return code

    @staticmethod
    def _pad_code(code, max_digits=4):
        """

        :param code:
        :param max_digids:
        :return:

        >>> Profile._pad_code('6543')
        '6543'
        >>> Profile._pad_code('543')
        '0543'
        >>> Profile._pad_code('43')
        '0043'
        >>> Profile._pad_code('3')
        '0003'
        >>> Profile._pad_code('')
        '0000'
        """
        return (max_digits - len(code)) * '0' + code

    @staticmethod
    def make_code_hash(code):
        """

        :param code:
        :return:

        >>> len(Profile.make_code_hash('0123'))
        40
        """
        return hashlib.sha1((settings.ACTIVATION_SALT + code).encode('utf-8')).hexdigest()

    @property
    def unread_messages_count(self):
        return len(self.user.seen_messages.all())

    def update_message_list(self):
        messages = Message.objects.filter(groups__in=self.user.groups.all())
        self.user.all_messages.set(messages)

    def save(self, *args, **kwargs):
        if self.pk:
            super(Profile, self).save(*args, **kwargs)
            self.update_message_list()
            return
        try:
            profile_exist = Profile.objects.get(user=self.user)
        except Profile.DoesNotExist:
            super(Profile, self).save(*args, **kwargs)
            self.update_message_list()
            return
        self.pk = profile_exist.pk
        profile_exist = self
        self.update_message_list()
        profile_exist.save()


def get_conduster_bot():
    return User.objects.get(username='condusterBot')


class Message(models.Model):
    TYPES_CHOICES = (
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('alert', 'Alert'),
    )

    STATUSES_CHOICES = (
        ('delayed', 'Delayed'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )

    author = models.ForeignKey(User, on_delete=CASCADE, null=False, default=get_conduster_bot)
    m_type = models.CharField(max_length=20, choices=TYPES_CHOICES, null=False)
    title = models.CharField(max_length=120, null=False)
    text = RichTextField()
    create_at = models.DateTimeField(db_index=True, auto_now_add=True)
    status = models.CharField(null=False, max_length=20, choices=STATUSES_CHOICES, default='delayed')

    receivers = models.ManyToManyField(User, related_name='all_messages', blank=True)
    groups = models.ManyToManyField(Group, related_name='messages', blank=True)
    read_by = models.ManyToManyField(User, related_name='seen_messages', blank=True)

    def read_by_profile(self, profile):
        if self not in profile.all_messages.all():
            raise ValidationError(
                _('%(value)s is not in message receivers list'),
                params={'value': profile.user.username},
            )
        self.read_by.add(profile.user)

    def __str__(self):
        return f"{self.title}"


class PageFilters(models.Model):
    """
    Conatin get params for filters for pages for user
    """
    user = models.ForeignKey(User, on_delete=CASCADE)
    page = models.CharField(max_length=100)
    filters = models.TextField()

    class Meta:
        unique_together = ('user', 'page')


@receiver(post_save, sender=User)
def user_profile_exist(sender, instance, created, *args, **kwargs):
    """
    If after save object of class User doesn't have
    any profile related we create new empty profile
    """
    if created:
        if not instance.groups.all():
            default_groups = Group.objects.filter(Q(name='advertisers') | Q(name='base'))
            instance.groups.set(default_groups)
        try:
            Profile.objects.get(user=instance)
        except Profile.DoesNotExist:
            Profile.objects.create(user=instance)

# @receiver(post_save, sender=Message)
# def fill_receivers(sender, instance, created, *args, **kwargs):
#     user_qs = User.objects.filter(groups__in=instance.groups.all())
#     user_qs = user_qs.exclude(id__in=instance.receivers.all())
#     user_qs = user_qs.exclude(profile__isnull=True)
#     for user in user_qs:
#         instance.receivers.add(user.profile)
