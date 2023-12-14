import pdb
from django.conf.global_settings import LANGUAGES
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Count, Q, Sum, FloatField

from rest_framework import serializers,exceptions
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import Serializer, ModelSerializer
from apps.apis.marketfront.courses.serializers import CourseCategorySerializer, CourseSubCategorySerializer, SectionSerializer, ShortAssignmentSerializer, StudentAssignmentSerializer
from apps.apis.marketfront.sections.serializers import AssignmentSerializer, LectureSerializer, QuizSerializer, StudentQuizSerializer
from django.db.models.functions import Coalesce
from apps.apis.marketfront.users.serializers import UserShortSerializer
from apps.courses.models import Section
from apps.utils.cloudflare import CloudflareStream
from apps.users.models import UserClass, User
from apps.utils.serializers import DynamicFieldsModelSerializer
from apps.apis.common.serializer_cache import SerializerCacheMixin

from apps.utils.validators import validate_file_extension, validate_file_size, video_ext
from apps.courses.models import (
    Course,
    Category,
    CoursePrice,
    CourseReview,
    SubCategory,
    Scope,
    SubSection,
    SubsectionProgress,
    Topic,
)

class CourseReviewSerializer(ModelSerializer):
    is_liked = serializers.SerializerMethodField()
    is_disliked = serializers.SerializerMethodField()
    is_reported = serializers.SerializerMethodField()
    content = serializers.CharField(allow_null=True,allow_blank=True,required=False)

    class Meta:
        model = CourseReview
        read_only_fields = ['user','course']
        exclude = ('likes','dislikes',)

    def to_representation(self, instance):
        d = super().to_representation(instance)
        d['likes'] = instance.likes.all().count()
        d['user'] = UserShortSerializer(instance.user, context=self.context).data
        d['dislikes'] = instance.dislikes.all().count()
        d['reports'] = instance.reports.all().count()

        return d

    def create(self, validated_data):
        request = self.context.get('request')
        if  validated_data.get('course').reviews.prefetch_related('reviews').filter(user=request.user).count():
            raise PermissionDenied(_('You already wrote a review on this course')) 

        return super().create(validated_data)

    def get_is_liked(self,instance):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user in instance.likes.all():
            return True
            
        return False

    def get_is_disliked(self,instance):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user in instance.dislikes.all():
            return True

        return False

    def get_is_reported(self,instance):
        request = self.context.get('request')
        if request and request.user.is_authenticated and instance.reports.filter(user=request.user).count():
            return True

        return False

class TopicSerializer(serializers.ModelSerializer):
    courses_count = serializers.SerializerMethodField()
    class Meta:
        model = Topic
        read_only_fields = ('slug',)
        fields = [
            'name',
            'id',
            'slug',
            'courses_count',
        ]

    def validate_name(self,data: str):
        return data.lower()

    def get_or_create(self):
        topic = self.Meta.model.objects.get_or_create(
            **self.validated_data,defaults=self.validated_data)
        return topic

    def get_courses_count(self,instance):
        return instance.courses.count()
    
class SubCategorySerializer(DynamicFieldsModelSerializer):
    related_topics = serializers.SerializerMethodField()
    class Meta:
        model = SubCategory
        read_only_fields = ('slug',)
        fields = (
            'id',
            'name',
            'slug',
            'category',
            'related_topics'
        )

    def get_related_topics(self,instance):
        data = Topic.objects.filter(courses__subcategory=instance).distinct('id')[0:5]
        return  TopicSerializer(data,many=True).data 
    
class CategorySerializer(DynamicFieldsModelSerializer):
    """ category serializer
    """
    subcategories = SubCategorySerializer(many=True)

    class Meta:
        model = Category
        read_only_fields = ('slug',)
        fields = (
            'id',
            'name',
            'slug',
            'subcategories',
        )

class ScopeSerializer(ModelSerializer):
    """ course scope
    """
    class Meta:
        model = Scope
        fields = (
            'id',
            'text',
            'course',
        )


class CoursePriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoursePrice
        fields = '__all__'
        
class CourseSerializer(ModelSerializer):
    """ course serializer
    """

    duration = serializers.SerializerMethodField()
    article_count = serializers.SerializerMethodField()
    sections_total = serializers.SerializerMethodField()
    is_rated = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    is_in_cart = serializers.SerializerMethodField()
    is_owned = serializers.SerializerMethodField()
    sale_price = serializers.SerializerMethodField()
    promo_video = serializers.FileField(
            validators=[validate_file_size(),validate_file_extension(video_ext)],
            required=False,allow_null=True,allow_empty_file=True
    )

    class Meta:
        model = Course
        read_only_fields = ('user','scope','video_info','status','slug')
        fields = [
            'id',
            'article_count',
            'slug',
            'code',
            'user',
            'title',
            'subtitle',
            'description',
            'pricing',
            'currency',
            'image',
            'desc',
            'promo_video',
            'skill_level',
            'video_info',
            'is_favorite',
            'is_in_cart',
            'is_owned',
            'type',
            'is_promote',
            'duration',
            'sale_price',
            'sections_total',
            'is_rated',
            'language',
            'date_updated'
        ]   


    def to_representation(self, instance):
        """ customize to return the object data instead
            of just the id.
        """
        subsections = SubSection.objects.prefetch_related('section').select_related('section__course').filter(section__course=instance)
        context = super(CourseSerializer, self).to_representation(instance)
        context['user'] = UserShortSerializer(instance.user, context=self.context).data
        context['lecture_total'] = subsections.filter(type=SubSection.LECTURE).count()
        context['quiz_total'] = subsections.filter(type=SubSection.QUIZ).count()
        context['assignment_total'] = subsections.filter(type=SubSection.ASSIGNMENT).count()
        context['student_total'] = instance.classes.filter(is_purchased=True).count() # purchased count in instructor dashboard
        context['total_rate'] = instance.total_rate
        context['total_reviews'] = instance.total_reviews
        context['currency'] = instance.currency_code
        context['is_bestseller'] = instance.is_bestseller
        # context['video_info'] = CloudflareStream.signed_playback_url(instance.video_info)
        context['pricing'] = CoursePriceSerializer(instance.pricing,context=self.context).data
        context['category'] = CourseCategorySerializer(instance.category).data
        context['subcategory'] = CourseSubCategorySerializer(instance.subcategory).data
        context['objectives'] = instance.objectives
        return context

    def get_duration(self,instance):
        return instance.duration
    
    def get_sale_price(self,instance):
        return instance.sale_price

    def get_article_count(self,instance):
        return instance.article_count

    def get_is_favorite(self,instance):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False

        return instance in user.favorites.all()

    def get_is_owned(self,instance):
        # check if the user is the owner of course
        # or if the user bought the course
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False

        return user.id == instance.user.id or user.user_classes.filter(course=instance,is_purchased=True).exists()


    def get_is_in_cart(self,instance):
        user = self.context.get('request').user
        if not user.is_authenticated and not hasattr(user, 'cart'):
            return False
        return user.cart.items.filter(course=instance).exists()

    def get_sections_total(self,instance):
        return instance.sections.count()

    def get_is_rated(self,instance):
        request = self.context.get('request')
        if request and request.user.is_authenticated and instance.reviews.filter(user=request.user).exists():
            return True

        return False

    def create(self, validated_data):
        # User with Instructor account only allowed to add course
        user = self.context.get('request').user
        if not hasattr(user,'instructor'):
            raise exceptions.PermissionDenied()

        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):

        # Update topics with m2m set
        topics = validated_data.pop('topics',None)
        if isinstance(topics,list): 
            instance.topics.set(topics)
        
        # if 'promo_video' in validated_data:
        #     video = validated_data.pop('promo_video')
        #     uid = instance.video_info.get('uid')
            # stream = CloudflareStream(video,video_id=uid)
            # if video == None and uid:
            #     stream.delete()
            #     validated_data['video_info'] = { }
            # elif video:
            #     stream.metadata = {
            #         'name': f'Course#{instance.id} ({instance.title}) - {video.name}',
            #         'course_id': f'{instance.id}',
            #         'type': 'promo'
            #     }
            #     validated_data['video_info'] = stream.upload()
        return super().update(instance, validated_data)

class ShortCourseSerializer(ModelSerializer):
    
    class Meta:
        model = Course
        read_only_fields = ('user','video_info','status','slug')
        fields = [
            'id',
            'code',
            'article_count',
            'slug',
            'code',
            'user',
            'title',
            'subtitle',
            'description',
            'pricing',
            'currency',
            'image',
            'desc',
            'video_info',
            'status',
        ]
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['currency'] = instance.currency_code
        context['duration'] = instance.duration
        context['user'] = UserShortSerializer(instance.user, context=self.context).data
        context['category'] = CourseCategorySerializer(instance.category).data
        return context
    
        
class ClassSerializer(SerializerCacheMixin, ModelSerializer):
    class Meta:
        model = UserClass
        fields = (
            'id',
            'code',
            'user',
            'course',
            'price',
            'is_purchased',
            'archived',
        )
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['progress_total'] = instance.progress_total
        context['actual_progress'] = instance.actual_progress
        context['course'] = CourseSerializer(instance.course, context=self.context).data
        return context

class ShortClassSerializer(ModelSerializer):
    course = ShortCourseSerializer()
    
    class Meta:
        model = UserClass
        fields = (
            'id',
            'code',
            'user',
            'course',
            'currency',
            'price',
            'is_purchased',
            'archived',
            'certificate'
        )

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['currency'] = instance.currency_code
        return context

class ClassSectionSerializer(ModelSerializer):
    """ section serializer
    """
    duration = serializers.SerializerMethodField()
    class Meta:
        model = Section
        read_only_fields = ['subsections']
        fields = "__all__"

    def to_representation(self, instance):
        data= super().to_representation(instance)
        subsections = instance.subsections.select_related('assignment', 'quiz', 'lecture', 'section').prefetch_related('progress').all()
        data["subsections"] = ClassSubsectionSerializer(subsections, many=True, context=self.context).data
        return data

    def get_duration(self,instance):
        return instance.duration
    
    
class ClassSubsectionSerializer(ModelSerializer):
    class Meta:
        model = SubSection
        fields = '__all__'
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        request = self.context.get('request')
        context['preview'] = instance.preview
        result = instance.progress.filter(Q(user=request.user)).aggregate(progress=Coalesce(Sum('watched_duration'), 0, output_field=FloatField()))
        context['progress'] = round(result.get('progress'),0)
        context['is_completed'] = instance.progress.filter(Q(user=request.user) & Q(is_completed=True)).exists()

        if instance.type == self.Meta.model.QUIZ:
            context['quiz'] = QuizSerializer(instance.quiz, context=self.context).data
            if request.user.is_authenticated:
                student_quiz = request.user.student_quizzes.filter(quiz=instance.quiz)
                if student_quiz.exists():
                    context['student_quiz'] = StudentQuizSerializer(student_quiz.last(), context=self.context).data 
        
        if instance.type == self.Meta.model.ASSIGNMENT:
            context['assignment'] = AssignmentSerializer(instance.assignment, context=self.context).data
            if request.user.is_authenticated:
                student_assignments = request.user.student_assignments.filter(assignment=instance.assignment).last()
                if student_assignments:
                    context['student_assignment'] = StudentAssignmentSerializer(student_assignments, context=self.context).data 
        
        if instance.type == self.Meta.model.LECTURE:
            context['lecture'] = LectureSerializer(instance.lecture, context=self.context).data
            
        return context
    
class SubsectionProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubsectionProgress
        read_only_fields = ['user']
        fields = '__all__'

    def update_or_create(self):
        request = self.context.get('request') 
        subsection = self.validated_data.get('subsection')
        progress, is_created =self.Meta.model.objects.update_or_create(
            user=request.user,
            subsection=subsection,
            defaults={'position': self.validated_data.get('position'),
                      'watched_duration': self.validated_data.get('watched_duration'),
                      'is_completed': self.validated_data.get('is_completed')}
        )
        # TODO update is_completed by duration with lecture duration
        return progress


class ToggleCompleteSerializer(serializers.Serializer):
    subsection = serializers.PrimaryKeyRelatedField(queryset=SubSection.objects.prefetch_related('section', 'section__course').all())
    is_completed = serializers.BooleanField(required=False,allow_null=True)
    
    class Meta:
        model = SubSection
        fields = '__all__'
        
    @transaction.atomic
    def toggle(self,_class: UserClass):
        request = self.context.get('request') 
        is_completed = self.validated_data.get('is_completed', None)  
        sub = self.validated_data.get('subsection')  

        # If the subsection is mark as complete the progress will be completed as well
        if is_completed != None:
            progress, is_created = SubsectionProgress.objects.get_or_create(user=request.user,subsection=sub)
            progress.is_completed = is_completed
            progress.save()

        is_exists = sub in _class.subsections.all()
        if  is_exists:
            if is_completed: return _class
            _class.subsections.remove(sub)
        else:
            _class.subsections.add(sub)

        return _class