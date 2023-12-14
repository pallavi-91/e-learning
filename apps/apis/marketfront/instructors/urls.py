from django.urls import path, include
from apps.apis.marketfront.instructors.courses.urls import urlpatterns as instructor_courses_urls

from .controllers import (
    InstructorView,
    TransactionView,
    UserView,
    ReportsView,
)

urlpatterns = [
    path('', InstructorView.as_view({
        'post': 'create'
    })),
    path('<int:user__id>/', UserView.as_view({
        'get': 'get'
    })),
    path('reports/', ReportsView.as_view({
        'get': 'reports'
    })),
    path('reports/summary/', ReportsView.as_view({
        'get': 'summary',
    })),
    path('reports/enrollments/', ReportsView.as_view({
        'get': 'enrollments',
    })),
    path('reports/<str:month>/month/', TransactionView.as_view({
        'get': 'reports_by_month'
    })),
    path('reports/<str:month>/month/totals/', TransactionView.as_view({
        'get': 'totals_by_month'
    })),
    path('transactions/', TransactionView.as_view({
        'get': 'list'
    })),
    path('courses/', include(instructor_courses_urls)),
    
]