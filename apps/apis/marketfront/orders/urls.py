from django.urls import path
from .controllers import OrderView, PurchaseHistory

urlpatterns = [
    path('purchase/history/', PurchaseHistory.as_view({
        'get': 'list'
    })),
    path('<str:slug>/free-enroll/', OrderView.as_view({
        'post': 'enroll_for_free',
    })),
    
    path('cart/checkout/', OrderView.as_view({
        'post': 'checkout',
    })),
    path('cart/payment/', OrderView.as_view({
        'post': 'payment',
    })),
    path('cart/payment/success/', OrderView.as_view({
        'get': 'payment_capture',
    })),
    # get order details
    path('<uuid:code>/', OrderView.as_view({
        'get': 'get_order_details',
    })),
]