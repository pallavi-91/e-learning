from django.urls import path, include
from .controllers import AssignmentView

urlpatterns = [
    path('', AssignmentView.as_view({
        'get': 'list'
    })),
    path('create', AssignmentView.as_view({
        'post': 'create'
    })),
    path('<int:course_id>', AssignmentView.as_view({
        'delete': 'destroy',
        'put': 'update',
        'get':'retrieve'
    }))
]