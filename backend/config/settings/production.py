from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = env.bool("DJANGO_DEBUG")  # noqa: F405
if DEBUG:
    raise ImproperlyConfigured("DJANGO_DEBUG must be false in production.")

if SECRET_KEY == "local-development-only-change-me":  # noqa: F405
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY for production.")
if not ALLOWED_HOSTS:  # noqa: F405
    raise ImproperlyConfigured("Set DJANGO_ALLOWED_HOSTS for production.")

SECURE_PROXY_SSL_HEADER = (
    env("SECURE_PROXY_SSL_HEADER_NAME"),  # noqa: F405
    env("SECURE_PROXY_SSL_HEADER_VALUE"),  # noqa: F405
)
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT")  # noqa: F405
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE")  # noqa: F405
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE")  # noqa: F405
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS")  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS")  # noqa: F405
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD")  # noqa: F405
