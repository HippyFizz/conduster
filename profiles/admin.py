from ckeditor.widgets import CKEditorWidget
from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from profiles.models import Profile, Message

User = get_user_model()


# Register your models here.
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')


class MessageAdminForm(forms.ModelForm):
    class Meta:
        model = Message
        exclude = ('read_by',)
        search_fields = ['receivers__username']

    text = forms.CharField(widget=CKEditorWidget())


class MessageAdmin(admin.ModelAdmin):
    form = MessageAdminForm


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Profile)
admin.site.register(Message, MessageAdmin)
