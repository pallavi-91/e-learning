from django.urls import path, include
from .controller import CourseChangeHistoryView, CourseView, CourseStatisticView, CourseExtrasView, CourseDetailStatisticView
from .intended.urls import intended_urls
from .reviews.urls import urlpatterns as review_urls
from .qna.urls import urlpatterns as qna_urls

exras_urls = [
    path('topics', CourseExtrasView.as_view({
            'get': 'topic_list'
    })),
    path('category', CourseExtrasView.as_view({
            'get': 'category_list'
    })),
    path('subcategory', CourseExtrasView.as_view({
            'get': 'subcategory_list'
    })),
    path('languages', CourseExtrasView.as_view({
            'get': 'language_list'
    })),
]

feedback_urls = [
    path('<uuid:course__code>/history', CourseChangeHistoryView.as_view({
        'get': 'list',
        'post': 'create',
        'delete': 'purge_all',
    })),
    path('history/<int:pk>/restore', CourseChangeHistoryView.as_view({
        'get': 'restore',
    })),
    path('history/<int:pk>', CourseChangeHistoryView.as_view({
        'get': 'retrieve',
        'delete': 'destroy'
    })),
]

statistic_urls = [
    path('users-progress', CourseDetailStatisticView.as_view({
            'get': 'users_progress'
    })),
    path('certifications', CourseDetailStatisticView.as_view({
            'get': 'certifications'
    })),
    path('general-stats', CourseDetailStatisticView.as_view({
            'get': 'general_stats'
    })),
    path('sales-revenue', CourseDetailStatisticView.as_view({
            'get': 'sales_revenue'
    })),
]

urlpatterns = [
    path('', CourseView.as_view({
            'get': 'list'
    })),
    path('statistics', CourseView.as_view({
        'get': 'statistic_overview',
    })),
    path('recently-updated', CourseView.as_view({
        'get': 'recently_updated',
    })),
    path('<uuid:code>', CourseView.as_view({
        'get': 'retrieve',
        'put': 'update',
    })),
    path('<uuid:code>/pricing', CourseView.as_view({
        'get': 'pricing_detail',
    })),
    path('<uuid:code>/sections', CourseView.as_view({
        'get': 'section_list',
    })),
    path('section/<int:pk>/update', CourseView.as_view({
        'post': 'section_update'
    })),
    path('<uuid:code>/sections/<int:section>', CourseView.as_view({
        'get': 'subsection_list',
    })),
    path('<uuid:code>/sections/<int:section>/sbs/<int:subsection>', CourseView.as_view({
        'delete': 'subsection_delete',
    })),
    path('<uuid:code>/intended/', include(intended_urls)),
]

urlpatterns += [
    path('course-statistic', CourseStatisticView.as_view({
        'get': 'list',
    })),
    path('course-statistic/enrollments', CourseStatisticView.as_view({
        'get': 'enrollments',
    })),
    path('course-statistic/top-courses', CourseStatisticView.as_view({
        'get': 'top_courses',
    })),
    path('course-statistic/most-popular', CourseStatisticView.as_view({
        'get': 'most_popular',
    })),
    path('course-statistic/most-engaging', CourseStatisticView.as_view({
        'get': 'most_engaging',
    })),
    path('course-statistic/unfinished', CourseStatisticView.as_view({
        'get': 'unfinished',
    })),
    path('course-statistic/withdrawn', CourseStatisticView.as_view({
        'get': 'withdrawn',
    })),
]

urlpatterns += [
    path('extras/', include(exras_urls)),
    path('feedback/', include(feedback_urls)),
    path('<uuid:code>/statistics/', include(statistic_urls)),
    path('<uuid:code>/reviews/', include(review_urls)),
    path('<uuid:code>/qna/', include(qna_urls)),
]