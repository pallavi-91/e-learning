from django.urls import path
from .controller import CourseReviewView

urlpatterns = [
    path('', CourseReviewView.as_view({
        'get': 'list'
    }))
]