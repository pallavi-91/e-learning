from django.urls import include, path
from .transactions.controller import TransactionView
from .refunds.controller import RefundRequestView
from .instructors.controller import InstructorView
from .statements.controller import StatementView
from .orders.controller import OrdersView
from .payouts.urls import payouts_urls

transactions_urls = [
    path('', TransactionView.as_view({
        'get': 'list',
    })),
    path('<int:pk>', TransactionView.as_view({
        'put': 'update',
        'get': 'retrieve',
    })),
    path('<int:pk>/invoice-detail', TransactionView.as_view({
        'get': 'invoice_detail',
    })),
    path('earnings', TransactionView.as_view({
        'get': 'total_earnings',
    })),
    path('ecommerce-summery', TransactionView.as_view({
        'get': 'ecommerce_summery'
    })),
    path('<int:pk>/receipt', TransactionView.as_view({
        'get': 'transaction_receipt',
    })),
    
]

instructor_urls = [
    path('', InstructorView.as_view({
        'get': 'list',
    })),
    path('<int:pk>', InstructorView.as_view({
        'put': 'update',
        'get': 'retrieve',
    })),
    path('top-n/<int:n>', InstructorView.as_view({
        'get': 'top_n'
    })),
    path('count-by-date', InstructorView.as_view({
        'get': 'count_by_date'
    })),
    path('<int:pk>/statements', InstructorView.as_view({
        'get': 'instructor_statements',
    })),
    path('<int:pk>/statements/<int:st_pk>/transactions', InstructorView.as_view({
        'get': 'instructor_statement_transactions',
    })),
    
]

statement_urls = [
    path('', StatementView.as_view({
        'get': 'list',
    })),
    path('chart-data-summery', StatementView.as_view({
        'get': 'chart_data_summery',
    })),
    
    path('total-orders', StatementView.as_view({
        'get': 'get_total_orders',
    })),
    path('<int:pk>', StatementView.as_view({
        'put': 'update',
        'get': 'retrieve',
    })),
    path('<int:pk>/transactions', StatementView.as_view({
        'get': 'transactions',
    })),
    path('<int:pk>/detail', StatementView.as_view({
        'get': 'details',
    })),
    path('<int:pk>/invoice-detail', StatementView.as_view({
        'get': 'invoice_detail',
    })),
]

refund_requests_urls = [
    path('', RefundRequestView.as_view({
        'get': 'list',
    })),
    path('<int:pk>', RefundRequestView.as_view({
        'put': 'update',
        'get': 'retrieve',
    })),
    path('case-volume-by-status', RefundRequestView.as_view({
        'get': 'case_volume_by_status',
    })),
    path('<int:pk>/accept', RefundRequestView.as_view({
        'get': 'approve_refund',
    })),
    path('<int:pk>/reject', RefundRequestView.as_view({
        'get': 'reject_refund',
    })),
    path('thkee-issue-refund', RefundRequestView.as_view({
        'post': 'thkee_issue_refund'
    })),
    path('transaction/<int:pk>/cancel', RefundRequestView.as_view({
        'get': 'thkee_issue_refund_cancel',
    })),
    
]

order_urls = [
    path('', OrdersView.as_view({
        'get': 'list',
    })),
    path('<int:pk>', OrdersView.as_view({
        'get': 'retrieve',
    })),
    path('count-by-date-orders', OrdersView.as_view({
        'get': 'count_by_date_orders'
    })),
    path('<int:pk>/transactions', OrdersView.as_view({
        'get': 'transactions',
    })),

]



urlpatterns = [
    path('transactions/', include(transactions_urls)),
    path('instructors/', include(instructor_urls)),
    path('statements/', include(statement_urls)),
    path('refund-requests/', include(refund_requests_urls)),
    path('orders/', include(order_urls)),
    path('payouts/', include(payouts_urls))
]
