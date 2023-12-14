from django.apps import AppConfig


class CurrencyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.currency'

    def ready(self):
        from .models import init_currency_code
        init_currency_code()