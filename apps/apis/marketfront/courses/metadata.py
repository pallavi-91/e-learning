from rest_framework.viewsets import GenericViewSet, ModelViewSet
from apps.courses.models import Course
from apps.users.models import Instructor, User
from apps.countries.models import Country
from apps.utils.paginations import ViewSetPagination
from apps.utils.query import SerializerProperty
from rest_framework.response import Response
from django.conf.global_settings import LANGUAGES
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.conf import settings
import os, json

class CourseExtrasView(SerializerProperty, ViewSetPagination, GenericViewSet):
    public_actions = ['language_list', 
                      'language_courses', 
                      'assets_count',
                      'filter_metadata']

    def language_list(self, request, *args, **kwargs):
        data = [dict(zip(('id', 'name'), i)) for i in LANGUAGES]
        return Response(data)
    
    @method_decorator(cache_page(60*2, key_prefix='language_courses'))
    def language_courses(self, request, *args, **kwargs):
        data = [dict(zip(('id', 'name'), i)) for i in LANGUAGES]
        for item in data:
            total_course = Course.objects.filter(language=item.get('id')).count()
            item.update({'total_course': total_course})
        return Response(data)
    
    @method_decorator(cache_page(60*2, key_prefix='assets_count_courses'))
    def assets_count(self, request):
        """
            Get count of company major assets.
            Students, Instructors, Country etc.
        """
        context = dict()
        instructors = Instructor.objects.all()
        context['total_students'] = User.objects.exclude(id__in=instructors.values_list('user', flat=True)).count()
        context['total_instructors'] = instructors.count()
        context['total_country'] = Country.objects.count()

        return Response(context)
    
    def filter_metadata(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'core', 'course-filter-meta.json')
        with open(file_path) as file:
            data = json.loads(file.read())
        return Response(data)