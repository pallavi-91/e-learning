from django.urls import path, include
from .controller import StudentView

student_list = [
    path('', StudentView.as_view({
        'get': 'list'
    })),
    path('students-count', StudentView.as_view({
        'get': 'students_count'
    })),
    path('<int:pk>/detail', StudentView.as_view({
        'get': 'profile',
    })),
    path('<int:pk>/update', StudentView.as_view({
        'put': 'update_profile',
    }))
]
