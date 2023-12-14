from rest_framework import serializers
from apps.shares.models import SharePrices
from django.utils.translation import gettext as _


class SharePriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharePrices
        fields = '__all__'
