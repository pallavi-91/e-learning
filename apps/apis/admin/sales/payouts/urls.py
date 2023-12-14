from django.urls import path, include
from .controller import PaidPayoutView, PayoutView

payouts_urls = [
    path('', PayoutView.as_view({
        'get': 'list',
    })),
    path('dashboard-summery',PayoutView.as_view({
        'get':'dashboard_data_summery'
    })),
    path('ongoing-summery',PayoutView.as_view({
        'get':'ongoing_payout_summery'
    })),
    path('upcoming-summery',PayoutView.as_view({
        'get':'upcoming_dashboard_payout_summery'
    })),
    path('upcoming/detail-summery',PayoutView.as_view({
        'get':'upcoming_payout_summery'
    })),
    path('failed/summery',PayoutView.as_view({
        'get':'failed_payouts_summery'
    })),
    path('failed/periods',PaidPayoutView.as_view({
        'get':'failed_payout_periods'
    })),
    path('failed/<int:id>/retry-payout',PaidPayoutView.as_view({
        'get':'retry_failed_payout'
    })),
    path('failed/retry-all-payout/<str:period>',PaidPayoutView.as_view({
        'get':'retry_all_failed_payout'
    })),
    path('<int:pk>', PayoutView.as_view({
        'put': 'update',
        'get': 'retrieve',
    })),
    
    path('<int:id>/payout-detail-summery',PayoutView.as_view({
        'get':'payout_detail_summery'
    })),
    path('<int:id>/transactions',PayoutView.as_view({
        'get':'payout_transactions'
    })),
    path('<int:id>/unhold/<int:tid>/transaction',PayoutView.as_view({
        'get':'unhold_transaction'
    })),
    path('<int:id>/hold/<int:tid>/transaction',PayoutView.as_view({
        'post':'hold_transaction'
    })),
    path('mark-ready',PayoutView.as_view({
        'post':'mark_ready'
    })),
    path('hold-transactions',PayoutView.as_view({
        'get':'payout_hold_transactions'
    })),
    path('<int:id>/mark-paid',PayoutView.as_view({
        'get':'mark_paid'
    })),
    path('inactive/activated',PayoutView.as_view({
        'post':'mark_activated'
    })),
    path('inactive/<int:id>/detail-summery',PaidPayoutView.as_view({
        'get':'inactive_payout_consolidated_history'
    })),
    # Paid pariods Urls
    path('paid-summery',PaidPayoutView.as_view({
        'get':'paid_payout_summery'
    })),
    path('periods/paid',PaidPayoutView.as_view({
        'get':'paid_payout_periods'
    })),
    path('instructor-paid-detail',PaidPayoutView.as_view({
        'get':'instructor_paid_detail'
    })),
    path('paid-period-history',PaidPayoutView.as_view({
        'get':'paid_payout_consolidated_history'
    })),
    path('period/<str:period>/summery',PaidPayoutView.as_view({
        'get':'paid_payout_detail_summery'
    })),
        
]
