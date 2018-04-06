from django.conf.urls import url
from django.views.generic.base import TemplateView

from collector.views import collect_event, open_session, test_form, conduster_js

urlpatterns = [
    url(r'^test-form/', test_form, name="test-form"),
    url(r'^test-iframe/', TemplateView.as_view(template_name="collector/test_iframe.html")),
    url(r'^conduster.js', conduster_js, name="conduster_js"),
    url(r'^collect-event/', collect_event, name="collect-event"),
    url(r'^open-session/', open_session, name="open-session"),
]
