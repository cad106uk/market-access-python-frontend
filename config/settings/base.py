"""
Django settings for market_access_python_frontend project.

Generated by 'django-admin startproject' using Django 3.0.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import dj_database_url
import logging.config
import json
import os

from django.utils.log import DEFAULT_LOGGING

ROOT_DIR = os.path.abspath(os.path.dirname(__name__))

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load PaaS Service env vars
VCAP_SERVICES = json.loads(os.environ.get('VCAP_SERVICES', "{}"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = (os.environ.get("DEBUG", "false").lower() == 'true')

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")
# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.forms',
]

THIRD_PARTY_APPS = [
    "django_extensions",
    'compressor',
    'sass_processor',
]

LOCAL_APPS = [
    'barriers',
    'users',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'users.middleware.SSOMiddleware',
]

ROOT_URLCONF = 'config.urls'

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

SESSION_ENGINE = "users.sessions"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(ROOT_DIR, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'utils.context_processors.user_scope',
                'django_settings_export.settings_export',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": dj_database_url.config(env="DATABASE_URL", default="")
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(ROOT_DIR, "static")

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)

COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)

TRUSTED_USER_TOKEN = 'ssobypass'

METADATA_CACHE_TIME = "10600"

# CACHE / REDIS
# Try to read from PaaS service env vars first
REDIS_DB = os.environ.get("REDIS_DB", 4)
if "redis" in VCAP_SERVICES:
    REDIS_URI = VCAP_SERVICES["redis"][0]["credentials"]["uri"]
else:
    REDIS_URI = os.environ.get("REDIS_URI")
REDIS_URI = f"{REDIS_URI}/{REDIS_DB}"

# Market access API
MARKET_ACCESS_API_URI = os.environ.get("MARKET_ACCESS_API_URI", "unset")
MARKET_ACCESS_API_HAWK_ID = os.environ.get("MARKET_ACCESS_API_HAWK_ID")
MARKET_ACCESS_API_HAWK_KEY = os.environ.get("MARKET_ACCESS_API_HAWK_KEY")

MAX_WATCHLIST_LENGTH = 3

SETTINGS_EXPORT = [
    'DJANGO_ENV',
]

SSO_CLIENT = os.environ.get("SSO_CLIENT")
SSO_SECRET = os.environ.get("SSO_SECRET")
SSO_API_URI = os.environ.get("SSO_API_URI")
SSO_API_TOKEN = os.environ.get("SSO_API_TOKEN")
SSO_AUTHORIZE_URI = os.environ.get("SSO_AUTHORIZE_URI")
SSO_BASE_URI = os.environ.get("SSO_BASE_URI")
SSO_TOKEN_URI = os.environ.get("SSO_TOKEN_URI")
SSO_MOCK_CODE = os.environ.get("SSO_MOCK_CODE")
OAUTH_PARAM_LENGTH = os.environ.get("OAUTH_PARAM_LENGTH", 75)

ADD_COMPANY = os.environ.get("ADD_COMPANY", True)

DATAHUB_URL = os.environ.get("DATAHUB_URL")
DATAHUB_HAWK_ID = os.environ.get("DATAHUB_HAWK_ID", "")
DATAHUB_HAWK_KEY = os.environ.get("DATAHUB_HAWK_KEY", "")

FILE_MAX_SIZE = os.environ.get("FILE_MAX_SIZE", (5 * 1024 * 1024))
FILE_SCAN_MAX_WAIT_TIME = os.environ.get("FILE_SCAN_MAX_WAIT_TIME", 30000)
FILE_SCAN_STATUS_CHECK_INTERVAL = os.environ.get(
    "FILE_SCAN_STATUS_CHECK_INTERVAL",
    500
)

MAX_WATCH_LISTS = os.environ.get('MAX_WATCH_LISTS', 3)
MAX_WATCH_LIST_NAME_LENGTH = os.environ.get('MAX_WATCH_LIST_NAME_LENGTH', 25)

# Logging
# ============================================
DJANGO_LOG_LEVEL = os.environ.get("DJANGO_LOG_LEVEL", "info").upper()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "[%(asctime)s] %(name)s %(levelname)5s - %(message)s"
        },
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[%(asctime)s] %(message)s",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "console"},
        "django.server": DEFAULT_LOGGING['handlers']['django.server']

    },
    "loggers": {
        # default for all undefined Python modules
        '': {
            'level': DJANGO_LOG_LEVEL,
            'handlers': ['console'],
        },
        # application code
        "app": {
            "level": DJANGO_LOG_LEVEL,
            "handlers": ["console"],
            "propagate": True,
        },
        # Default runserver request logging
        'django.server': DEFAULT_LOGGING['loggers']['django.server'],
    },
}
