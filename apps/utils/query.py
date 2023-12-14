from django.apps import apps
from django.db.models.base import Model
from django.db.models.query import QuerySet
from django.shortcuts import _get_queryset
from django.utils import timezone

from core.authentications import AnyUserAuthentication


def get_object_or_none(klass, *args, **kwargs):
    """ try to return the class instance and
        return None if none existent.
    """
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None


class SerializerProperty(object):

    def __init__(self, *args, **kwargs):
        return super(SerializerProperty, self).__init__(*args, **kwargs)

    @property
    def _model(self) -> Model:
        return self.serializer_class.Meta.model

    def inject_authuser(self, data):
        return {'user': self.request.user.id, **data}



    def initialize_request(self, request, *args, **kwargs):
        """ fix self.action to get assign first before the get_authenticators """
        self.action = self.action_map.get(request.method.lower())
        return super().initialize_request(request, *args, **kwargs)


    public_actions = []
    permission_classes_by_action = {}
    authentication_classes_by_action = {}

    def get_permissions(self):
        if self.action in self.public_actions: return []

        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]


    def get_authenticators(self):
        if self.action in self.public_actions: return [AnyUserAuthentication()]
        
        try:
            # return authentication_classes depending on `action`
            return [authentication() for authentication in self.authentication_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default authentication_classes
            return [authentication() for authentication in self.authentication_classes]


class InjectUserToData(object):
    """ inject the auth user's id into
        the `request.data`
    """
    def dispatch(self, request, *args, **kwargs):
        super().dispatch(request, *args, **kwargs)

        # inject user's id into the request data
        request.POST._mutable = True
        request.POST.update({'user': request.user.id})

        return super().dispatch(request, *args, **kwargs)


def get_model(appdotmodel):
    """ get the model without importing it on
        the file. this is to prevent circular importing
    """
    return apps.get_model(appdotmodel)
