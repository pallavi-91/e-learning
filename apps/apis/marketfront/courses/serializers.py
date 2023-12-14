from dataclasses import fields
import os
import pdb
from wsgiref import validate
from django.conf.global_settings import LANGUAGES

from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Count

from rest_framework import serializers,exceptions
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import Serializer, ModelSerializer

from apps.apis.marketfront.users.serializers import CartSerializer, InstructorSerializer, InstructorUserSerializer, UserSerializer, UserShortSerializer
from apps.status import CourseLectureType, CourseStatus
from apps.utils.cloudflare import CloudflareStream
from apps.utils.helpers import get_client_ip

from apps.utils.query import get_object_or_none

from apps.users.models import UserClass, User
from apps.utils.serializers import DynamicFieldsModelSerializer
from apps.utils.validators import validate_file_extension, validate_file_size, video_ext
from apps.courses.models import (
    Assignment,
    AssignmentQuestion,
    Course,
    Category,
    CourseAnnouncement,
    CoursePrice,
    CourseReject,
    CourseReview,
    CourseView,
    LectureResource,
    Note,
    Quiz,
    QuizAnswer,
    QuizQuestion,
    ReportedCourseReview,
    StudentAssignment,
    StudentAssignmentAnswer,
    StudentQuiz,
    StudentQuizAnswer,
    SubCategory,
    Section,
    Lecture,
    Scope,
    SubSection,
    SubsectionProgress,
    Topic,
    QnA,
    QnAReplys,
    ReportedQnaReply,
)


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
            'article_count',
            'slug',
            'id',
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
        context['student_total'] = instance.classes.filter(is_purchased=True).count() # purchased count in instructor dashboard
        context['total_rate'] = instance.total_rate
        context['total_reviews'] = instance.total_reviews
        context['currency'] = instance.currency_code
        context['is_bestseller'] = instance.is_bestseller
        context['pricing'] = CoursePriceSerializer(instance.pricing,context=self.context).data
        context['objectives'] = instance.objectives
        # Check if this course is owned by user
        user = self.context.get('request').user
        if user.is_authenticated and user.id != instance.user.id:
            classes = user.user_classes.filter(course=instance,is_purchased=True).values('id','code', 'archived').last()
            if classes:
                context['user_class'] = classes
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

        return user == instance.user or user.user_classes.filter(course=instance, is_purchased=True).exists()

    

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
        if isinstance(topics,list): instance.topics.set(topics)
        
        # if 'promo_video' in validated_data:
        #     video = validated_data.pop('promo_video')
        #     uid = instance.video_info.get('uid')
        #     stream = CloudflareStream(video,video_id=uid)
        #     if video == None and uid:
        #         stream.delete()
        #         validated_data['video_info'] = { }
        #     elif video:
        #         stream.metadata = {
        #             'name': f'Course#{instance.id} ({instance.title}) - {video.name}',
        #             'course_id': f'{instance.id}',
        #             'type': 'promo'
        #         }
        #         validated_data['video_info'] = stream.upload()
        return super().update(instance, validated_data)


class CourseDetailSerializer(CourseSerializer):
    """ course detail serializer
    """
    
    def to_representation(self, instance):
        context = super(CourseDetailSerializer, self).to_representation(instance)
        context['user'] = InstructorUserSerializer(instance.user, context=self.context).data
        context['category'] = CourseCategorySerializer(instance.category).data
        context['subcategory'] = CourseSubCategorySerializer(instance.subcategory).data
        return context
        
class CourseQnASerializer(serializers.ModelSerializer):
    class Meta:
        model = QnA
        fields = (
            'id',
            'title',
            'user',
            'user_class',
            'description',
            'subsection',
            'date_created',
            'date_updated',
        )
        read_only_fields = ['user','user_class','date_created','date_updated']
        
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['user'] = UserShortSerializer(instance.user).data
        context['upvoted'] = instance.upvoted_users.count()
        context['subsection'] = NoteSubsectionSerializer(instance.subsection, context=self.context).data
        return context
    
    
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
        context['upvoted'] = instance.upvoted_users.count()
        context['is_reported'] = instance.reported
        return context

class ReportedQnaReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportedQnaReply
        fields = ['id', 'issue', 'user', 'reply', 'description', 'date_created']
        read_only_fields = ['user', 'reply']


class AdminCourseSerializer(CourseSerializer):

    class Meta(CourseSerializer.Meta):
        pass

    def to_representation(self, instance):
        context = super().to_representation(instance)
        section = instance.sections.first()
        subsection = section.subsections.first() if section else None
        context['first_subsection'] = SubSectionSerializer(subsection,context=self.context).data if subsection else None
        return context

class CourseSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category']

class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class SubCategorySerializer(DynamicFieldsModelSerializer):
    related_topics = serializers.SerializerMethodField()
    totalcourse = serializers.SerializerMethodField()
    
    class Meta:
        model = SubCategory
        read_only_fields = ('slug',)
        fields = (
            'id',
            'name',
            'slug',
            'category',
            'totalcourse',
            'related_topics'
        )

    def get_related_topics(self, instance):
        data = Topic.objects.filter(courses__subcategory=instance).distinct('id')[0:5]
        return  TopicSerializer(data,many=True).data
    
    def get_totalcourse(self, instance):
        return instance.courses.count()

class CategorySerializer(DynamicFieldsModelSerializer):
    """ category serializer
    """
    class Meta:
        model = Category
        read_only_fields = ('slug',)
        fields = (
            'id',
            'name',
            'icon',
            'slug',
        )

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['totalcourse'] = instance.courses.count()
        context['subcategories'] = SubCategorySerializer(instance.subcategories.prefetch_related('courses').all(), many=True).data
        return context

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

class CourseSectionSerializer(ModelSerializer):
    """ section serializer
    """
    duration = serializers.SerializerMethodField()
    class Meta:
        model = Section
        read_only_fields = ['subsections']
        fields = (
            'id',
            'title',
            'position',
            'duration',
            'subsections'
        )

    def to_representation(self, instance):
        context= super(CourseSectionSerializer,self).to_representation(instance)
        context['subsections'] = SubSectionSerializer(instance.subsections.all(),context=self.context, many= True).data
        context["quiz_count"] = instance.subsections.filter(type=SubSection.QUIZ).count()
        context["assignment_count"] = instance.subsections.filter(type=SubSection.ASSIGNMENT).count()
        context["lecture_count"] = instance.subsections.filter(type=SubSection.LECTURE).count()
        return context

    def get_duration(self,instance):
        return instance.duration
    
class SectionSerializer(ModelSerializer):
    """ section serializer
    """
    duration = serializers.SerializerMethodField()
    class Meta:
        model = Section
        read_only_fields = ['subsections']
        fields = (
            'id',
            'title',
            'position',
            'duration',
            'subsections'
        )

    def to_representation(self, instance):
        context = super(SectionSerializer,self).to_representation(instance)
        context["quiz_count"] = instance.subsections.filter(type=SubSection.QUIZ).count()
        context["assignment_count"] = instance.subsections.filter(type=SubSection.ASSIGNMENT).count()
        context["lecture_count"] = instance.subsections.filter(type=SubSection.LECTURE).count()
        return context

    def get_duration(self,instance):
        return instance.duration

    
class CourseContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = (
            'id',
            'title',
        )
        
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['sections'] = CourseSectionSerializer(instance.sections.prefetch_related('subsections').all(),context=self.context, many= True).data
        return context
    
class PublicSubsectionSerializer(ModelSerializer):
    """ public subsection serializer
    """
    title = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = SubSection
        fields = (
            'title',
            'duration',
            'type',
        )

    def get_title(self, instance):
        content= instance.lecture or instance.quiz or instance.assignment
        return content.title

    def get_type(self, instance):
        return instance.lecture.type if instance.lecture else instance.type

    def get_duration(self, instance):
        if not instance.lecture: return 0
        lecture_info = {
            CourseLectureType.ARTICLE: instance.lecture.article_info,
            CourseLectureType.VIDEO: instance.lecture.video_info,
        }
        if instance.lecture.type:
            return lecture_info[instance.lecture.type].get('duration')
        return 0


class LectureResourceSerializer(ModelSerializer):
    """ lecture resource serializer
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


class LectureSerializer(ModelSerializer):
    """ lecture serializer
    """
    video = serializers.FileField(
        validators=[validate_file_extension(video_ext), validate_file_size(1000 * 1024 * 1024)], # 1gb
        required=False,allow_null=True,allow_empty_file=True)

    resources = LectureResourceSerializer(many=True,required=False)
    deleted_resources = serializers.ListField(
        required=False,
        child=serializers.PrimaryKeyRelatedField(
            write_only=True,queryset=LectureResource.objects.all()
        )
    )
        
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
            'resources',
            'deleted_resources'
        )

    def to_representation(self, instance):
        context = super().to_representation(instance)
        # add additional fields for video type
        # lectures.
        if(instance.type == CourseLectureType.VIDEO ):
            # prepare the video info from cdn77 secure token
            # r['video'] = {
            #     **{'url':  r['video'] if instance.video else ''},
            #     **CloudflareStream.signed_playback_url(instance.video_info),
            # }
            pass

        if(instance.type == CourseLectureType.ARTICLE ):
            context['article'] = {
                'data': context["article"],
                **instance.article_info
            }
        return context

    @transaction.atomic
    def create(self, validated_data):
        resources = validated_data.pop("resources",[])
        # has_video = 'video' in validated_data
        # video = validated_data.pop("video",None)
        instance = super(LectureSerializer,self).create(validated_data)

        # has_video and self._upload_video(instance=instance,video=video)

        serializer = LectureResourceSerializer(many=True,data=resources)
        serializer.is_valid(raise_exception=True)
        serializer.save(lecture=instance)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data,**kwargs):
        resources = validated_data.pop("resources",[])
        deleted_resources = validated_data.pop("deleted_resources",[])
        instance = super(LectureSerializer,self).update(instance,validated_data)

        serializer = LectureResourceSerializer(many=True,data=resources)
        serializer.is_valid(raise_exception=True)
        serializer.save(lecture=instance)
        for deleted in deleted_resources:
            deleted.delete()

        return instance


    @transaction.atomic
    def _upload_video(self,instance,video):
        if instance.type != CourseLectureType.VIDEO: return
        
        uid = instance.video_info.get('uid')
        # stream = CloudflareStream(video,video_id=uid)
        # video_info = { }

        # if video == None and uid:
        #     stream.delete()
        #     video_info = { }
        # elif video:
        #     stream.metadata = {
        #         'name': f'Lecture#{instance.id} ({instance.title}) - {video.name}',
        #         'course_id': f'{instance.section.course.id}',
        #         'instructor_id': f'{instance.section.course.user.id}',
        #         'type': 'lecture'
        #     }
        #     video_info = stream.upload()
        # instance.video_info = video_info
        instance.save()

class ShortLectureSerializer(ModelSerializer):
    """ lecture serializer
    """
    class Meta:
        model = Lecture
        fields = (
            'id',
            'title',
            'type'
        )

class QuizAnswerSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(allow_null=True,required=False,queryset=QuizAnswer.objects.all())
    class Meta:
        model = QuizAnswer
        read_only_fields = ['quiz_question'] 
        fields = '__all__'

    def get_filename(self, instance):
        """ get the filename
        """
        path_, name = os.path.split(instance.file.name)
        return name


class ClassSerializer(ModelSerializer):
    course = CourseSerializer()
    progress_total = serializers.SerializerMethodField()
    first_subsection = serializers.SerializerMethodField()
    actual_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = UserClass
        read_only_fields = ['subsections']
        fields = (
            'id',
            'user',
            'course',
            'subsections',
            'price',
            'first_subsection',
            'progress_total',
            'actual_progress',
        )


    # The toggle state is like a bookmark, so the progress_total is not the actual percent that user completed the course
    # this function will calculate the actual progress percentage
    def get_actual_progress(self,instance):
        
        progresses = instance.user.class_progress.filter(subsection__section__course=instance.course)
        total = 0
        for progress in progresses:
            if progress.is_completed:
                total += 1

        return round(total / (SubSection.objects.select_related('section__course').filter(section__course=instance.course).count() or 1) * 100)

    def get_progress_total(self,instance):
        # NOTE: Can be change using the aggregate
        total = 0
        for section in instance.course.sections.prefetch_related('subsections').all():
            total += section.subsections.count()

        return total

    def get_first_subsection(self,instance):
        section = instance.course.sections.prefetch_related('subsections').first()
        if section:
            current_progress = SubsectionProgress.objects.select_related('subsection').filter(
                subsection__section__course=instance.course,
            ).order_by('-date_updated').first()

            if current_progress:
                subsection = current_progress.subsection
            else:
                subsection = section.subsections.first()

            return SubSectionSerializer(subsection,context=self.context).data if subsection else None
        return None


class QuizQuestionSerializer(serializers.ModelSerializer):

    answers = QuizAnswerSerializer(many=True,min_length=2)
    deleted_answers = serializers.ListField(
        required=False,
        child = serializers.PrimaryKeyRelatedField(required=False,queryset=QuizAnswer.objects.all())
    )

    class Meta:
        model = QuizQuestion
        read_only_fields = ['quiz'] 
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data,**kwargs):
        answers = validated_data.pop('answers',[])
        deleted_answers = validated_data.pop('deleted_answers',[])
        instance = super().create(validated_data,**kwargs)

        if not instance.quiz.section.course.is_editable:
            raise exceptions.PermissionDenied()

        serializer = QuizAnswerSerializer(many=True,data=answers)
        serializer.is_valid(raise_exception=True)
        serializer.save(quiz_question=instance)
        return instance

    @transaction.atomic
    def update(self,instance, validated_data):
        answers = validated_data.pop('answers',[])
        deleted_answers = validated_data.pop('deleted_answers',[])
        data = super().update(instance,validated_data)

        if not instance.quiz.section.course.is_editable:
            raise exceptions.PermissionDenied()

        for ans in answers:
            serializer = QuizAnswerSerializer(instance=ans.pop('id',None),data=ans)
            serializer.is_valid(raise_exception=True)
            serializer.save(quiz_question=data)
            
        for deleted_answer in deleted_answers:
            deleted_answer.delete()

        return data


class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True,required=False)
    class Meta:
        model = Quiz
        read_only_fields = ['section'] 
        fields = '__all__'

class QuizShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'title']


class AssignmentQuestionSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(allow_null=True,required=False,queryset=AssignmentQuestion.objects.all())
    class Meta:
        model = AssignmentQuestion
        read_only_fields = ['assignment']
        fields = '__all__'


    def create(self, validated_data,**kwargs):
        validated_data.pop('id',None)
        instance = super(AssignmentQuestionSerializer,self).create(validated_data,**kwargs)
        return instance

    def update(self,instance, validated_data):
        assignment = self.validated_data.pop('id',instance)
        res = super(AssignmentQuestionSerializer,self).update(assignment,validated_data)
        return res

class ShortAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ['id', 'title']

class AssignmentSerializer(serializers.ModelSerializer):
    
    questions = AssignmentQuestionSerializer(many=True,required=False)
    deleted_questions = serializers.ListField(
        required=False,
        child=serializers.PrimaryKeyRelatedField(queryset=AssignmentQuestion.objects.all())
    )
    class Meta:
        model = Assignment
        read_only_fields = ['section','questions']
        fields = '__all__'

    @transaction.atomic
    def update(self, instance, validated_data):
        questions = validated_data.pop('questions')
        deleted_questions = validated_data.pop('deleted_questions')
        data = super().update(instance, validated_data)

        for question in questions:
            serializer =AssignmentQuestionSerializer(instance=question.pop('id',None),data=question)
            serializer.is_valid(raise_exception=True)
            serializer.save(assignment=data)

        for deleted_question in deleted_questions:
            deleted_question.delete()

        return data


class SubSectionSerializer(serializers.ModelSerializer):
    quiz = QuizSerializer(required=False)
    lecture = LectureSerializer(required=False)
    assignment = AssignmentSerializer(required=False)
    student_quiz = serializers.SerializerMethodField()
    student_assignment = serializers.SerializerMethodField()
    current_progress = serializers.SerializerMethodField()

    class Meta:
        model = SubSection
        read_only_fields = ['section']
        fields = '__all__'

    def get_current_progress(self,instance):
        user_id = self.context.get('user_id')
        if not user_id:return None

        progress = get_object_or_none(instance.progress.select_related('user').all(), user=user_id)

        return SubsectionProgressSerializer(progress).data if progress else None 

    def get_student_assignment(self,instance):
        request = self.context.get('request')
        if not request or not request.user.id or instance.type != self.Meta.model.ASSIGNMENT: return None
        data = get_object_or_none(request.user.student_assignments.select_related('user').prefetch_related('student_assignments').all(), assignment=instance.assignment)
        return StudentAssignmentSerializer(data,context=self.context).data if data else None


    def get_student_quiz(self,instance):
        request = self.context.get('request')
        if not request or not request.user.id or instance.type != self.Meta.model.QUIZ: return None
        data = get_object_or_none(request.user.student_quizzes.select_related('user').all(), quiz=instance.quiz)
        return StudentQuizSerializer(data,context=self.context).data if data else None


class SubsectionPositionSerializer(serializers.Serializer):
    position = serializers.IntegerField(required=True)
    subsection = serializers.PrimaryKeyRelatedField(queryset=SubSection.objects.prefetch_related('section', 'section__course').all())

    class Meta:
        model = SubSection


class ToggleCompleteSerializer(serializers.Serializer):
    subsection = serializers.PrimaryKeyRelatedField(queryset=SubSection.objects.prefetch_related('section', 'section__course').all())
    is_completed = serializers.BooleanField(required=False,allow_null=True)
    class Meta:
        model = SubSection

    @transaction.atomic
    def toggle(self,_class: UserClass):
        request = self.context.get('request') 
        is_completed = self.validated_data.get('is_completed')  
        sub = self.validated_data.get('subsection')  

        # If the subsection is mark as complete the progress will be completed as well
        if is_completed: 
            progress, is_created = SubsectionProgress.objects.get_or_create(user=request.user,subsection=sub)
            progress.is_completed = True
            progress.save()

        is_exists = sub in _class.subsections.all()
        if  is_exists:
            if is_completed: return _class
            _class.subsections.remove(sub)
        else:
            _class.subsections.add(sub)

        return _class


class StudentQuizAnswerSerializer(serializers.ModelSerializer):

    class Meta: 
        model = StudentQuizAnswer
        read_only_fields = ['student_quiz']
        fields = '__all__'


class StudentQuizSerializer(serializers.ModelSerializer):
    student_answers = StudentQuizAnswerSerializer(many=True)
    class Meta: 
        model = StudentQuiz
        read_only_fields = ['user','quiz']
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data,**kwargs):
        user = self.context.get('request').user
        student_answers = validated_data.pop('student_answers',[])
        student_quiz = get_object_or_none(user.student_quizzes.all(),quiz=validated_data.get('quiz'))

        if student_quiz:
            raise exceptions.PermissionDenied()

        instance = super(StudentQuizSerializer,self).create(validated_data,**kwargs)
        
        for student_answer in student_answers:
            StudentQuizAnswer.objects.create(**student_answer,student_quiz=instance)
        return instance


# Read only serializer
class StudentAssignmentAnswerDetailSerializer(serializers.ModelSerializer):
    question = AssignmentQuestionSerializer(read_only=True)
    class Meta: 
        model = StudentAssignmentAnswer
        read_only_fields = ['student_assignment']
        fields = '__all__'


# Read only serializer
class StudentAssignmentDetailSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    student_answers = StudentAssignmentAnswerDetailSerializer(many=True,read_only=True)

    class Meta: 
        model = StudentAssignment
        fields = '__all__'



class StudentAssignmentSerializer(serializers.ModelSerializer):
    class Meta: 
        model = StudentAssignment
        read_only_fields = ['user','assignment']
        fields = '__all__'


class BillingSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    full_name = serializers.CharField(required=True)
    address = serializers.CharField(required=True)

    courses = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=Course.objects.all()),required=False)

    class Meta:
        model = User
        fields = ('email','full_name','address','courses')

    def validate_email(self,data):
        request = self.context.get("request")

        if request.user.is_authenticated: return data
        if get_object_or_none(User,email=data):
            raise serializers.ValidationError(_("Email already exists"))

        return data

    @transaction.atomic
    def purchased(self):
        request = self.context.get("request")
        if request.user.is_authenticated:
            request.user.cart.purchase()
            request.user.cart.clear()
        else:
            user = User.objects.create(email=self.validated_data.get("email"))
            data = [ { 'course': course.id } for course in self.validated_data.get("courses")]
            serializer = CartSerializer(data=data,many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(cart=user.cart)
            user.cart.purchase()
            user.cart.clear()

        return


class CourseReviewSerializer(ModelSerializer):

    is_liked = serializers.SerializerMethodField()
    is_disliked = serializers.SerializerMethodField()
    is_reported = serializers.SerializerMethodField()
    content = serializers.CharField(allow_null=True,allow_blank=True,required=False)

    class Meta:
        model = CourseReview
        read_only_fields = ['user','course']
        exclude = ('likes','dislikes')

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['likes'] = instance.likes.all().count()
        context['user'] = UserShortSerializer(instance.user,context=self.context).data
        context['dislikes'] = instance.dislikes.all().count()
        context['reports'] = instance.reports.all().count()
        return context

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


class MyCourseReviewSerializer(CourseReviewSerializer):
    class Meta(CourseReviewSerializer.Meta):
        pass

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['user'] = UserShortSerializer(instance.user,context=self.context).data
        context['course'] = CourseSerializer(instance.course,context=self.context).data
        return context


class CourseSubmissionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Course
        fields = [
            'title',
            'image',
            'code',
            'id',
            'desc',
        ]

    def to_representation(self, instance):
        context = super(CourseSubmissionSerializer,self).to_representation(instance)
        context['total_assignments'] = instance.total_assignments
        context['total_submissions'] = instance.total_submissions
        return context
        

class CourseFeedbackSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(required=True,queryset=StudentAssignmentAnswer.objects.all())
    feedback = serializers.CharField(required=True)

    class Meta:
        model = StudentAssignmentAnswer
        fields = ['feedback']
     

class ReviewSubmissionSerializer(serializers.Serializer):

    data = CourseFeedbackSerializer(many=True)

    @transaction.atomic
    def feedback(self):
        data = self.validated_data.get('data')
        for d in data:
            instance = d.pop('id')
            instance.__dict__.update(**d)
            instance.save()

        return data
    

class CourseActionSerializer(Serializer):

    class Meta:
        model = CourseReview
        fields = ['user']

    def like(self,user):
        """Return true if like the review return false if remove the like"""
        self.instance.dislikes.remove(user)

        if user in self.instance.likes.all():
            self.instance.likes.remove(user)
            return False
        else:
            self.instance.likes.add(user)
            return True

    def dislike(self,user):
        """Return true if dislike the review return false if remove the like"""
        self.instance.likes.remove(user)
        if user in self.instance.dislikes.all():
            self.instance.dislikes.remove(user)
            return False
        else:
            self.instance.dislikes.add(user)
            return True


class ReportedCourseReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportedCourseReview
        fields = ['user', 'review', 'issue', 'description']
        read_only_fields = ['user','review']

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['user'] = UserShortSerializer(instance.user,context=self.context).data
        return context
    
class CourseAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseAnnouncement
        read_only_fields = ['user','course']
        fields = '__all__'

class CourseRejectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseReject
        read_only_fields = ['user','course']
        fields = '__all__'


class CoursePriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoursePrice
        fields = '__all__'
    
    def to_representation(self, instance):
        context =  super().to_representation(instance)
        context['price'] = instance.listed_price
        return context

class NoteSubsectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSection
        fields = ['id', 'type']

    def to_representation(self, instance):
        context = super().to_representation(instance)
        if instance.type == self.Meta.model.QUIZ:
            context['quiz'] = QuizShortSerializer(instance.quiz, context=self.context).data
        
        if instance.type == self.Meta.model.ASSIGNMENT:
            context['assignment'] = ShortAssignmentSerializer(instance.assignment, context=self.context).data
        
        if instance.type == self.Meta.model.LECTURE:
            context['lecture'] = ShortLectureSerializer(instance.lecture, context=self.context).data
        return context
    
class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        read_only_fields = ['user','user_class','subsection']
        fields = ['id', 'content', 'metadata', 'subsection', 'type', 'date_created', 'date_updated']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        user_class = get_object_or_none(user.user_classes, pk=validated_data.get('user_class_id'))
        if not user_class:
            raise PermissionDenied()
        return super().create(validated_data)

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['subsection'] = NoteSubsectionSerializer(instance.subsection, context=self.context).data
        return context



class ClassSectionSerializer(ModelSerializer):
    """ section serializer
    """
    duration = serializers.SerializerMethodField()
    class Meta:
        model = Section
        fields = "__all__"

    def to_representation(self, instance):
        context= super().to_representation(instance)
        context["subsections"] = SubSectionSerializer(instance.subsections.select_related('assignment', 'quiz', 'lecture', 'section').prefetch_related('progress'),context=self.context,many=True).data
        return context

    def get_duration(self,instance):
        return instance.duration


class SubsectionProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubsectionProgress
        read_only_fields = ['user']
        fields = '__all__'

    def update_or_create(self):
        request = self.context.get('request') 
        subsection = self.validated_data.get('subsection')
        progress,is_created =self.Meta.model.objects.update_or_create(
            user=request.user,
            subsection=subsection,
            defaults={'position': self.validated_data.get('position') }
        )
        return progress



class MarketplaceCountSerializer(Serializer):
    class Meta:
        model = Course

    def counts(self):
        context = {}
        context['type'] = self.get_type()
        context['length'] = self.get_length()
        context['ratings'] = self.get_ratings()
        return context

    @property
    def _qs(self):
        return self.Meta.model.objects.filter(status=CourseStatus.STATUS_PUBLISHED,is_deleted=False)

    @property
    def _filtered_qs(self):
        request = self.context.get('request')
        views = self.context.get('view')
        queryset = self._qs

        if request.user.is_authenticated:
            queryset = queryset.exclude(user=request.user).exclude(id__in=request.user.user_classes.values_list('course', flat=True))

        return views.filter_queryset(queryset) 

    def get_type(self):
        free_qs = self._filtered_qs.filter(pricing__tier_level__lte=0)
        return {
            'free': free_qs.count(),
            'paid': self._filtered_qs.exclude(id__in=[q.id for q in free_qs ]).count()
        }

    def get_length(self):
        qs = self._filtered_qs
        one_hour = 3600
        three_hours = one_hour * 3
        six_hours = one_hour * 6
        ten_hours = one_hour * 10 
        
        return {
            'zero_to_one': len(list(filter(lambda x: x.duration >= 0 and x.duration < one_hour  ,qs))),
            'one_to_three': len(list(filter(lambda x: x.duration > one_hour and x.duration < three_hours  ,qs))),
            'three_to_six': len(list(filter(lambda x: x.duration > three_hours and x.duration < six_hours  ,qs))),
            'six_to_ten': len(list(filter(lambda x: x.duration > six_hours and x.duration < ten_hours  ,qs))),
            'ten_plus': len(list(filter(lambda x: x.duration > ten_hours  ,qs)))
        }

    def get_ratings(self):
        qs = self._filtered_qs
        
        return {
            'five': len(list(filter(lambda x: x.total_rate == 5  ,qs))),
            'four': len(list(filter(lambda x: x.total_rate >= 4  ,qs))),
            'three': len(list(filter(lambda x: x.total_rate >= 3  ,qs))),
            'two': len(list(filter(lambda x: x.total_rate >= 2  ,qs))),
            'one': len(list(filter(lambda x: x.total_rate >= 1,qs)))
        }


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


class CourseViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseView
        fields = '__all__'

    def get_or_create(self,course):
        request = self.context.get('request')
        if not request.user.is_staff and course.user.id != request.user.id:
            return self.Meta.model.objects.get_or_create(
                ip=get_client_ip(request),
                date_created__month=timezone.now().month,
                user=request.user if request.user.is_authenticated else None,
                course=course
            )
            
        return None


class MarketplaceSlugSerializer(serializers.Serializer):

    class Meta:
        model = Course

    @property
    def _qs(self):
        return self.Meta.model.objects.filter(status=CourseStatus.STATUS_PUBLISHED,is_deleted=False)

    @property
    def _filtered_qs(self):
        request = self.context.get('request')
        views = self.context.get('view')
        queryset = self._qs

        if request.user.is_authenticated:
            queryset = queryset.exclude(user=request.user).exclude(id__in=request.user.user_classes.values_list('course', flat=True))

        return views.filter_queryset(queryset) 


    def slug_data(self,title=None,slug=None):
        qs = self._filtered_qs
        # featured course is most viewed course 
        popular_courses = qs.filter(date_created__month=timezone.now().month)\
                    .annotate(views_count=Count('views'))\
                    .order_by('-views_count')[0:8]

        return CourseSerializer(popular_courses, context=self.context, many=True).data