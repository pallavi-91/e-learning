from core.secrets import get_secrets
secrets = get_secrets()
from datetime import timedelta

CLOUDFLARE_API_TOKEN = secrets.get('CLOUDFLARE-API-TOKEN')
CLOUDFLARE_ACCOUNT_ID = secrets.get('CLOUDFLARE-ACCOUNT-ID')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': secrets.get('DEV-DB-NAME'),
        'USER': secrets.get('DEV-DB-USERNAME'),
        'PASSWORD': secrets.get('DEV-DB-PASSWORD'),
        'HOST': secrets.get('DEV-DB-HOST'),
        'PORT': secrets.get('DEV-DB-PORT'),
    }
}

# Paypal integration
# https://developer.paypal.com/developer/applications

PAYPAL_PAYOUT_SUBJECT = "You have a sandbox payout!"
PAYPAL_PAYOUT_MESSAGE = "You have received a sandbox payout! Thanks for using our service!"

PAYPAL_URL = secrets.get("PAYPAL-SANDBOX-URL")
PAYPAL_API_URL = secrets.get("PAYPAL-SANDBOX-API-URL")
PAYPAL_CLIENT_ID = secrets.get("PAYPAL-SANDBOX-CLIENT-ID")
PAYPAL_CLIENT_SECRET = secrets.get("PAYPAL-SANDBOX-CLIENT-SECRET")

# Email configuration
# https://docs.djangoproject.com/en/3.1/topics/email/

DEFAULT_FROM_EMAIL = 'Thkee <earvin.gemenez@gmail.com>'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = secrets.get('SENDGRID-API-KEY')
EMAIL_USE_TLS = True
EMAIL_PORT = 587

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=15),
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'AUTH_HEADER_TYPES': ('Bearer',),
}

REFUND_PERIOD_THRESHOLD=30 # less than days
REFUND_COURSE_THRESHOLD=30 # less than x% completed

PAYOUT_THRESHOLD = 30 #days

# Quickbooks details
QUICKBOOKS_CLIENT_ID = secrets.get('QUICKBOOKS_CLIENT_ID',"ABWXSUw8KfM84EGnRh0wjrVsnXXTGzKNlYdn1umfqLsDyeL4p9")
QUICKBOOKS_CLIENT_SECRET = secrets.get('QUICKBOOKS_CLIENT_SECRET',"dVbaJVBrRSYxruZ5cyZJJKDFBksmjZJdEcY4gySe")
QUICKBOOKS_COMPANY_ID = secrets.get('QUICKBOOKS_COMPANY_ID',"4620816365264620940")
QUICKBOOKS_REFRESH_TOKEN = secrets.get('QUICKBOOKS_REFRESH_TOKEN',"AB11684251896a6FKLwgsiWwK4mBgWgV8XJQp5D8n2qCgdZ9p8")


CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}