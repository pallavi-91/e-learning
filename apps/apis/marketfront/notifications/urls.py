from django.urls import include, path
from .controllers import NotificationView
urlpatterns = [
    path('notifications/',include([        
        path('<int:user_id>',NotificationView.as_view({
            'get': 'queryset',
        }))
    ]))
]
