from django.utils.functional import cached_property
from django.db import models
from apps.transactions.utility import get_transaction_code
from apps.users.models import Order
from apps.courses.models import UserClass
from apps.currency.models import Currency
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils.timezone import localtime
from types import SimpleNamespace
from apps.status.mixins import AutoCreatedUpdatedMixin
from apps.status import *

PERCENTAGE_VALIDATOR = [MinValueValidator(0), MaxValueValidator(100)]


# Create your models here.
class PaymentType(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'payment_options'
        
    payment_gateway = models.CharField(max_length=100, default=SupportedGateway.PAYPAL, choices=SupportedGateway.choices)
    payment_method = models.CharField(max_length=100, choices=PaymentMethods.choices, default=PaymentMethods.CARD)
    
    def __str__(self) -> str:
        return f"{self.payment_gateway} - {self.payment_method}"


class OrderQuerySet(models.QuerySet):
    def sales_transactions(self, *args, **kwargs):
        return self.exclude(type=TransactionTypes.PAYOUT).filter(**kwargs)
    

class Transactions(AutoCreatedUpdatedMixin):
    """ transaction made from an order. this is
        created after the payment is made.
    """
    class Meta:
        db_table = 'transactions'
        ordering = ['-date_updated']
        
    transaction_id = models.CharField(max_length=50, default=get_transaction_code, editable=True)
    # request refund status
    refund = models.BooleanField(default=False)
    refund_status = models.CharField(max_length=30, choices=RefundStatus.choices, null=True, blank=True)
    date_refunded = models.DateTimeField(null=True, blank=True)
    student = models.ForeignKey(get_user_model(), related_name="student_transactions", on_delete=models.CASCADE)
    instructor = models.ForeignKey(get_user_model(), related_name="instructor_transactions", on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, related_name="order_transactions")
    type = models.CharField("Transaction Type", max_length=50, choices=TransactionTypes.choices, default=TransactionTypes.SALE)
    status = models.CharField("Transaction Status", max_length=20, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    payment_type = models.ForeignKey(PaymentType, on_delete=models.SET_NULL, null=True)
    gateway_charge = models.FloatField(default=0.00)
    objects = OrderQuerySet.as_manager()
    # orders
    gross_amount = models.FloatField(default=0.00)
    # gross amount the total amount of sales without any deductions
    vat_amount = models.FloatField(default=0.00)
    currency = models.ForeignKey(Currency, null=True, related_name="transactions", on_delete=models.SET_NULL)
    channel = models.JSONField(default=dict)
    
    payment_transaction_id = models.CharField(max_length=100, null=True, blank=True)
    gateway_raw = models.JSONField(default=dict)
    user_class = models.ForeignKey(UserClass, on_delete=models.SET_NULL, null=True,related_name='transactions')# User selected course, created in separate model class
    payout_status = models.CharField(max_length=20, choices=PayoutStatus.choices, default=PayoutStatus.PENDING)
    payout_error = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"<Transactions> {self.id}"

    @cached_property
    def channel_obj(self):
        if self.channel:
            return SimpleNamespace(**self.channel)
        return None
    
    @cached_property
    def affiliate_fee(self):
        if not self.refund and self.type == TransactionTypes.SALE:
            _fee = round((self.channel_obj.affiliate_share/100),2)
            return round(self.net_amount * _fee, 2)
        
        return 0
    
    @cached_property
    def instructor_fee(self):
        if not self.refund:
            if self.type == TransactionTypes.PAYOUT:
                return round(self.net_amount, 2)
            _fee = round((self.channel_obj.instructor_share/100),2)
            return round(self.net_amount * _fee, 2)
        return 0
    
    @cached_property
    def platform_fee(self):
        if not self.refund and self.type == TransactionTypes.SALE:
            _fee = round((self.channel_obj.platform_share/100),2)
            return round(self.net_amount * _fee, 2)
        return 0
    
    @cached_property
    def thkee_credit_fee(self):
        if not self.refund and self.type == TransactionTypes.SALE:
            _fee = round((self.channel_obj.thkee_credit/100),2)
            return round(self.net_amount * _fee, 2)
        return 0
    
    @property
    def net_amount(self):
        """ total amount after the deduction (amount that reflected to the merchant account)
        """
        if self.type == TransactionTypes.PAYOUT:
            return round(float(self.gross_amount), 2)

        return self.gross_amount - (self.gateway_charge + self.vat_amount)

    @cached_property
    def can_refund(self):
        """ check if it is possible to request for
            as refund on this transaction.
        """
        if self.type == TransactionTypes.SALE:
            # if the user is already requested for refund that means he/she cannot request again
            if self.refund_status is not None: return False
            # check if the transaction date is less than 30 days
            # it means that it is possible for a refund. beyond
            # that it is no longer possible for a refund.
            dt_ = localtime() - self.date_updated
            if dt_.days <= settings.REFUND_PERIOD_THRESHOLD:
                # Check if course has completed less then x%
                progress_percent = self.user_class.actual_progress
                if progress_percent <= settings.REFUND_COURSE_THRESHOLD:
                    return True

        return False
    
    @property
    def is_eligible(self):
        """ check if it is possible to request for
            as refund on this transaction.
        """
        if self.type == TransactionTypes.SALE:
            # check if the transaction date is less than 30 days
            # it means that it is possible for a refund. beyond
            # that it is no longer possible for a refund.
            dt_ = localtime() - self.date_updated
            if dt_.days <= settings.REFUND_PERIOD_THRESHOLD:
                # Check if course has completed less then x%
                progress_percent = self.user_class.actual_progress
                if progress_percent <= settings.REFUND_COURSE_THRESHOLD:
                    return True

        return False
    
    @cached_property
    def refund_transactions(self):
        return self.order.order_transactions.filter(type=TransactionTypes.REFUND)


class TransactionCoupons(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'transaction_coupons'
        verbose_name = 'Transaction Discount'
        
    transaction = models.ForeignKey(Transactions,related_name="transaction_coupons", on_delete=models.CASCADE)
    discount = models.FloatField(default=0.0, validators=PERCENTAGE_VALIDATOR)# TOD: Need to copy from DiscountCoupons discount % field
    discount_value = models.FloatField(default=0.0, validators=PERCENTAGE_VALIDATOR)# TOD: Need to copy from DiscountCoupons discount % discount_value
    coupon_code = models.CharField(max_length=10, blank=True, null=True)
    
    def __str__(self) -> str:
        return f"<TransactionCoupons> {self.id}"

