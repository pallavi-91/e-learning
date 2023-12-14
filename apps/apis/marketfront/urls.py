from django.urls import path, include
from apps.apis.marketfront.users.urls import urlpatterns as users_urls
from apps.apis.marketfront.instructors.urls import urlpatterns as instructor_urls
from apps.apis.marketfront.courses.urls import urlpatterns as courses_urls
from apps.apis.marketfront.assignments.urls import urlpatterns as assignment_urls
from apps.apis.marketfront.classes.urls import urlpatterns as classes_urls
from apps.apis.marketfront.sections.urls import urlpatterns as section_urls
from apps.apis.marketfront.orders.urls import urlpatterns as orders_urls
from apps.apis.marketfront.notifications.urls import urlpatterns as notification_urls
from apps.apis.marketfront.country.urls import urlpatterns as country_urls

urlpatterns = [
    path('users/', include(users_urls)),
    path('instructors/', include(instructor_urls)),
    path('courses/', include(courses_urls)),
    path('', include(assignment_urls)),
    path('', include(classes_urls)),
    path('', include(section_urls)),
    path('orders/', include(orders_urls)),
    path('',include(notification_urls)),
    path('', include(country_urls)),
    
]