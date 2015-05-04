import sys

if 'nosetests' in sys.argv[0]:
    # Configure settings manually
    from .settings import JS_HOST
    from js_host.conf import settings
    settings.configure(**JS_HOST)