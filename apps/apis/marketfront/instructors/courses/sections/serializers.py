from rest_framework import serializers,exceptions
from apps.apis.marketfront.sections.serializers import StudentAssignmentSerializer, SubsectionProgressSerializer
from apps.courses.models import Section, Lecture, LectureResource, AssignmentQuestion, Assignment, Quiz, QuizAnswer, QuizQuestion
from apps.courses.models.sections import SubSection
from apps.status import CourseLectureType
from django.db.models import Count, Q
from apps.utils.validators import validate_file_extension, validate_file_size, video_ext
from apps.utils.query import get_object_or_none
import os

class InstructorSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        read_only_fields = ['course']
        fields = (
            'id',
            'title',
            'position',
            'course'
        )

class SubSectionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SubSection
        read_only_fields = ['section', 'preview']
        fields = '__all__'

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['preview'] = instance.preview
        
        if instance.type == self.Meta.model.QUIZ:
            context['quiz'] = QuizSerializer(instance.quiz, context=self.context).data
        
        if instance.type == self.Meta.model.ASSIGNMENT:
            context['assignment'] = AssignmentSerializer(instance.assignment, context=self.context).data

        if instance.type == self.Meta.model.LECTURE:
            context['lecture'] = LectureSerializer(instance.lecture, context=self.context).data
        context['duration'] = instance.duration
        return context
    
class SectionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        read_only_fields = ['subsections']
        fields = "__all__"

    def to_representation(self, instance):
        context = super(SectionListSerializer,self).to_representation(instance)
        result = instance.subsections.aggregate(
            quiz_count=Count('id', filter=Q(type=SubSection.QUIZ)),
            assignment_count=Count('id', filter=Q(type=SubSection.ASSIGNMENT)),
            article_count=Count('id', filter=Q(type=SubSection.LECTURE) & Q(lecture__type=CourseLectureType.ARTICLE)),
            video_count=Count('id', filter=Q(type=SubSection.LECTURE) & Q(lecture__type=CourseLectureType.VIDEO)),
        )
        context.update(result)
        return context

class LectureResourceSerializer(serializers.ModelSerializer):
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
        path_, name = os.path.split(instance.file.name)
        return name    

class LectureSerializer(serializers.ModelSerializer):
    """ lecture serializer
    """
    video = serializers.FileField(validators=[validate_file_extension(video_ext), 
                                              validate_file_size(1000 * 1024 * 1024)], # 1gb
                                              required=False, 
                                              allow_null=True, 
                                              allow_empty_file=True)
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
            'video_info',
            'deleted_resources',
        )

    def to_representation(self, instance):
        context = super().to_representation(instance)
        if instance.type == CourseLectureType.ARTICLE:
            context['article'] = {
                'data': context["article"],
                **instance.article_info
            }
        return context
    

    def create(self, validated_data):
        resources = validated_data.pop("resources",[])
        instance = super(LectureSerializer,self).create(validated_data)
        # Save resources
        if resources:
            serializer = LectureResourceSerializer(data=resources, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(lecture=instance)
        return instance
    
    def update(self, instance, validated_data,**kwargs):
        resources = validated_data.pop("resources",[])
        deleted_resources = validated_data.pop("deleted_resources",[])
        instance = super(LectureSerializer,self).update(instance, validated_data)
        for deleted in deleted_resources:
            deleted.delete()
        # Save resources
        if resources:
            serializer = LectureResourceSerializer(data=resources, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(lecture=instance)
        return instance
    

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
    class Meta:
        model = Assignment
        read_only_fields = ['section','questions']
        fields = '__all__'
        
    def update(self, instance, validated_data):
        questions = validated_data.pop('questions')
        data = super().update(instance, validated_data)
        for question in questions:
            serializer =AssignmentQuestionSerializer(instance=question.pop('id',None),data=question)
            serializer.is_valid(raise_exception=True)
            serializer.save(assignment=data)
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

    class Meta:
        model = QuizQuestion
        read_only_fields = ['quiz'] 
        fields = '__all__'
    
    def create(self, validated_data,**kwargs):
        answers = validated_data.pop('answers',[])
        instance = super().create(validated_data,**kwargs)
        serializer = QuizAnswerSerializer(many=True,data=answers)
        serializer.is_valid(raise_exception=True)
        serializer.save(quiz_question=instance)
        return instance

    
    def update(self,instance, validated_data):
        answers = validated_data.pop('answers',[])
        data = super().update(instance,validated_data)
        existing_id = [item.get('id').id for item in answers if item.get('id', None)]
        instance.answers.exclude(id__in=existing_id).delete()# Delete answers that are not in request
        for ans in answers:
            instance = ans.pop('id',None)
            if instance:
                serializer = QuizAnswerSerializer(instance=instance, data=ans)
            else:
                serializer = QuizAnswerSerializer(data=ans)
            serializer.is_valid(raise_exception=True)
            serializer.save(quiz_question=data)
        return data
    
class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True,required=False)
    class Meta:
        model = Quiz
        read_only_fields = ['section'] 
        fields = '__all__'