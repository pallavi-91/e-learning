from django.urls import path
from rest_framework_simplejwt import views as jwt_views
from .controllers import (
    ForgotPasswordView,
    ImageUploadView,
    RefundRequestView,
    SignupView,
    ChangePasswordView,
    ProfileView,
    InstructorsView,
    CartView,
    TransactionView,
    UserView,
    ReportsView,
)

urlpatterns = [
    path('login/',jwt_views.TokenObtainPairView.as_view(),name ='user_token_obtain_pair'),
    path('token/refresh',jwt_views.TokenRefreshView.as_view(),name ='user_token_refresh'),
    path('signup/', SignupView.as_view()),
    path('subscribe/', UserView.as_view({
        'post': 'post'
    })),
    path('images/', ImageUploadView.as_view({ 'post': 'create'})),

    path('forgot-password/', ForgotPasswordView.as_view({
        'post': 'verify_email',
    })),
    path('reset-password/', ForgotPasswordView.as_view({
        'put': 'reset_password',
    })),
    path('auth/', ProfileView.as_view({
        'get': 'get',
        'post': 'update',
    })),
    path('cart/', CartView.as_view({
        'get': 'get',
        'post': 'add',
    })),
    path('cart/<int:id>/', CartView.as_view({
        'delete': 'delete',
    })),
    
    path('refund/<str:transaction_id>/', RefundRequestView.as_view({
        'post': 'create',
    })),
]

urlpatterns += [
    path('passwords/request/', ChangePasswordView.as_view({
        'post': 'request_reset',
    })),
    path('passwords/validate/', ChangePasswordView.as_view({
        'post': 'token_valid',
    })),
    path('passwords/reset/', ChangePasswordView.as_view({
        'post': 'reset_password',
    }))
]

urlpatterns += [
    path('instructors/<int:user__id>/', UserView.as_view({
        'get': 'get'
    })),
    path('my-instructors', InstructorsView.as_view({
        'get': 'list'
    })),
    path('become-instructor/', InstructorsView.as_view({
        'post': 'become_instructor'
    })),
    path('instructors/reports/', ReportsView.as_view({
        'get': 'reports'
    })),
    path('instructors/reports/summary/', ReportsView.as_view({
        'get': 'summary',
    })),
    path('instructors/reports/enrollments/', ReportsView.as_view({
        'get': 'enrollments',
    })),
    path('instructors/reports/<str:month>/month/', TransactionView.as_view({
        'get': 'reports_by_month'
    })),
    path('instructors/reports/<str:month>/month/totals/', TransactionView.as_view({
        'get': 'totals_by_month'
    })),
    path('transactions/', TransactionView.as_view({
        'get': 'list'
    })),
]