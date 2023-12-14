import os
from django.conf.global_settings import LANGUAGES
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Count, Q

from rest_framework import serializers,exceptions
from rest_framework.serializers import ModelSerializer

from apps.apis.marketfront.users.serializers import UserShortSerializer
from apps.status import CourseLectureType
from apps.utils.cloudflare import CloudflareStream
from apps.utils.query import get_object_or_none

from apps.utils.validators import validate_file_extension, validate_file_size, video_ext
from apps.courses.models import (
    Assignment,
    AssignmentQuestion,
    LectureResource,
    Quiz,
    QuizAnswer,
    QuizQuestion,
    StudentAssignment,
    StudentAssignmentAnswer,
    StudentQuiz,
    StudentQuizAnswer,
    Section,
    Lecture,
    SubSection,
    SubsectionProgress,
)

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
    
class LectureDetailSerializer(ModelSerializer):
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
            'preview',
            'resources',
            'deleted_resources',
            'video_info',
        )

    def to_representation(self, instance):
        context = super().to_representation(instance)
        # add additional fields for video type
        # lectures.
        if(instance.type == CourseLectureType.VIDEO ):
            # Get video info
            # context['video_info'] = {
            #     **{'url':  context['video'] if instance.video else ''},
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
        
        # uid = instance.video_info.get('uid')
        # stream = CloudflareStream(video,video_id=uid)
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
        
class QuizAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswer
        read_only_fields = ['quiz_question'] 
        fields = '__all__'
    
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
            defaults={'position': self.validated_data.get('position'),
                      'watched_duration': self.validated_data.get('watched_duration')}
        )
        return progress

        
class StudentAssignmentSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    class Meta: 
        model = StudentAssignment
        read_only_fields = ['user','assignment']
        fields = '__all__'


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
    
    
class SubSectionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SubSection
        read_only_fields = ['section', 'preview']
        fields = '__all__'

    def to_representation(self, instance):
        context = super().to_representation(instance)
        request = self.context.get('request')
        context['preview'] = instance.preview
        
        if instance.type == self.Meta.model.QUIZ:
            context['quiz'] = QuizSerializer(instance.quiz, context=self.context).data
            if request.user.is_authenticated:
                student_quiz = request.user.student_quizzes.filter(quiz=instance.quiz)
                context['student_quiz'] = StudentQuizSerializer(student_quiz, many=True, context=self.context).data 
        
        if instance.type == self.Meta.model.ASSIGNMENT:
            context['assignment'] = AssignmentSerializer(instance.assignment, context=self.context).data
            if request.user.is_authenticated:
                student_assignments = request.user.student_assignments.filter(assignment=instance.assignment)
                context['student_assignment'] = StudentAssignmentSerializer(student_assignments, many=True, context=self.context).data 
        
        if instance.type == self.Meta.model.LECTURE:
            context['lecture'] = LectureSerializer(instance.lecture, context=self.context).data
            
        if request.user.is_authenticated:
            progress = get_object_or_none(instance.progress.select_related('user').all(), user=request.user)
            context['current_progress'] = SubsectionProgressSerializer(progress).data
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
        data["subsections"] = SubSectionSerializer(subsections, many=True, context=self.context).data
        return data

    def get_duration(self,instance):
        return instance.duration
    

class SectionSerializer(ModelSerializer):
    """ section serializer
    """
    duration = serializers.SerializerMethodField()
    class Meta:
        model = Section
        read_only_fields = ['subsections']
        fields = "__all__"

    def to_representation(self, instance):
        data= super(SectionSerializer,self).to_representation(instance)
        result = instance.subsections.aggregate(
            quiz_count=Count('id', filter=Q(type=SubSection.QUIZ)),
            assignment_count=Count('id', filter=Q(type=SubSection.ASSIGNMENT)),
            lecture_count=Count('id', filter=Q(type=SubSection.LECTURE)),
        )
        data.update(result)
        subsections = instance.subsections.select_related('assignment', 'quiz', 'lecture', 'section').prefetch_related('progress').all()
        data['subsections'] = SubSectionSerializer(subsections, many=True, context=self.context).data
        return data

    def get_duration(self,instance):
        return instance.duration

class ShortLectureSerializer(ModelSerializer):
    """ lecture serializer
    """
    class Meta:
        model = Lecture
        fields = (
            'id',
            'title',
        )

class SubsectionPositionSerializer(serializers.Serializer):
    position = serializers.IntegerField(required=True)
    subsection = serializers.PrimaryKeyRelatedField(queryset=SubSection.objects.prefetch_related('section', 'section__course').all())

    class Meta:
        model = SubSection

class PublicSectionSerializer(ModelSerializer):
    """ public section serializer
    """
    class Meta:
        model = Section
        fields = (
            'id',
            'title',
            'position',
            'duration',
        )

    def to_representation(self, instance):
        resp = super().to_representation(instance)
        resp['subsections'] = PublicSubsectionSerializer(
            instance.subsections.all(),
            many=True,
        ).data

        return resp


class PublicSubsectionSerializer(ModelSerializer):
    """ public subsection serializer
    """
    title = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    preview = serializers.SerializerMethodField()

    class Meta:
        model = SubSection
        fields = (
            'id',
            'title',
            'duration',
            'type',
            'preview',
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
    
    def get_preview(self, instance):
        return instance.preview