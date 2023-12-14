from django.urls import include, path

from .controllers import (
    SectionsView,
    PublicSections,
    LecturesView,
    LectureResources,
    SubSectionView,
)

urlpatterns = [
    path('lectures/', LecturesView.as_view({
        'post': 'create',
        'get': 'list',
    })),
    path('lectures/<str:pk>/', LecturesView.as_view({
        'post': 'update',
        'get': 'retrieve'
    })),
    path('lectures/<str:id>/delete/', LecturesView.as_view({
        'delete': 'delete',
    })),
    path('lectures/<str:id>/resources/', LectureResources.as_view({
        'post': 'create',
        'get': 'list',
    })),
    path('lectures/<str:id>/short/', LecturesView.as_view({
        'get': 'short_list',
    })),
    path('lectures/<str:lecture__id>/resources/<str:id>/delete/', LectureResources.as_view({
        'delete': 'delete',
    })),
]

urlpatterns += [
    path('courses/<str:course__code>/sections/', SectionsView.as_view({
        'post': 'create',
        'get': 'list',
    })),
    path('courses/<str:course__code>/sections/list/', SectionsView.as_view({
        'get': 'class_section',
    })),
    path('courses/<str:course__code>/sections/public/', PublicSections.as_view({
        'get': 'course_sections',
    })),
    path('courses/<str:course__code>/sections/<str:id>/', SectionsView.as_view({
        'post': 'update',
        'get': 'get',
        'delete': 'delete',
    })),
    path('subsection/<int:id>/',include([
        path('position/',SubSectionView.as_view({
            'put': 'update_subsection_position',
        })),
        path('list/', SubSectionView.as_view({
            'get': 'get_subsection_list',
        })),
        path('class/', SubSectionView.as_view({
            'get': 'get_subsection_class',
        })),
        path('lecture/', SubSectionView.as_view({
            'post': 'create_lecture',
            'put': 'update_lecture',
        })),
        path('',SubSectionView.as_view({
            'delete': 'delete'
        }))
    ])) 
]
