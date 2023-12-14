from django.urls import path, include
from .controller import CourseLearnersView, CourseObjectivesView, CourseRequirementView

intended_urls = [
    path('learners', CourseLearnersView.as_view({
            'get': 'list',
            'post': 'create',
    })),
    path('<int:pk>/learners', CourseLearnersView.as_view({
            'delete': 'destroy',
            'get': 'retrieve'
    })),
    path('objectives', CourseObjectivesView.as_view({
            'get': 'list',
            'post': 'create',
    })),
    path('<int:pk>/objectives', CourseObjectivesView.as_view({
            'delete': 'destroy',
            'get': 'retrieve'
    })),
    path('requirements', CourseRequirementView.as_view({
            'get': 'list',
            'post': 'create',
    })),
    path('<int:pk>/requirements', CourseRequirementView.as_view({
            'delete': 'destroy',
            'get': 'retrieve'
    })),
]