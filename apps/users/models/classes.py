from functools import cached_property
import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.timezone import localdate, localtime
from django.db.models import Q, Count, Sum, FloatField
from django.db import models
from apps.status.mixins import AutoCreatedUpdatedMixin
from core.store.storage_backends import PrivateMediaStorage
from django.db.models.functions import Coalesce

def course_certificate_media(obj, filename):
    """ set course certificate media pdf
    """
    return f"users/{obj.user.id}/courses/{obj.course.code}/{filename}"



class UserClass(AutoCreatedUpdatedMixin):
    """ Product
    """
    class Meta:
        db_table = 'user_classes'
        
    # user is optional for users that have purchased
    # the course but haven't created an account yet.
    code = models.UUIDField(default=uuid.uuid4, editable=False, null=True)

    user = models.ForeignKey(get_user_model(),
        related_name="user_classes", null=True, blank=True, on_delete=models.SET_NULL)
    
    course = models.ForeignKey('courses.Course',
        related_name="classes", on_delete=models.CASCADE)
    subsections = models.ManyToManyField('courses.SubSection', related_name='classes', blank=True)

    currency = models.ForeignKey('currency.Currency', related_name="classes", on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=999, decimal_places=2, default=0.00)

    order = models.ForeignKey('Order',
        related_name="classes", on_delete=models.CASCADE,null=True,blank=True)
    is_purchased = models.BooleanField(default=False)
    archived = models.BooleanField(default=False, help_text='less frequently used')

    certificate = models.FileField(upload_to=course_certificate_media, null=True, blank=True, storage=PrivateMediaStorage())
    certificate_number = models.PositiveBigIntegerField(default=0)

    def __str__(self):
        return f"<UserClass>:({self.id})"

    @cached_property
    def currency_code(self):
        try:
            return self.currency.currency_code
        except:
            return ''

    @cached_property
    def progress_total(self):
        result = self.subsections.prefetch_related('progress').filter(Q(progress__user=self.user)).aggregate(progress=Count('id'))
        return round(result.get('progress') / (self.subsections_total or 1) * 100)
    
    @cached_property
    def actual_progress(self):
        result = self.subsections.prefetch_related('progress').filter(Q(progress__user=self.user)).aggregate(progress=Count('id', filter=Q(progress__is_completed=True)))
        return round(result.get('progress') / (self.subsections_total or 1) * 100)
    
    @cached_property
    def total_minutes_watch(self):
        result = self.subsections.prefetch_related('progress').filter(Q(progress__user=self.user)).aggregate(minute_watch_time=Coalesce(Sum('position', filter=Q(progress__is_completed=True)), 0, output_field=FloatField()))
        return result.get('minute_watch_time')
    
    @cached_property
    def students_completed_course(self):
        result = self.subsections.prefetch_related('progress').filter(Q(progress__user=self.user)).aggregate(progress=Count('id', filter=Q(progress__is_completed=True)))
        return result.get('progress')

    @cached_property
    def subsections_total(self):
        return self.subsections.count()
    
    @cached_property
    def remaining_days(self):
        time_diff = localtime()- self.date_created
        if time_diff.days > settings.REFUND_PERIOD_THRESHOLD:
            return 0
        return settings.REFUND_PERIOD_THRESHOLD - time_diff.days