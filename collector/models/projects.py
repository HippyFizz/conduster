import uuid
from django.db import models
from django.db.models.deletion import SET_NULL, CASCADE, PROTECT
from django.contrib.auth import get_user_model

from collector.models.dictionaries import Field

User = get_user_model()


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, related_name="projects", on_delete=CASCADE)
    title = models.CharField(max_length=128)
    tag = models.CharField(max_length=128, blank=True, null=True, default=None)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{0}: {1} ({2})".format(self.user.username, self.title, self.tag)


class Pixel(models.Model):
    """
    Pixels (Offers)
    """
    LEAD_TYPES = (
        ("mortgage", "ипотека"),
        ("cash loan", "кредит наличными"),
        ("credit card", "кредитная карта"),
        ("business credit", "кредит на бизнес"),
        ("micro loan", "микро-заём"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, related_name='pixels',
                                null=True, blank=True, on_delete=SET_NULL)
    title = models.CharField(max_length=128)
    save_client_data = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    lead_type = models.CharField(max_length=100, choices=LEAD_TYPES, null=True, blank=True)
    removed = models.BooleanField(default=False)

    def __str__(self):
        project_title = self.project.title if self.project else None
        return "{0}: {1} ({2})".format(project_title, self.id, self.title)


class FieldMapping(models.Model):
    """
    map fields for pixel to check_lead
    """
    pixel = models.ForeignKey(Pixel, related_name='fields_mapping', on_delete=CASCADE)
    target_field = models.ForeignKey(Field, related_name='fields_mapping', on_delete=PROTECT)
    html_tag = models.CharField(max_length=30)
    html_attr_name = models.CharField(max_length=50)
    html_attr_value = models.CharField(max_length=50)
    required = models.BooleanField(default=True)
    description = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return "{0} {1}".format(self.pixel.title, self.target_field)

    def find_event(self, form_data):
        for event in form_data.values():
            html_attr_name = self.html_attr_name.lower()
            html_attr_value = self.html_attr_value.lower()
            try:
                event_attr_value = getattr(event, 'field_'+html_attr_name)
            except AttributeError:
                continue
            if event.field_tag.lower() == self.html_tag.lower() \
                    and event_attr_value == html_attr_value:
                return event
        return None
