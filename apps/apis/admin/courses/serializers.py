import os
from rest_framework import serializers
from apps.apis.admin.pricing.serializers import CurrencySerializer
from apps.apis.admin.users.instructors.serializers import UserProfileSerializer, UserDetailProfileSerializer
from apps.courses.models import Category, Course, SubSection, Topic, SubCategory
from apps.courses.models import (
    Assignment, 
    AssignmentQuestion, 
    Lecture, 
    LectureResource, 
    Quiz, 
    QuizAnswer, 
    QuizQuestion, 
    Section, 
    CourseChangeHistory,
    QnA,
    QnAReplys,
    ReportedQnaReply,
    )
from apps.apis.marketfront.users.serializers import UserShortSerializer
from apps.courses.models.courses import CoursePrice 
from apps.status import CourseLectureType
from apps.users.models import UserClass
from django.db.models import Avg, Sum, Q, Count

from apps.utils.validators import validate_file_extension, validate_file_size, video_ext

class CourseTopicsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    class Meta:
        model = Topic
        fields = ['id', 'name']

class CourseSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category']

class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class CourseSerializer(serializers.ModelSerializer):
    topics = CourseTopicsSerializer(many=True, required=False)

    class Meta:
        model = Course
        fields = ['id', 
                    'code', 
                    'title', 
                    'type', 
                    'status', 
                    'date_created', 
                    'skill_level', 
                    'category', 
                    'subcategory', 
                    'description',
                    'desc',
                    'language', 
                    'date_updated', 
                    'date_published', 
                    'topics',]
        
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['user'] = UserProfileSerializer(instance.user).data
        context['category'] = CourseCategorySerializer(instance.category).data
        context['sold_courses'] = instance.classes.filter(is_purchased=True).count()
        context['total_reviews'] = instance.total_reviews
        context['total_rate'] = instance.total_rate
        context['sale_price'] = instance.sale_price
        context['listed_price'] = instance.listed_price
        context['resource_mode'] = instance.resource_mode
        context['course_topics'] = instance.sections.prefetch_related('subsections').aggregate(
                                    total_sections=Count('id'),
                                    total_lectures=Count('subsections__id', filter=Q(subsections__type=SubSection.LECTURE)),\
                                    total_assignments=Count('subsections__id', filter=Q(subsections__type=SubSection.ASSIGNMENT)),\
                                    total_quiz=Count('subsections__id', filter=Q(subsections__type=SubSection.QUIZ))
                                    )
        return context

    def update(self, instance, validated_data):
        topics_data = validated_data.pop('topics', None)
        instance.topics.clear()
        if topics_data:
            instance.topics.set([topic['id'] for topic in topics_data])
        return super().update(instance, validated_data)
    

class CourseStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'code', 'title', 'type', 'status', 'date_created', 'date_updated', 'date_published']
        
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['enrollments'] = instance.classes.count()
        context['sold_courses'] = instance.classes.filter(is_purchased=True).count()
        context['withdrawn'] = instance.classes.select_related('transactions').filter(transactions__refund=True).count()
        context['completed_classes'] = instance.classes.prefetch_related('subsections').filter(subsections__progress__is_completed=True).count()
        context['minute_watched'] = instance.minute_watched
        return context


class CourseDetailSerializer(serializers.ModelSerializer):
    topics = CourseTopicsSerializer(many=True, required=False)
    class Meta:
        model = Course
        fields = ['id', 
                  'code', 
                  'title', 
                  'subtitle',
                  'type', 
                  'currency',
                  'pricing',
                  'desc',
                  'description',
                  'image',
                  'promo_video',
                  'video_info',
                  'is_promote',
                  'skill_level',
                  'category',
                  'subcategory',
                  'language',
                  'topics',
                  'price',
                  'date_published',
                  'status', 
                  'date_created', 
                  'date_updated', 
                  'date_published']
    
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['user'] = UserDetailProfileSerializer(instance.user).data
        context['category_info'] = CourseCategorySerializer(instance.category).data
        context['total_reviews'] = instance.total_reviews
        context['total_rate'] = instance.total_rate
        context['resource_mode'] = instance.resource_mode
        context['image_info'] = instance.image_info
        return context


# ====================================  Course Sections Serializers =====================================

class QuizAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswer
        fields = ['id','answer', 'is_correct', 'expected']

class QuizQuestionSerializer(serializers.ModelSerializer):
    answers = QuizAnswerSerializer(many=True, min_length=100)
    class Meta:
        model = QuizQuestion
        fields = ['id', 'question', 'answers']

        
class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id','title', 'questions']
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['questions'] = QuizQuestionSerializer(instance.questions.all(), many=True).data
        return context

class AssignmentQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentQuestion
        fields = ['id', 'question', 'expected']

class AssignmentSerializer(serializers.ModelSerializer):
    questions = AssignmentQuestionSerializer(many=True,required=False)
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'questions']

class LectureResourceSerializer(serializers.ModelSerializer):
    """ Course lecture resource serializer
    """
    filename = serializers.SerializerMethodField()
    file = serializers.FileField(validators=[validate_file_size(10 * 1024 * 1024)],required=True)

    class Meta:
        model = LectureResource
        read_only_fields = ('lecture',)
        fields = (
            'id',
            'lecture',
            'file',
            'filename',
        )

    def get_filename(self, instance):
        """ get the filename
        """
        path_, name = os.path.split(instance.file.name)
        return name


class LectureSerializer(serializers.ModelSerializer):
    """ lecture serializer
    """
    resources = LectureResourceSerializer(many=True,required=False)
    class Meta:
        model = Lecture
        read_only_fields = ('section','video_info')
        fields = (
            'id',
            'title',
            'section',
            'video',
            'video_id',
            'article',
            'position',
            'type',
            'preview',
            'resources',
            'video_info',
        )

    def to_representation(self, instance):
        context = super().to_representation(instance)
        if(instance.type == CourseLectureType.ARTICLE ):
            context['article'] = {
                'data': context["article"],
                **instance.article_info
            }
        return context
        
class SubSectionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SubSection
        fields = ['id', 'type', 'position', 'preview', 'date_created', 'date_updated']

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['preview'] = instance.preview

        if instance.type == self.Meta.model.QUIZ:
            context['quiz'] = QuizSerializer(instance.quiz, context=self.context).data
        
        if instance.type == self.Meta.model.ASSIGNMENT:
            context['assignment'] = AssignmentSerializer(instance.assignment, context=self.context).data
        
        if instance.type == self.Meta.model.LECTURE:
            context['lecture'] = LectureSerializer(instance.lecture, context=self.context).data
            
        return context


class SectionSerializer(serializers.ModelSerializer):
    """Course section serializer"""
    class Meta:
        model = Section
        fields = (
            'id',
            'title',
            'position',
        )

class CourseChangeHistorySerializer(serializers.ModelSerializer):
    """Course feedback history"""
    class Meta:
        model = CourseChangeHistory
        fields = '__all__'
        read_only_fields = ['course', 'user']
        
class CourseUserProgressSerializer(serializers.ModelSerializer):
    """Course user progress sereializer """
    class Meta:
        model = UserClass
        fields = ['id', 'progress_total','total_minutes_watch']
        
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['user'] = UserDetailProfileSerializer(instance.user).data
        return context
    
class UserCertificationSerializer(serializers.ModelSerializer):
    """Course user certification sereializer """
    
    finished_at = serializers.SerializerMethodField()
    watched_time = serializers.SerializerMethodField()

    class Meta:
        model = UserClass
        fields = ['id', 'progress_total','certificate', 'certificate_number','finished_at','watched_time']
        
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['user'] = UserDetailProfileSerializer(instance.user).data
        return context
    
    def get_watched_time(self, instance):
        """ get watched time
        """
        purchase_date = instance.date_updated
        watched_time = instance.subsections.prefetch_related('progress').order_by('-position').values('date_updated')
        if watched_time:
            finished_date = watched_time[0]['date_updated']
            return (finished_date - purchase_date)
        return 0
    
    def get_finished_at(self, instance):
        """ get finished at time
        """
        finished_at = instance.subsections.prefetch_related('progress').order_by('-position').values('date_updated')
        if finished_at:
            return finished_at[0]['date_updated']
        return ''

class ReportedQnaReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportedQnaReply
        fields = ['id', 'issue', 'user', 'reply', 'description', 'date_created']
        read_only_fields = ['user', 'reply']

class CourseQnAReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = QnAReplys
        fields = (
            'id',
            'qna',
            'user',
            'comment',
            'date_created',
            'date_updated',
        )
        read_only_fields = ['date_created', 'qna', 'user','date_updated']
        
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['user'] = UserShortSerializer(instance.user).data
        context['is_reported'] = instance.reported
        context['reports'] = ReportedQnaReplySerializer(instance.reports, many=True, context=self.context).data
        return context 

class CoursePricingSerializer(serializers.ModelSerializer):
    currency = CurrencySerializer()
    class Meta:
        model = CoursePrice
        fields = [
            'id',
            'price',
            'name',
            'currency',
            'price_tier_status',
            'tier_level',]