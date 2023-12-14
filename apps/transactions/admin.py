from django.contrib import admin

from apps.status import TransactionTypes
from .models import Transactions, PaymentType, InstructorPayouts, TransactionPayout
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered

@admin.register(PaymentType)
class AdminPaymentType(admin.ModelAdmin):
    list_display = (
        'id',
        'payment_gateway',
        'payment_method',
    )

@admin.register(Transactions)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student',
        'instructor',
        'type',
        'get_status',
        'user_class',
        'refund_status',
        'payout_status',
        'gross_amount',
        'get_platform_fee',
        'net_amount',
        'date_created',
    )

    def get_status(self, instance):
        if instance.type == TransactionTypes.PAYOUT:
            return instance.get_payout_status_display().title()
        return instance.get_status_display()
    get_status.short_description = "Status"

    def get_platform_fee(self, instance):
        return instance.platform_fee
    get_platform_fee.short_description = "Platform fee"
    
    
@admin.register(InstructorPayouts)
class AdminInstructorPayouts(admin.ModelAdmin):
    list_display = ['id', 'status', 'payout_type', 'user', 'date_updated']
    list_filter = ['payout_type', 'status']

@admin.register(TransactionPayout)
class AdminTransactionPayout(admin.ModelAdmin):
    list_display = ['id', 'payout', 'transaction', 'date_created']
    
models = apps.get_models(include_auto_created=False)
for model in models:
    try:
        if model._meta.app_label in ['transactions', 'statements', 'shares', 'courses', 'coupons', 'countries', 'notifications', 'pricing']:
            admin.site.register(model)
    except AlreadyRegistered:
        pass
    except Exception as ex:
        pass
