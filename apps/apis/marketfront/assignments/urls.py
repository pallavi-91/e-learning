from django.urls import include, path

from .controllers import (
    StudentAssignmentView,
    AssignmentView,
    StudentQuizView,
    QuizView,
)

students_urls = [
    path('quiz/',include([
        path('<int:id>/answer/',StudentQuizView.as_view({
            'post': 'answer',
            'delete': 'delete_answer',
        })),
    ])),
    path('assignment/',include([
        path('<int:id>/', AssignmentView.as_view({
            'get': 'get',
        })),
        path('<int:id>/answer/',StudentAssignmentView.as_view({
            'post': 'answer',
            'put': 'update_answer',
            'get': 'get'
        })),
    ])),
    path('<int:assignment_id>/',include([
        path('submissions/', StudentAssignmentView.as_view({
            'get': 'list'
        })),
    ])),
]

instructor_urls = [
    path('quiz/',include([
        path('<int:id>/',QuizView.as_view({
            'post': 'create_quiz',
            'put': 'update_quiz'
        })),
        path('<int:id>/question/',QuizView.as_view({
            'post': 'create_question',
            'put': 'update_question',
        })),
    ])),    
    path('assignment/',include([
        path('details/<int:id>/', AssignmentView.as_view({
            'get': 'get',
        })),
        path('<int:quiz_id>/',QuizView.as_view({
            'post': 'create_assignment',
            'put': 'update_assignment',
        })),
    ])),
    path('assignments/',include([
        path('<str:code>/', AssignmentView.as_view({
            'get': 'get_assignments'
        })),
    ])),
]

urlpatterns = [
    path('student/', include(students_urls)),
    path('instructor/', include(instructor_urls)),
]