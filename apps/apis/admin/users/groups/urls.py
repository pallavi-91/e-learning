from django.urls import path
from .controller import InstructorGroupView

instructor_group_urls = [
    path('', InstructorGroupView.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('stats-count', InstructorGroupView.as_view({
        'get': 'groups_count'
    })),
    path('<int:pk>', InstructorGroupView.as_view({
        'get': 'retrieve',
        'put': 'partial_update',
        'delete': 'destroy'
    })),
]
