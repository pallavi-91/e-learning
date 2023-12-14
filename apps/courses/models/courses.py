import uuid
import os
from django.conf import settings
import json
from django.conf.global_settings import LANGUAGES
from django.db import models, transaction
from django.contrib.postgres.fields import ArrayField
from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
from django.dispatch import receiver
from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from apps.courses.models.lectures import Lecture, LectureResource
from apps.courses.models.quizs import Assignment, StudentAssignment
from apps.courses.models.sections import SubSection
from apps.status import CourseLectureType, CourseResourceMode, CourseSkillLevel, CourseStatus, CourseType, NotesType, OrderStatus
from apps.status.mixins import AutoCreatedUpdatedMixin
from apps.utils.cloudflare import CloudflareStream
from django.utils.functional import cached_property
from django.contrib.auth import get_user_model
from apps.users.models import UserClass
from django.db.models import Func, F, FloatField, Sum, Q, Case, When, Count
from django.db.models.expressions import Value
from django.db.models.functions import Cast, Coalesce, TruncDate
from itertools import groupby
from apps.utils.query import get_object_or_none
from apps.utils.helpers import (
    calc_read_time,
    count_words,
    file_info,
    quill_delta_to_text,
    sizeof_fmt,
)
from apps.utils.slugify import unique_slugify
from apps.currency.models import Currency
from core.store.storage_backends import CoursesMediaStorage, PrivateMediaStorage

def courses_code(*args, **kwargs):
    code = uuid.uuid4()
    existing  = Course.objects.filter(code=code).count()
    while existing:
        code = uuid.uuid4()
        existing  = Course.objects.filter(code=code).count()
    return code

MAX_RATE = 5


def course_main_media(obj, filename):
    """ set course main media image
    """
    return f"users/{obj.user.id}/courses/{obj.code}/{filename}"

    
class Course(AutoCreatedUpdatedMixin):
    """ instructor course
    """
    class Meta:
        db_table = 'courses'
    
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    user = models.ForeignKey(get_user_model(),verbose_name="Instructor",
        related_name="courses", on_delete=models.CASCADE)

    title = models.CharField(max_length=60)
    slug = models.SlugField(max_length=500,null=True,blank=True)
    type = models.CharField(max_length=60,choices=CourseType.choices, default=CourseType.PAID)
    currency = models.ForeignKey(Currency, blank=True, null=True, on_delete=models.SET_NULL)
    pricing = models.ForeignKey('CoursePrice', blank=True, null=True, on_delete=models.SET_NULL)
    subtitle = models.CharField(max_length=120, null=True, blank=True)
    desc = models.TextField(null=True, blank=True)
    description = models.JSONField(default=dict,null=True, blank=True)
    image = models.ImageField(upload_to=course_main_media, null=True, blank=True, storage=PrivateMediaStorage())

    # should be delete
    promo_video = models.FileField(upload_to=course_main_media, null=True, blank=True, storage=CoursesMediaStorage())

    video_info = models.JSONField(default=dict, null=True, blank=True)
        
    is_promote = models.BooleanField(default=False)

    skill_level = models.CharField(max_length=20, choices=CourseSkillLevel.choices, default=CourseSkillLevel.SKILL_ALL)
    category = models.ForeignKey('Category', related_name="courses",
        null=True, blank=True, on_delete=models.SET_NULL)
    subcategory = models.ForeignKey('SubCategory', related_name="courses",
        null=True, blank=True, on_delete=models.SET_NULL)
    language = models.CharField(max_length=7, choices=LANGUAGES, default='en')
    topics = models.ManyToManyField('Topic',related_name='courses',blank=True)
    status = models.CharField(max_length=20, choices=CourseStatus.choices, default=CourseStatus.STATUS_DRAFT)

    begin_msg = models.TextField(null=True, blank=True)
    completion_msg = models.TextField(null=True, blank=True)

    price = models.DecimalField(max_digits=999, decimal_places=2, default=0.00)
    included_in_promo = models.BooleanField(default=False)

    date_published = models.DateTimeField(null=True, blank=True)

    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title}"
    
    def save(self, **kwargs):
        unique_slugify(self, self.title) 
        return super(Course, self).save(**kwargs)
    
    @transaction.atomic
    def update_section_position(self):
        index = 0
        for sec in self.sections.order_by('position'):
            index += 1
            sec.position = index
            sec.save()
    
        return self

    @cached_property
    def objectives(self):
        return self.course_objectives.values_list('content', flat=True)
    
    @cached_property
    def learners(self):
        return self.course_learners.values_list('content', flat=True)
    
    @cached_property
    def requirements(self):
        return self.course_requirements.values_list('content', flat=True)

    @cached_property
    def image_info(self):
        if self.image:
            size = self.image.size
            mbsize = '{:.2f}'.format(int(size) / float(1 << 20))
            return {
                "filename": os.path.basename(self.image.name),
                "size": size,
                "mbsize": mbsize
            }
        return {}
    
    @cached_property
    def duration(self):
        return self.video_length

    @cached_property
    def currency_code(self):
        if self.currency:
            return self.currency.currency_code
        return ''
        
    @cached_property
    def quiz_count(self):
        quizzes = SubSection.objects.filter(type=SubSection.QUIZ)
        return quizzes.count()

    @cached_property
    def assignment_count(self):
        assignment = SubSection.objects.filter(type=SubSection.ASSIGNMENT)
        return assignment.count()

    @cached_property
    def article_count(self):
        articles = Lecture.objects.prefetch_related('section_cource').filter(section__course=self,type=CourseLectureType.ARTICLE)
        return articles.count()

    @cached_property
    def resources_count(self):
        resources = LectureResource.objects.prefetch_related('lecture', 'section__course').filter(lecture__section__course=self)
        return resources.count()

    @cached_property
    def total_reviews(self):
        return self.reviews.select_related('reviews').count()

    @cached_property
    def total_rate(self):
        total = 0
        reviews = self.reviews.select_related('reviews').values('rate')
        for review in reviews:
            total += review.get('rate')

        return round(total / (len(reviews) or 1),1) # round to 1 decimals to prevent long decimals


    @cached_property
    def total_assignments(self):
        return Assignment.objects.select_related('section__course').filter(section__course_id=self.id).count()

    @cached_property
    def total_submissions(self):
        return StudentAssignment.objects.prefetch_related('assignment','section__course').filter(assignment__section__course=self, type=StudentAssignment.PUBLISH).count()

    @cached_property
    def is_editable(self):
        return self.status in [CourseStatus.STATUS_REJECTED, CourseStatus.STATUS_DRAFT]

    @transaction.atomic
    def approve(self):
        self.status = CourseStatus.STATUS_PUBLISHED
        self.date_published = timezone.now()
        rejects = self.rejects.prefetch_related('rejects').all()
        for reject in rejects:
            reject.is_resolve = True
            reject.save()
        self.save()
        return self

    @cached_property
    def video_length(self):
        lectures = self.lectures.filter(type=CourseLectureType.VIDEO, video_info__status='completed')
        total = sum([lect.video_info.get('duration', 0) for lect in lectures.iterator()])
        return total

    @cached_property
    def listed_price(self):
        if self.currency and self.pricing:
            return self.currency.rounding(self.pricing.price)
        return 0
    
    @cached_property
    def sale_price(self):
        # TODO: Minus Course Discount
        return self.listed_price
    
    @cached_property
    def lectures(self):
        return Lecture.objects.select_related('section__course').filter(section__course=self)
    
    
    @cached_property
    def resource_mode(self):
        result =  self.lectures.annotate(total_rectures=Count('id')).values('id', 'type', 'total_rectures').aggregate(mode=Case(
            When(
                total_rectures=Count('id', filter=Q(type=CourseLectureType.VIDEO)), then=Value(CourseResourceMode.VIDEO_BASED)
            ),
            When(
                total_rectures=Count('id', filter=Q(type=CourseLectureType.ARTICLE)), then=Value(CourseResourceMode.ARTICLE_BASED)
            ),
            When(
                ~Q(total_rectures=Count('id', filter=Q(type=CourseLectureType.ARTICLE))), then=Value(CourseResourceMode.HYBRID)
            ),
            default=Value(None),
        ))
        
        if result.get('mode') != NotImplemented:
            return result.get('mode')
        return ""
    
    @property
    def needed_for_review(self):
        description_text = quill_delta_to_text(self.description)
        is_free = self.pricing and self.pricing.is_free

        objectives_valid = len(self.objectives) >= 4 and all(text for text in self.objectives)
        requirements_valid = len(self.requirements) >= 1 and all(text for text in self.requirements)
        learners_valid = len(self.learners) >= 1 and all(text for text in self.learners)

        return {
            'instructor': {
                'bio': False if self.user.bio else True,
                'language': False if self.user.language else True,
                'first_name': False if self.user.first_name else True,
                'last_name': False if self.user.last_name else True,
                'email': False if self.user.email else True,
                # 'paypal_email': False if self.user.paypal_email else True,
            },
            'curriculum': {
                'video_length': False if not (self.video_length / 60) < 30 else True,
                'lectures': False if not  self.lectures.count() < 5 else True,
                'free_video_length': False if not is_free else True if (self.video_length / 60) > 120  else False # if video is free and exceed to two hours
            },
            'intended_learners': {
                'objectives': False if objectives_valid else True,
                'requirements': False if requirements_valid else True,
                'learners': False if learners_valid else True
            },
            'details': {
                'title': False if self.title else True,
                'subtitle': False if self.subtitle else True,
                'skill_level': False if self.skill_level else True,
                'language': False if self.language else True,
                'category': False if self.category else True,
                'subcategory': False if self.subcategory else True,
                'description': False if count_words(description_text) >= 60 else True,
                'topics': False if self.topics.count() >= 1 else True,
                'image': False if self.image else True,
                'video_info': False if self.video_info.get('status') == 'completed' else True,
            },
            'pricing': {
                'price': False if self.pricing else True,
                'is_promoted': False if self.is_promote else True,
            }
        }

    @cached_property   
    def is_valid_for_review(self):
        # If there is a true in a needed for review it means it is invalid
        if 'true' in  json.dumps(self.needed_for_review):
            return False
        return True

    @cached_property
    def orders_this_month(self):
        from apps.users.models import Order
        orders = Order.objects.prefetch_related('classes', 'classes_course').filter(classes__course=self,status=OrderStatus.COMPLETED,
                      date_created__month=timezone.now().month)
        return orders
        
    @cached_property
    def is_bestseller(self):
        return self.orders_this_month.count() >= settings.SOLD_PER_MONTH 
    
    @cached_property
    def minute_watched(self):
        minute_watched = 0
        for cls in self.classes.prefetch_related('subsections', 'subsections__progress').iterator():
            for subsection in cls.subsections.select_related('lecture').filter(type = SubSection.LECTURE).iterator():
                progress = subsection.progress.all()
                if progress.exists():
                    if subsection.lecture.type == CourseLectureType.VIDEO:
                        total_duration = progress.aggregate(value=Coalesce(
                            Sum('watched_duration'),
                            0
                        ))
                        minute_watched += total_duration.get('value') * 60 # Use minutes from seconds
                    else:
                        article_info = subsection.lecture.article_info
                        minute_watched += article_info.get('duration') * 60 # Use minutes from seconds
        return minute_watched
    
    @cached_property   
    def course_gross_revenue(self):
        classes = self.classes.select_related('currency').filter(is_purchased=True)
        current_currency = self.currency_code
        revenue_price = sum([cls.currency.exchange.convert(cls.price, cls.currency_code, current_currency) if cls.currency.currency_code != current_currency else cls.price
                             for cls in classes.iterator()])
        
        return revenue_price # Substract the other expenses to get net revenue

    @cached_property   
    def median_completion_times(self):
        classes = self.classes.prefetch_related('subsections','subsections__progress')\
        .filter(is_purchased=True).order_by('-date_updated')
        data_list = []
        
        for cls in classes.iterator():
            for subsection in cls.subsections.all().iterator():
                if not subsection.progress.exists():
                    continue
                progress_set = subsection.progress.order_by('-date_updated').first()
                delta = (progress_set.date_updated - cls.date_updated) / 2
                median_date = cls.date_updated + delta
                data_list.append({
                    "completion_days": (median_date - cls.date_updated).days
                })

        context = []
        for completion_days, group in groupby(sorted(data_list, key=lambda x: x['completion_days']), key=lambda x: x['completion_days']):
            context.append({
                "count": len(list(group)),
                "days": int(completion_days)
            })

        return context

class CourseObjective(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_objectives'
    
    course = models.ForeignKey('Course', related_name='course_objectives',on_delete=models.CASCADE)
    content = models.TextField()

    def __str__(self) -> str:
        return f'<CourseObjectives>: {self.content}'

class CourseRequirement(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_requirements'
    
    course = models.ForeignKey('Course', related_name='course_requirements',on_delete=models.CASCADE)
    content = models.TextField()

    def __str__(self) -> str:
        return f'<CourseRequirement>: {self.content}'

class CourseLearner(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_learners'
    
    course = models.ForeignKey('Course', related_name='course_learners',on_delete=models.CASCADE)
    content = models.TextField()

    def __str__(self) -> str:
        return f'<CourseLearner>: {self.content}'
    
class CourseView(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_viewed'
        
    course = models.ForeignKey('Course',related_name='views',on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(),related_name='viewed_courses',on_delete=models.SET_NULL,null=True,)
    ip = models.GenericIPAddressField(null=True,blank=True)

    def __str__(self) -> str:
        return f'#{self.id} ({self.ip}) {self.course}'


class Topic(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_topics'
        
    name = models.CharField(max_length=60)
    slug = models.SlugField(max_length=500,null=True,blank=True)

    def __str__(self) -> str:
        return f'#{self.id} {self.name}'

    @cached_property
    def courses_used(self):
        return self.courses.select_related('courses').count()

    

@receiver(pre_save,sender=Topic)
def pre_save_topic(instance,**kwargs):
    instance.name = instance.name.lower()
    unique_slugify(instance, instance.name) 
     

class Note(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_notes'
        
    subsection = models.ForeignKey('SubSection',on_delete=models.CASCADE,related_name='notes')
    user_class = models.ForeignKey(UserClass,related_name='notes',on_delete=models.CASCADE)
    content = models.JSONField(default=dict)
    user = models.ForeignKey(get_user_model(),related_name='notes',on_delete=models.CASCADE)
    metadata = models.JSONField(default=dict)
    type = models.CharField(max_length=10, choices=NotesType.choices, default=NotesType.NOTE)
        
    def __str__(self) -> str:
        return str(self.id)

class CoursePrice(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_prices'
        verbose_name = 'Pricing Tier'
        ordering = ['-id']
        
    """Pricing Tier"""
    price = models.FloatField(default=0)
    name = models.CharField(max_length=50, unique=True)
    tier_level = models.IntegerField(default=0, help_text=_('Hint: 0 is free'), unique=True) # 0 is not good for ordering
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name= "pricing_tiers")
    price_tier_status = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return self.name
    
    @cached_property
    def is_free(self):
        """Tier Level 0 is for the free course"""
        return self.tier_level == 0
    
    @cached_property
    def listed_price(self):
        return self.currency.rounding(self.price)


class CourseReject(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'rejected_courses'
        
    content = models.JSONField(default=dict)
    user = models.ForeignKey(get_user_model(),related_name='course_rejects',on_delete=models.CASCADE)  
    course = models.ForeignKey(Course,related_name='rejects',on_delete=models.CASCADE)  
    is_resolve = models.BooleanField(default=False) 

    def __str__(self) -> str:
        return f'Course #{self.id}'

    class Meta:
        verbose_name_plural = _('Reject (Reasons)')


class CourseAnnouncement(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'course_announcements'
        
    user = models.ForeignKey(get_user_model(),related_name='course_announcements',on_delete=models.CASCADE)  
    content = models.JSONField(default=dict)    
    course = models.ForeignKey(Course,related_name='announcements',on_delete=models.CASCADE)
    seen = models.ManyToManyField(get_user_model(),related_name='seen_announcements',blank=True)  


class Scope(AutoCreatedUpdatedMixin):
    """ course scope
    """
    class Meta:
        db_table = 'course_scope'
        
    course = models.ForeignKey(Course,
        related_name="scope", on_delete=models.CASCADE)
    text = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.text}"


# Updated item in quickbook
def update_product_in_quickbook(sender, instance, created, **kwargs):
    from apps.quickbooks.client import QuickbookClient
    qb_client = QuickbookClient()
    description_text = quill_delta_to_text(instance.description)
    payload = {
                 "title": instance.title,
                 "date_updated": instance.date_updated,
                 "id": instance.id,
                 "price": instance.price,
                 "description": description_text
             } 
    result = qb_client.add_or_get_product(payload)
    print('Add service ', result)

# post_save.connect(update_product_in_quickbook, Course)
