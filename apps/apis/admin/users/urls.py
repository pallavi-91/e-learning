from django.urls import path, include
from .instructors.urls import instructor_list
from .students.urls import student_list
from .groups.urls import instructor_group_urls

urlpatterns = [
    path('instructors/', include(instructor_list)),
    path('students/', include(student_list)),
    path('groups/', include(instructor_group_urls))
]
