from django.urls import path, include
from .controllers import CourseChangeHistoryView, InstructorCourseView
from .sections.urls import urlpatterns as sections_urls
from .intended.urls import intended_urls

feedback_urls = [
    path('history', CourseChangeHistoryView.as_view({
        'get': 'list',
    })),
    path('<int:pk>/history', CourseChangeHistoryView.as_view({
        'get': 'retrieve',
        'put': 'partial_update'
    })),
]

urlpatterns = [
    path('', InstructorCourseView.as_view({
        'get': 'list'
    })),
    path('create', InstructorCourseView.as_view({
        'post': 'create'
    })),
    path('<uuid:code>', InstructorCourseView.as_view({
        'delete': 'destroy',
        'put': 'update',
        'get':'retrieve'
    })),
    path('<uuid:code>/submit-for-review', InstructorCourseView.as_view({
        'get': 'submit_for_review',
    })),
    path('currency-list', InstructorCourseView.as_view({
        'get': 'currency_list'
    })),
    path('pricing-tier-list', InstructorCourseView.as_view({
        'get': 'pricing_tier_list'
    })),
    path('<int:course_id>/sections/', include(sections_urls)),
    path('<int:course_id>/feedbacks/', include(feedback_urls)),
    path('<int:course_id>/intended/', include(intended_urls))
]