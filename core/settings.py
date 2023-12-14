"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 4.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import logging
import os
from pathlib import Path
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

from huey import MemoryHuey, SqliteHuey, RedisHuey
from redis import ConnectionPool
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY','django-insecure-ffm+f#f(xfk)4^a6foqp^+&((6)7%)d_kf_gnpyhl5k_#=yde2')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = eval(os.environ.get('DEBUG', "True"))


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'drf_standardized_errors',
    'storages',
    'apps.users.apps.UsersConfig',
    'apps.courses.apps.CoursesConfig',
    'apps.shares.apps.SharesConfig',
    'apps.currency.apps.CurrencyConfig',
    'apps.countries.apps.CountriesConfig',
    'apps.transactions.apps.TransactionsConfig',
    'apps.statements.apps.StatementsConfig',
    'apps.coupons.apps.CouponsConfig',
    'apps.geopricing.apps.GeoPricingConfig',
    'django_extensions',
    'nested_inline',
    # 'nplusone.ext.django',
    'corsheaders',
    'huey.contrib.djhuey',
    'apps.notifications.apps.NotificationsConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # Cors
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    # 'nplusone.ext.django.NPlusOneMiddleware',
]
CORS_ORIGIN_ALLOW_ALL = True 


REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.BasicAuthentication', # For Docs
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'drf_nested_forms.parsers.NestedMultiPartParser',
        'drf_nested_forms.parsers.NestedJSONParser',
        'rest_framework.parsers.FormParser',
        # so this settings will work in respective of a nested request
    ],
    "EXCEPTION_HANDLER": "drf_standardized_errors.handler.exception_handler",
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'SEARCH_PARAM': 'search',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ]
}

DRF_STANDARDIZED_ERRORS = {"ENABLE_IN_DEBUG_FOR_UNHANDLED_EXCEPTIONS": True}

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context.constant',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.ScryptPasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {'NAME': 'core.password_validator.NumberValidator',
        'OPTIONS': {
            'min_digits': 3, 
        }},
    {'NAME': 'core.password_validator.UppercaseValidator', },
    {'NAME': 'core.password_validator.LowercaseValidator', },
    {'NAME': 'core.password_validator.SymbolValidator', },
]

AUTH_USER_MODEL = 'users.User'

AUTH_TOKEN_EXPIRY_TIME = 60# Hours


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / MEDIA_URL

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / STATIC_URL

from core.store.storage_conf import * # Storage configurations

# Bestseller criteria 
SOLD_PER_MONTH = 100

# Password validations
PASSWORD_MIN_LENGTH = 8

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# increase max number fields for quill delta 
# https://docs.djangoproject.com/en/4.1/ref/settings/#data-upload-max-number-fields
DATA_UPLOAD_MAX_NUMBER_FIELDS = 12240

# Set any settings based on the environment by the application debug state 

try:
    if DEBUG:
        from .dev import *
    else:
        from .prod import *
except ImportError as e:
    raise e


NPLUSONE_LOGGER = logging.getLogger('nplusone')
NPLUSONE_LOG_LEVEL = logging.WARN
# Domain name

SITE_PROTOCOL = "https://"
SITE_DOMAIN_URL = os.environ.get("SITE_DOMAIN_URL")
SITE_URL = f"{SITE_PROTOCOL}{SITE_DOMAIN_URL}"
ALLOWED_HOSTS = (SITE_DOMAIN_URL, '*')

# Currency
PRIMARY_CURRENCY_CODE = {
    'exchange_rate_currency' : 'USD',
    'store_currency' : 'USD',
    'exchange_rate_currency_symbol': '$'
}

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")

pool = ConnectionPool(host=REDIS_HOST, port=6379, max_connections=20)
HUEY = RedisHuey('task-app', connection_pool=pool)

# Rect(x0, y0, x1, y1), top-left, bottom-right
# Width = x1-x0
# Height = y1-y0

EN_CERT_FIELDS = {
    '[certificate-no]': (210.47789001464844, 96, 270.2599792480469, 105),
    '[certificate-url]': (210.47789001464844, 106, 270.2599792480469, 118.36585235595703),
    '[full-name]': (294.20001220703125, 259.8966979980469, 547.5325927734375, 312.5848083496094),
    '[course-title]': (470.0799865722656, 328.78101806640625, 581.087646484375, 353.0530090332031),
    '[instructor-signature]': (550.1799926757812, 450.91400146484375, 686.8724365234375, 477.8940124511719),
    '[instructor-name]': (540.1400146484375, 483.0539855957031, 648.6336059570312, 497.03399658203125),
    '[complete-date]': (171.74000549316406, 459.65399169921875, 249.79603576660156, 476.6340026855469),
}

DATA_UPLOAD_MAX_MEMORY_SIZE = None