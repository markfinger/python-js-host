# Django hook to configure the host during startup

from django.conf import settings
from . import conf

conf.settings.configure(
    **getattr(settings, 'JS_HOST', {})
)
