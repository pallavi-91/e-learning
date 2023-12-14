from django.urls import path
from .controller import CourseQnaView

urlpatterns = [
    path('', CourseQnaView.as_view({
        'get': 'list'
    }))
]