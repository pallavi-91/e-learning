from django.conf import settings
from apps.utils.http import urlsafe

# SITE API URL
SITE_API_URL = settings.SITE_URL

# ORDERS
PAYPAL_ORDERS_URL = urlsafe(settings.PAYPAL_API_URL, 'v2', 'checkout', 'orders')