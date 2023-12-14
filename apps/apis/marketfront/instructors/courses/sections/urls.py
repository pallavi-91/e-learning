from django.urls import path, include
from .controllers import InstructorSectionView, LectureResourcesView, LectureView, AssignmentView, QuizView, AssignmentQuestionsView, QuizQuestionsView

urlpatterns = [
    path('', InstructorSectionView.as_view({
        'get': 'list',
    })),
    path('create', InstructorSectionView.as_view({
        'post': 'create'
    })),
    path('<int:pk>', InstructorSectionView.as_view({
        'put': 'update',
        'get': 'retrieve',
        'delete': 'destroy'
    })),
    path('<int:pk>/subsections', InstructorSectionView.as_view({
        'get': 'list_subsections'
    })),
    path('<int:section>/lectures', LectureView.as_view({
        'post': 'create',
        'get': 'list',
    })),
    path('<int:section>/lectures/<int:pk>', LectureView.as_view({
        'put': 'update',
        'get': 'retrieve',
        'delete': 'destroy',
    })),
    path('lecture/<int:lecture>/resources', LectureResourcesView.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('lecture/<int:lecture>/resource/<int:pk>', LectureResourcesView.as_view({
        'delete': 'destroy',
        'get': 'retrieve',
        'put': 'update',
    })),
    path('<int:section>/assignments/create', AssignmentView.as_view({
        'post': 'create',
    })),
    path('<int:section>/assignments/<int:pk>', AssignmentView.as_view({
        'put': 'update',
        'get': 'retrieve',
        'delete': 'destroy',
    })),
    path('assignment/<int:assignment>/questions', AssignmentQuestionsView.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('assignment/<int:assignment>/questions/<int:pk>', AssignmentQuestionsView.as_view({
        'delete': 'destroy',
        'get': 'retrieve',
        'put': 'update',
    })),
    path('<int:section>/quiz/create', QuizView.as_view({
        'post': 'create',
    })),
    path('<int:section>/quiz/<int:pk>', QuizView.as_view({
        'put': 'update',
        'get': 'retrieve',
        'delete': 'destroy',
    })),
    path('<int:section>/quiz/<int:quiz>/create-question', QuizView.as_view({
        'post': 'create_question',
    })),
    path('<int:section>/quiz/<int:quiz>/update-question/<int:question>', QuizView.as_view({
        'put': 'update_question',
    })),
    path('quiz/<int:quiz>/questions', QuizQuestionsView.as_view({
        'get': 'list',
    })),
    path('quiz/<int:quiz>/question/<int:pk>', QuizQuestionsView.as_view({
        'delete': 'destroy',
        'get': 'retrieve',
    })),
]
