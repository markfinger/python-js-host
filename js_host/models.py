# Django configuration hook

from django.conf import settings
from . import conf

conf.settings.configure(
    **getattr(settings, 'JS_HOST', {})
)
