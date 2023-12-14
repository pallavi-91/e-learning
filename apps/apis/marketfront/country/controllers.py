from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from apps.utils.query import SerializerProperty
from .serializers import CountryResourceSerializer

class CountryResourceView(SerializerProperty, ViewSet):
    """ lecture resources
    """
    public_actions = ['list']
    serializer_class = CountryResourceSerializer

    def list(self, request, **kwargs):
        serializer = self.serializer_class(
            self._model.objects.all(),
            many=True
        )
        return Response(serializer.data, status=200)

