import pdb
from django.conf.global_settings import LANGUAGES
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework import serializers,exceptions
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import Serializer, ModelSerializer
from apps.notifications.models import (NotificationTemplate,Notification)

class NotificationSerializer(serializers.ModelSerializer):
    """
    Notification serializer
    """
    class Meta:
        model = Notification
        fields = ('user','notification_template','seen_status',)



