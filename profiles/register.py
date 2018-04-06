# -*- coding: utf-8 -*-
import logging
import re

from django.utils.translation import ugettext as _
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.transaction import atomic
from rest_framework_jwt.serializers import jwt_payload_handler, jwt_encode_handler

from profiles.forms import RegistrationForm, RecoveryForm
from profiles.models import Profile

logger = logging.getLogger(__name__)

User = get_user_model()


class RegisterError(Exception):
    """
    Errors during register process
    """
    pass


class RegisterService:

    @staticmethod
    def _split_user_fullname(name):
        name_arr = name.split(' ', 1)
        if len(name_arr) < 2:
            name_arr.append('')
        return name_arr

    @classmethod
    def _send_register_mail(cls, user):
        try:
            send_mail(
                subject=_('Thank you for your registartion on Conduster'),
                message=_("""Please follow next link to confirm your registration
https://dev.conduster.com/signup/confirm/{code_hash}
or provide this code {code} on confirtmation form https://dev.conduster.com/signup/confirm/"""
                          ).format(code_hash=user.profile.activation_code_hash,
                           code=user.profile.activation_code),
                from_email=settings.EMAIL_FROM,
                recipient_list=[user.username],
                fail_silently=False
            )
        except Exception as e:
            logger.warning("Unuable to send email to {}".format(user.username))
            logger.exception(e)

    @atomic()
    def register_user(self, **kwargs):
        form = RegistrationForm(kwargs)
        if form.is_valid():
            email = form.cleaned_data['username']
            f_name, l_name = self._split_user_fullname(form.cleaned_data['name'])
            user = User.objects.create_user(
                username=email,
                email=email,
                password=form.cleaned_data['password'],
                first_name=f_name,
                last_name=l_name,
                is_active=False
            )
            profile = Profile(
                user=user,
                company_name=form.cleaned_data['company_name'],
                phone=form.cleaned_data['phone']
            )
            profile.activation_code = Profile.generate_activation_code()
            profile.activation_code_hash = Profile.make_code_hash(profile.activation_code)
            profile.save()
            self._send_register_mail(user)
            return user
        else:
            for f, err in form.errors.items():
                raise RegisterError(err[0])

    @atomic()
    def _confirm_by(self, code_val, code_re, code_field):
        if not re.fullmatch(code_re, code_val):
            raise RegisterError(_('Invalid confirmation code'))
        try:
            profiles = Profile.objects.select_related('user')\
                .filter(**{code_field: code_val})\
                .order_by('user__is_active')
            if len(profiles) == 0:
                raise RegisterError(_('Invalid confirmation code'))
            if len(profiles) > 0 and  profiles[0].user.is_active:
                raise RegisterError(_('Account already activated'))
            profile = profiles[0]
            user= profile.user
            user.is_active = True
            user.save()

            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)

            return profile.user, token
        except Profile.DoesNotExist:
            raise RegisterError(_('Invalid confirmation code'))

    def confirm_by_code(self, code):
        return self._confirm_by(code, r'^\d{4}$', 'activation_code')

    def confirm_by_code_hash(self, code_hash):
        return self._confirm_by(code_hash, r'^[a-zA-Z0-9]{40}$', 'activation_code_hash')

    @classmethod
    def _send_recovery_mail(cls, user):
        try:
            send_mail(
                subject=_('Conduster password recovery'),
                message=_("""Follow this link to reset your password 
https://dev.conduster.com/recovery/confirm/{code_hash}
or provide this code {code} on recovery confirmation form https://dev.conduster.com/recovery/confirm/
Just ignore this letter if didn't request password recovery.

Best regards,
Conduster support""").format(code_hash=user.profile.recovery_hash,
                           code=user.profile.recovery_code),
                from_email=settings.EMAIL_FROM,
                recipient_list=[user.username],
                fail_silently=False
            )
        except Exception as e:
            logger.warning("Unuable to send email to {}".format(user.username))
            logger.exception(e)

    @atomic()
    def recover(self, **kwargs):
        form = RecoveryForm(kwargs)
        if form.is_valid():
            try:
                user = User.objects.get(username=form.cleaned_data['username'])
                profile = user.profile
                profile.recovery_code = Profile.generate_recovery_code()
                profile.recovery_hash = Profile.make_code_hash(profile.recovery_code)
                profile.save()
                self._send_recovery_mail(user)
                return True
            except User.DoesNotExist:
                raise RegisterError(_("User with this email is not found"))
        else:
            for f, err in form.errors.items():
                raise RegisterError(err[0])

    @atomic()
    def _recover_by(self, code_val, password, confirm_password, code_re, code_field):
        if not re.fullmatch(code_re, code_val):
            raise RegisterError(_('Invalid recovery code'))
        try:

            profiles = Profile.objects.select_related('user')\
                .filter(**{code_field: code_val})\
                .order_by('-user__is_active')
            if len(profiles) == 0:
                raise RegisterError(_('Invalid recovery code'))
            if len(profiles) > 0 and not profiles[0].user.is_active:
                raise RegisterError(_('Account is not active'))

            profile = profiles[0]
            user = profile.user
            token = None
            if password:
                if password != confirm_password:
                    raise RegisterError(_('Password mismatch'))

                user.set_password(password)
                user.save()
                profile.recovery_code = None
                profile.recovery_hash = None
                profile.save()

                payload = jwt_payload_handler(user)
                token = jwt_encode_handler(payload)
            return user, token
        except Profile.DoesNotExist:
            raise RegisterError(_('Invalid confirmation code'))

    def recover_by_code(self, code, password, confirm_password):
        return self._recover_by(code, password, confirm_password, r'^\d{4}$', 'recovery_code')

    def recover_by_code_hash(self, code_hash, password, confirm_password):
        return self._recover_by(code_hash, password, confirm_password, r'^[a-zA-Z0-9]{40}$', 'recovery_hash')
