from functools import cached_property
import datetime
from django.conf import settings
from django.conf.global_settings import LANGUAGES
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from apps.shares.models import InstructorGroup
from apps.status import CourseStatus
from apps.status import InstructorGroups
from core.store.storage_backends import PrivateMediaStorage
from .managers import UserManager
from apps.status.mixins import AutoCreatedUpdatedMixin


def avatar_upload_location(instance, *args, **kwargs):
    return f"users/avatar/{instance.id}/{instance.photo.name}"

class User(AbstractBaseUser, PermissionsMixin):
    """ user account
    """
    class Meta:
        db_table = 'users'
        
    email = models.EmailField(max_length=500, unique=True)
    first_name = models.CharField(max_length=80, null=True, blank=True)
    last_name = models.CharField(max_length=80, null=True, blank=True)
    headline = models.CharField(max_length=60, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    language = models.CharField(max_length=7, choices=LANGUAGES, default='en')
    photo = models.ImageField(null=True, blank=True, upload_to=avatar_upload_location, storage=PrivateMediaStorage())
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    paypal_email = models.EmailField(null=True, blank=True)
    objects = UserManager()
    
    inactive_reason = models.TextField(blank=True)
    favorites = models.ManyToManyField('courses.Course',related_name='favorites',blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("first_name", "last_name")

    def __str__(self):
        if self.is_instructor:
            return f'{self.email}-Instructor'
        return self.email
    
    @cached_property
    def handle(self):
        return slugify(f"{self.first_name} {self.last_name}")
    

    @cached_property
    def balance(self):
        """ user balance (payout)
            NOTE*:
                orders - payouts = running
        """
        def __trans(type_):
            trans = self.instructor_transactions.filter(type=type_)
            return sum([i.net_amount for i in trans])

        return __trans('sale') - __trans('payout')

    @cached_property
    def payout_balance(self):
        """ user available balance to be
            sent to his account
        """
        th = timezone.now().date() - datetime.timedelta(days=settings.PAYOUT_THRESHOLD)

        def __trans(**kwargs):
            trans = self.instructor_transactions.filter(**kwargs)
            return sum([i.net_amount for i in trans])

        return __trans(type='sale', date_updated__date__lt=th) - __trans(type='payout')


    def get_passwordtoken(self, code):
        """ return password token
        """
        from apps.users.models import PasswordToken
        return get_object_or_404(PasswordToken, code=code)

    def create_passwordtoken(self):
        """ create a user password token
            to reset their password.
        """
        from apps.users.models import PasswordToken
        return PasswordToken.objects.create(user=self)

    def send_passwordreset(self, send_email=True):
        """ create and send the password reset link
            to the user's email.
        """
        token = self.create_passwordtoken()
        if send_email: token.send()
        return token

    @cached_property
    def stats(instance):
        from .classes import UserClass
        courses = instance.courses.all()
        return {
            'classes': list(instance.user_classes.values_list('course', flat=True)) + list(courses.values_list('id', flat=True)),
            'courses': courses.count(),
            'published_courses': courses.filter(status=CourseStatus.STATUS_PUBLISHED).count(),
            'students': UserClass.objects.filter(course__user=instance, is_purchased=True).distinct('user').count(),
            'ratings': instance.overall_ratings
        }

    @cached_property
    def overall_ratings(instance):
        """ Return 0% to 100% rating to percent """
        overall_ratings = 0
        for course in instance.courses.filter(is_deleted=False):
            overall_ratings += course.total_rate 
        
        return round(overall_ratings  / 5 * 100, 2)
    
    @cached_property
    def is_instructor(self):
        if hasattr(self, 'instructor'):
            return True
        return False
    
    @cached_property
    def fullname(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def profile_completion(self):
        fields = ["email", "first_name","last_name", "headline","bio", "language", "photo","paypal_email"]
        filled_values_count = 0
        for field in fields:
            field_value = getattr(self, field)
            if  field_value:
                filled_values_count += 1
        return f'{filled_values_count}/{len(fields)}' 

class Instructor(AutoCreatedUpdatedMixin):
    """ instructor
    """
    class Meta:
        db_table = 'instructors'
        
    user = models.OneToOneField(User, related_name="instructor", on_delete=models.CASCADE)
    payout_method = models.ForeignKey(to='transactions.PaymentType', blank=True, null=True, on_delete=models.SET_NULL)
    payout_pay_active = models.BooleanField(default=True)
    group_name = models.CharField(max_length=20, choices = InstructorGroups.choices, default=InstructorGroups.DEFAULT, blank=True)
    group = models.ForeignKey(InstructorGroup, null=True, blank=True, on_delete=models.SET_NULL, related_name='group_instructor')
    instructor_consent = models.JSONField(default=dict)
    public_profile = models.BooleanField(default=True)
    public_courses = models.BooleanField(default=True)

    def __str__(self):
        return f"<Instructor> {self.id}"

    @cached_property
    def ratings(self):
        """ instructor's total ratings
        """
        def __rate():
            for c in self.user.courses.all():
                yield c.total_rate

        rating = list(__rate())
        count = len(list(filter(None, rating)))
        return sum(rating) / (count or 1)
    
    @property
    def profile_completion(self):
        # my_model_fields = [field.name for field in self._meta.get_fields()]
        fields = ["email", "first_name","last_name", "headline","bio", "language", "photo","paypal_email","payout_pay_active","group_name","payout_method"]
        filled_values_count = 0
        
        # import pdb; pdb.set_trace()
        for field in fields:
            field_value = getattr(self.user, field)
            ifield_value = getattr(self, field)
            if  field_value or ifield_value:
                filled_values_count += 1
        return f'{filled_values_count}/{len(fields)}'

class SubscribedNewsLater(AutoCreatedUpdatedMixin):
    """
        Subscribed user for newsletetr
    """
    email_address = models.EmailField(max_length=250, unique=True)

    def __str__(self):
        return self.email_address
    
########## =========================  Signals ======================================##############

@receiver(post_save, sender=User)
def after_save_user(instance=None, created=False, **kwargs):
    if not hasattr(instance, 'cart'):
        from apps.users.models import Cart
        Cart.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def user_instructor_payouts_update(instance=None, created=False, **kwargs):
    if hasattr(instance, 'instructor') and not instance.is_active:
        from apps.transactions.tasks import update_inactive_instructor_payouts
        update_inactive_instructor_payouts(instance.id)


@receiver(post_save, sender=Instructor)
def instructor_payouts_update(instance=None, created=False, **kwargs):
    if not instance.payout_pay_active:
        from apps.transactions.tasks import update_inactive_instructor_payouts
        update_inactive_instructor_payouts(instance.user.id)
        
class NotificationSettings(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'notification_settings'
        
    user = models.OneToOneField(User, related_name="notification_settings", on_delete=models.CASCADE)
    course_recommendations = models.BooleanField(default=True)
    annoucements = models.BooleanField(default=True)
    promotional_emails = models.BooleanField(default=True)
    
    def __str__(self):
        return f"<Notification Settings> {self.id}"