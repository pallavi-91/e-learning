from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from rest_framework.serializers import Serializer, ModelSerializer
from apps.countries.models import Country

class CountryResourceSerializer(ModelSerializer):
    """ Country resource serializer
    """
    class Meta:
        model = Country
        fields = ['id', 'name', 'two_letter_iso_code', 'three_letter_iso_code', 'subject_to_vat', 'allow_billing',]
