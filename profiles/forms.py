import re
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

User = get_user_model()


class RegistrationForm(forms.Form):
    company_name = forms.CharField(required=True)
    username = forms.EmailField(required=True)
    name = forms.CharField(required=False)
    password = forms.CharField(required=True)
    phone = forms.CharField(required=False)
    agreement = forms.BooleanField(required=True)

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if phone and not re.fullmatch(r'^\+7\(\d{3}\)-\d{3}-\d{2}-\d{2}$', phone):
            raise forms.ValidationError(_("Incorrect phone number"), 'incorrect_phone')
        return phone

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_("User with this email elaready exists"), 'username_exists')
        return username


class RecoveryForm(forms.Form):
    username = forms.EmailField(required=True)