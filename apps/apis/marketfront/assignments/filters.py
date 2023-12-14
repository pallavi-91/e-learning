from time import timezone
from django_filters import rest_framework as filters

from apps.utils.helpers import get_client_ip
from apps.courses.models import Category, Course, CourseView
from django.db.models import Q, Count
from django.utils import timezone
