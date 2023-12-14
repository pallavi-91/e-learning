from django.conf import settings


def constant(request):
    context = {
        "is_production": not settings.DEBUG
    }
    return context