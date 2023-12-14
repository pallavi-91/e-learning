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

from apps.apis.marketfront.users.serializers import CartSerializer, UserSerializer, UserShortSerializer
from apps.status import CourseLectureType
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
)

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
        data= super(SectionSerializer,self).to_representation(instance)
        data["quiz_count"] = instance.subsections.filter(type=SubSection.QUIZ).count()
        data["assignment_count"] = instance.subsections.filter(type=SubSection.ASSIGNMENT).count()
        data["lecture_count"] = instance.subsections.filter(type=SubSection.LECTURE).count()
        return data

    def get_duration(self,instance):
        return instance.duration

class StudentAssignmentAnswerDetailSerializer(serializers.ModelSerializer):
    question = AssignmentQuestionSerializer(read_only=True)
    class Meta: 
        model = StudentAssignmentAnswer
        read_only_fields = ['student_assignment']
        fields = '__all__'
        
class StudentAssignmentDetailSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    student_answers = StudentAssignmentAnswerDetailSerializer(many=True,read_only=True)

    class Meta: 
        model = StudentAssignment
        fields = '__all__'


class StudentAssignmentAnswerSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=StudentAssignmentAnswer.objects.all(),allow_null=True,required=False)
    class Meta: 
        model = StudentAssignmentAnswer
        read_only_fields = ['student_assignment']
        fields = '__all__'
    
    
class StudentAssignmentSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    student_answers = StudentAssignmentAnswerSerializer(many=True)

    class Meta: 
        model = StudentAssignment
        read_only_fields = ['user','assignment']
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data, **kwargs):
        user = self.context.get('request').user
        student_answers = validated_data.pop('student_answers',[])
        # if user has an assignment that means he already answered the assignment
        if user.student_assignments.filter(assignment=validated_data.get('assignment')).exists():
            raise exceptions.ValidationError("Already has answered.")

        input_questions = set([item.get('question').id for item in student_answers])
        assignment_questions = set(validated_data.get('assignment').questions.values_list('id', flat=True))
        if not input_questions <= assignment_questions:
            raise exceptions.ValidationError("Some of the questions are not from current assignment.")
        
        instance = super(StudentAssignmentSerializer,self).create(validated_data,**kwargs)
        for student_answer in student_answers:

            StudentAssignmentAnswer.objects.create(**student_answer,student_assignment=instance)
        return instance


    @transaction.atomic
    def update(self, instance, validated_data,**kwargs):
        student_answers = validated_data.pop('student_answers',[])

        input_questions = set([item.get('question').id for item in student_answers])
        assignment_questions = set(validated_data.get('assignment').questions.values_list('id', flat=True))
        if not input_questions <= assignment_questions:
            raise exceptions.ValidationError("Some of the questions are not from current assignment.")
        
        super(StudentAssignmentSerializer,self).update(instance, validated_data)
        for student_answer in student_answers:
            id = student_answer.pop("id",None)
            if id:
                id.__dict__.update(**student_answer)
                id.save()
            else:
                StudentAssignmentAnswer.objects.create(**student_answer,student_assignment=instance)

        return instance


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
        r = super().to_representation(instance)
        # add additional fields for video type
        # lectures.
        if(instance.type == CourseLectureType.VIDEO ):
            # r['video'] = {
            #     **{'url':  r['video'] if instance.video else ''},
            #     **CloudflareStream.signed_playback_url(instance.video_info),
            # }
            pass # get video info

        if(instance.type == CourseLectureType.ARTICLE ):
            r['article'] = {
                'data': r["article"],
                **instance.article_info
            }
        return r

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
        # Upload video to s3 and cdb77
        video_info = { }
        if video == None and uid:
            # stream.delete()
            pass
        elif video:
            pass
            # stream.metadata = {
            #     'name': f'Lecture#{instance.id} ({instance.title}) - {video.name}',
            #     'course_id': f'{instance.section.course.id}',
            #     'instructor_id': f'{instance.section.course.user.id}',
            #     'type': 'lecture'
            # }
            # video_info = stream.upload()
        instance.video_info = video_info
        instance.save()


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
        data = get_object_or_none(request.user.student_assignments.select_related('user', 'student_answers').prefetch_related('student_assignments').all(), assignment=instance.assignment)
        return StudentAssignmentSerializer(data,context=self.context).data if data else None


    def get_student_quiz(self,instance):
        request = self.context.get('request')
        if not request or not request.user.id or instance.type != self.Meta.model.QUIZ: return None
        data = get_object_or_none(request.user.student_quizzes.select_related('student_answers').all(), quiz=instance.quiz)
        return StudentQuizSerializer(data,context=self.context).data if data else None