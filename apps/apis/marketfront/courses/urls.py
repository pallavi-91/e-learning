from django.urls import include, path
from .metadata import CourseExtrasView
from .controllers import (
    CategoriesView,
    SubcategoriesView,
    CourseAnnouncementView,
    CoursePriceView,
    CourseRejectView,
    CourseReviewView,
    CourseSubmissionView,
    CoursesView,
    ForReviewCourseView,
    NoteView,
    TopicView,
    UploadVideo,
    CourseQnAView,
    CourseQnAReplyView,
)


urlpatterns = [
    path('upload/', UploadVideo.as_view({
        'post': 'upload'
    })),
    path('slug/<str:slug>/',include([
        path('category/', CoursesView.as_view({
            'get': 'courses_cat_slug',
        })),
        path('subcategory/', CoursesView.as_view({
            'get': 'courses_sub_slug',
        })),
        path('topic/', CoursesView.as_view({
            'get': 'courses_topic_slug',
        })),
    ])),
    
    path('favorites/', include([
        path('<uuid:code>/toggle/', CoursesView.as_view({
            'post': 'toggle_favorite'
        })),
        path('my/', CoursesView.as_view({
            'get': 'my_favorites'
        })),
    ])),
    
    path('', CoursesView.as_view({
        'post': 'create',
        'get': 'list',
    })),
    path('my/', CoursesView.as_view({
        'get': 'my_courses',
    })),
    path('filters/count/', CoursesView.as_view({
        'get': 'filters_count',
    })),
    
    path('user/<int:userid>/', CoursesView.as_view({
        'get': 'instructor_courses',
    })),
    path('<uuid:code>/get-instructor/', CoursesView.as_view({
        'get': 'instructor',
    })),
    path('<str:slug>/slug/', CoursesView.as_view({
        'get': 'get',
    })),
    
    path('<uuid:code>/request/edit/', CoursesView.as_view({
        'post': 'request_edit',
    })),
    # Courses API end
    
    
    path('video/<int:id>/info/', UploadVideo.as_view({
        'put': 'update_video_info'
    })),
    path('categories/', CategoriesView.as_view({
        'get': 'list',
    })),
    path('<int:category>/subcategories/', SubcategoriesView.as_view({
        'get': 'list',
    })),
    path('categories/top/', CategoriesView.as_view({
        'get': 'top_category'
    })),
    path('categories/used/', CategoriesView.as_view({
        'get': 'used_category'
    })),
    path('topics/',include([
        path('', TopicView.as_view({
            'get': 'list',
            'post': 'create',
        })),
        path('<int:pk>/', TopicView.as_view({
            'get': 'retrieve',
        })),
        path('most-searched', TopicView.as_view({
        'get': 'most_searched_topics'
        })),
    ])),
    path('<uuid:code>/', CoursesView.as_view({
        'get': 'get',
        'post': 'edit',
        'delete': 'delete'
    })),
]

urlpatterns += [
    path('announcement/',include([
        path('', CourseAnnouncementView.as_view({
            'get': 'list'
        })),
        path('<int:course_id>/create/', CourseAnnouncementView.as_view({
            'post': 'create'
        })),
        path('<int:course_id>/course/', CourseAnnouncementView.as_view({
            'get': 'course_announcements'
        })),
        path('<int:pk>/', CourseAnnouncementView.as_view({
            'get': 'retrieve',
            'put': 'update',
            'delete': 'destroy'
        })),
    ]))
]
urlpatterns += [
    path('note/<int:user_class_id>/',include([
        path('create/<int:subsection_id>/', NoteView.as_view({
            'post': 'create'
        })),
        path('list', NoteView.as_view({
            'get': 'list'
        })),
        path('<int:pk>/', NoteView.as_view({
            'put': 'partial_update',
            'delete': 'destroy'
        })),
    ]))
]

urlpatterns += [
    path('reject/',include([
        path('', CourseRejectView.as_view({
            'get': 'list'
        })),
        path('<int:course_id>/create/', CourseRejectView.as_view({
            'post': 'create'
        })),
        path('<int:course_id>/course/', CourseRejectView.as_view({
            'get': 'course_rejects'
        })),
        path('<int:pk>/', CourseRejectView.as_view({
            'put': 'update',
            'delete': 'destroy'
        })),
    ]))
]

urlpatterns += [
    path('prices/',include([
        path('', CoursePriceView.as_view({
            'get': 'list'
        }))
    ]))
]


urlpatterns += [
    
    # Review and rating 
    path('<uuid:code>/review/',include([
        path('', CourseReviewView.as_view({ 
            'post': 'create', 
            'get': 'list' ,
        })),
        path('student-feedbacks', CourseReviewView.as_view({ 
            'get': 'student_feedbacks' ,
            
        })),
        path('my/', CourseReviewView.as_view({ 
            'get': 'get_my_ratings' 
        })),
    ])),
    path('review/<int:id>/',include([
        path('like/',CourseReviewView.as_view({
            'get': 'like_review',
        })),
        path('dislike/',CourseReviewView.as_view({
            'get': 'dislike_review',
        })),
        path('report/',CourseReviewView.as_view({
            'post': 'report_review',
        })),
        path('list-report/', CourseReviewView.as_view({
            'get': 'review_reportes'  
        }))
    ])),
    
    path('submissions/',include([
        path('', CourseSubmissionView.as_view({
            'get': 'list'
        })),
        path('review/', CourseSubmissionView.as_view({
            'post': 'review_questions'
        })),
    ])),
    path('qna/',include([
        path('<int:user_class_id>', CourseQnAView.as_view({
            'get': 'list'
        })),
        path('<int:user_class_id>/ask-question', CourseQnAView.as_view({
            'post': 'create'
        })),
        path('<int:pk>/toggle-upvoting', CourseQnAView.as_view({
            'get': 'toggle_upvoting'
        })),
        # Comments
        path('<int:qna_id>/reply', CourseQnAReplyView.as_view({
            'post': 'create',
            'get': 'list'
        })),
        
        path('<int:qna_id>/reply/<int:pk>', CourseQnAReplyView.as_view({
            'put': 'partial_update',
            'delete':'destroy',
        })),
        path('<int:qna_id>/report-reply/<int:pk>', CourseQnAReplyView.as_view({
            'post': 'report_reply'
        })),
        path('<int:qna_id>/toggle-upvoting/<int:pk>', CourseQnAReplyView.as_view({
            'get': 'toggle_upvoting'
        })),
    ])),
    
    path('extras/', include([
        path('languages', CourseExtrasView.as_view({
            'get': 'language_list'
        })),
        path('language-courses', CourseExtrasView.as_view({
            'get': 'language_courses'
        })),
        path('resources', CourseExtrasView.as_view({
            'get': 'assets_count'
        })),
        path('filter-metadata', CourseExtrasView.as_view({
            'get': 'filter_metadata'
        })),
    ]))
    
]


urlpatterns += [
    path('admin/review/<str:code>/',include([
        path('', ForReviewCourseView.as_view({
            'get': 'get_course'
        })),
        path('approve/', ForReviewCourseView.as_view({
            'put': 'approve'
        })),
        path('reject/', ForReviewCourseView.as_view({
            'put': 'reject'
        })),
    ]))
]