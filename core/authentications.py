from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication

class AnyUserAuthentication(JWTAuthentication):
    """
    An authentication plugin that authenticates requests through a JSON web
    token provided in a request header.
    """
    www_authenticate_realm = "api"
    media_type = "application/json"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    