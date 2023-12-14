from django.urls import include, path

from .controllers import ClassesView, CourseCertificationView, SubsectionProgressView

urlpatterns = [
    path('classes/',include([
        path('progress/', SubsectionProgressView.as_view({
            'post': 'update_or_create'
        })),
        path('',ClassesView.as_view({
            'get': 'list',
        })),
        path('<str:code>/toggle-archive',ClassesView.as_view({
            'get': 'toggle_archive',
        })),
        path('<str:code>/sections/',ClassesView.as_view({
            'get': 'get_sections'
        })),
        path('<str:code>/',ClassesView.as_view({
            'get': 'get_class_by_code'
        })),
        path('<str:code>/complete/',ClassesView.as_view({
            'post': 'toggle_complete'
        })),

        path('certification/<uuid:code>/',include([
            path('course-progress', CourseCertificationView.as_view({
                'get': 'course_progress'
            })),
            path('course-overview', CourseCertificationView.as_view({
                'get': 'course_overview'
            })),
        ])),
    ])),
]
