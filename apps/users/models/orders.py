from functools import cached_property
from types import SimpleNamespace
import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, transaction
from rest_framework import exceptions
from apps.currency.models import Currency
from apps.status import OrderStatus, RefundStatus, TransactionTypes
from apps.utils.paypal.checkout import PaypalOrder
from apps.utils.http import urlsafe
from apps.utils.transactions import TransactionManager
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .classes import UserClass
from apps.status.mixins import AutoCreatedUpdatedMixin


class OrderQuerySet(models.QuerySet):
    def transactions_of_order(self, *args, **kwargs):
        return self.order_transactions.exclude(type=TransactionTypes.PAYOUT).filter(**kwargs)

class OrderToken(AutoCreatedUpdatedMixin):
    """ generated token when the anonymous user checkout the courses
    """
    class Meta:
        db_table = 'order_tokens'
        
    token = models.UUIDField(default=uuid.uuid4)
    order = models.ForeignKey('Order',related_name='tokens',on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(null=True,blank=True)
    is_used = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.email}"

    @transaction.atomic
    def link_order(self, user):
        self.order.user = user
        self.order.save()
        self.is_used = True
        self.order.classes.all().update(user=user)
        self.order.transactions.all().update(student=user)
        self.save()
        return self
    
    def send_email(self):
        """ send email to the anonymous user the magic link after he/she successfully pay the courses
        """
        
        html_content = render_to_string(
            'users/emails/checkout-register.html',
            {'obj': self},
        )
        text_content = render_to_string(
            'users/emails/checkout-register.txt',
            {'obj': self},
        )
        msg = EmailMultiAlternatives(
            "Checkout details",
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return
    
class Order(TransactionManager, AutoCreatedUpdatedMixin):
    """ user purchase order
        :: a request made by the user to acquire a single or
            group of courses.
    """
    class Meta:
        db_table = 'orders'
    # user is optional for users that have purchased
    # the course but haven't created an account yet.
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(get_user_model(), related_name="orders", null=True, blank=True, on_delete=models.SET_NULL)
    email = models.EmailField(null=True, blank=True)
    full_name = models.CharField(max_length=120,blank=True,null=True)
    status = models.CharField(max_length=50, choices=OrderStatus.choices, default=OrderStatus.CREATED)
    paypal_orderid = models.CharField(max_length=30, null=True, blank=True)
    paypal_payment_raw = models.JSONField(null=True, blank=True)
    channel = models.JSONField(default=dict)
    refund = models.BooleanField(default=False)
    refund_status = models.CharField(max_length=30, choices=RefundStatus.choices, null=True, blank=True)
    date_refunded = models.DateTimeField(null=True, blank=True)

    objects = OrderQuerySet.as_manager()
    
    def __str__(self) -> str:
        return str(self.id)
    
    @cached_property
    def channel_obj(self):
        if self.channel:
            return SimpleNamespace(**self.channel)
        return None
    
    @cached_property
    def payment_type(self):
        trans = self.order_transactions.filter(type=TransactionTypes.SALE).first()
        if trans:
            return trans.payment_type 
        return ""
        
    @cached_property
    def channel_type(self):
        return self.channel_obj.share_types
    
    @cached_property
    def can_refund(self):
        trans = self.order_transactions.filter(type=TransactionTypes.SALE).first()
        return trans.can_refund if trans else False

    @cached_property
    def total_amount(self):
        """ total amount
        """
        return sum(self.classes.values_list('price', flat=True))

    def add_courses(self, courses):
        """ add courses to this purchase order
        """
        classes = []
        for course in courses:
            # create a relationship of the course
            # to specific user
            classes.append(UserClass(
                order=self,
                course=course,
                user=self.user,
                price=course.sale_price,
                currency=course.currency,
            ))

        UserClass.objects.bulk_create(classes)
        return

    def courses(self):
        """ return the `Course` list
        """
        from apps.courses.models import Course
        return Course.objects.filter(id__in=self.classes.values_list('course', flat=True))

    @transaction.atomic
    def paypal_createorder(self):
        """ An order represents a payment between two or more parties.
            Use the Orders API to create, update, retrieve,
            authorize, and capture orders.
            https://developer.paypal.com/docs/api/orders/v2/#orders_create
        """
        # instantiate the `PaypalOrder` class to create
        # a purchase order into the paypal server.
        order = PaypalOrder(order=self, classes=self.classes.all()).create()
        self.paypal_orderid = order.get('id')
        self.status = order.get('status')
        self.save()

        return urlsafe(settings.PAYPAL_URL, 'checkoutnow', token= self.paypal_orderid)

    @transaction.atomic
    def paypal_sendpayment(self):
        """ Captures payment for an order. To successfully capture payment
            for an order, the buyer must first approve the order or a
            valid payment_source must be provided in the request.
            https://developer.paypal.com/docs/api/orders/v2/#orders_capture
        """
        resp = PaypalOrder(order=self).pay()
        if resp.get('status') == OrderStatus.COMPLETED.upper():
            # check if the order doesn't have an owner/user
            # create a user based on the email provided from
            # paypal.
            # Note: there are cases that the user purchased and
            # has not logged in, but he has an account. this will
            # cause issue as we might create a new account based on
            # which paypal account info he uses.
            # update the courses status to be added
            # to the user's dashboard
            self.classes.all().update(user=self.user, is_purchased=True)

            # update details
            self.status = OrderStatus.COMPLETED
            self.paypal_payment_raw = resp
            self.save()

            # Send email to the user
            self.send() 

            # create transactions for customer and instructors
            def __pamount(obj, k):
                return obj['seller_receivable_breakdown'][k]['value']

            for purchase in resp['purchase_units']:
                # create an sale type transaction
                _item = purchase['payments']['captures'][0]
                _bd = _item['seller_receivable_breakdown']
                currency = Currency.objects.get(currency_code=_item['amount']['currency_code'])
                user_class = UserClass.objects.get(id=_item['custom_id'])
                instructor = user_class.course.user
                # Get Payment method
                self.create_paypal_sale(_item['id'], 
                                 _item['custom_id'], 
                                 self.user, 
                                 instructor, 
                                 self,
                                 __pamount(_item, 'gross_amount'), 
                                 __pamount(_item, 'paypal_fee'), 
                                 currency, 
                                 self.channel)


            if not self.user:
                payer = resp.get('payer')
                email = payer.get('email_address')
                order_token = OrderToken.objects.create(order=self, email=email)
                order_token.send_email() # change self.email to  for paypal email 

            return self
        
        raise exceptions.ValidationError(resp.get('message'))


    def send(self):
        """ send email to the user that he/she bought the courses
        """
        if not self.user: return 
        
        html_content = render_to_string(
            'users/emails/checkout.html',
            {'obj': self},
        )
        text_content = render_to_string(
            'users/emails/checkout.txt',
            {'obj': self},
        )
        msg = EmailMultiAlternatives(
            "Checkout details",
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [self.user.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return