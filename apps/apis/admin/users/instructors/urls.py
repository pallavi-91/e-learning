from django.urls import path, include
from .controller import InstructorView

instructor_list = [
    path('', InstructorView.as_view({
        'get': 'list'
    })),
    path('instructors-count', InstructorView.as_view({
        'get': 'instructors_count'
    })),
    path('<int:pk>/detail', InstructorView.as_view({
        'get': 'profile',
    })),
    path('<int:pk>/delete', InstructorView.as_view({
            'delete': 'destroy',
        })),
    path('<int:pk>/update/', include([
        path('', InstructorView.as_view({
            'put': 'update_profile',
        })),
        path('basic', InstructorView.as_view({
            'put': 'update_instructor',
        })),
        
        path('change-password', InstructorView.as_view({
            'put': 'change_password',
        })),
        path('notification', InstructorView.as_view({
            'put': 'update_notifications',
        }))
    ])),
]
