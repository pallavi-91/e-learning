from django.db.models import Avg, Case, Count, F, Sum, When, FloatField, Value, Q, Max
from django.db.models.functions import Coalesce, Round
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from apps.courses.models.courses import Course
from apps.courses.models.lectures import LectureResource
from .serializers import ( InstructorSectionSerializer, 
                          LectureResourceSerializer, 
                          LectureSerializer, 
                          AssignmentSerializer,  
                          QuizQuestionSerializer, 
                          QuizSerializer, 
                          SectionListSerializer, 
                          SubSectionSerializer, 
                          AssignmentQuestionSerializer, 
                          QuizQuestionSerializer , )

from rest_framework import viewsets
from apps.status import CourseStatus
from apps.courses.models import Section, Lecture, SubSection, Assignment, Quiz, QuizQuestion, AssignmentQuestion
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

class InstructorSectionView(viewsets.ModelViewSet):
    serializer_class = InstructorSectionSerializer
    queryset = Section.objects.select_related('course')

    def get_queryset(self):
        return super().get_queryset().filter(**self.kwargs)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SectionListSerializer(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)

        serializer = SectionListSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        course = get_object_or_404(Course, id=kwargs.get('course_id'))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        instance = get_object_or_404(Section, id=kwargs.get('pk'))
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def list_subsections(self, request, **kwargs):
        instance = get_object_or_404(Section, id=kwargs.get('pk'))
        subsections = instance.subsections.select_related('assignment', 'quiz', 'lecture', 'section').all()
        serializer = SubSectionSerializer(subsections, many=True, context=self.get_serializer_context())
        return Response(serializer.data)


class LectureView(viewsets.ModelViewSet):
    serializer_class = LectureSerializer
    queryset = Lecture.objects.select_related('section').prefetch_related('resources', 'section__course')
    # parser_classes = [JSONParser, FormParser, MultiPartParser]
    
    def get_queryset(self):
        return super().get_queryset().filter(section__course_id=self.kwargs.get('course_id'))

    def perform_create(self, serializer):
        section = get_object_or_404(Section, id=self.kwargs.get('section'))
        instance = serializer.save(section=section)
        SubSection.objects.get_or_create(type=SubSection.LECTURE,lecture=instance, section=section)
        return instance

    def update(self, request, **kwargs):
        lecture = get_object_or_404(Lecture, id=kwargs.get('pk'))
        serializer = self.get_serializer(
            instance=lecture,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)
    

class LectureResourcesView(viewsets.ModelViewSet):
    serializer_class = LectureResourceSerializer
    queryset = LectureResource.objects.select_related('lecture')
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_queryset(self):
        return super().get_queryset().filter(lecture_id=self.kwargs.get('lecture'))

    def perform_create(self, serializer):
        lecture = get_object_or_404(Lecture, id=self.kwargs.get('lecture'))
        serializer.save(lecture=lecture)


class AssignmentView(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    queryset = Assignment.objects.all()

    def create(self, request, *args, **kwargs):
        section = Section.objects.get(id=kwargs.get('section'))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save(section=section)
        subs = SubSection.objects.create(type=SubSection.ASSIGNMENT,assignment=assignment,section=section
        )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        section = Section.objects.get(id=kwargs.get('section'))
        instance = Assignment.objects.get(id=kwargs.get('pk'))
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(section=section)
        return Response(serializer.data)
    
    def delete(self, request, **kwargs):
        section = Section.objects.get(id = kwargs.get('section'))
        section.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AssignmentQuestionsView(viewsets.ModelViewSet):
    serializer_class = AssignmentQuestionSerializer
    queryset = AssignmentQuestion.objects.select_related('assignment')
    

    def get_queryset(self):
        return super().get_queryset().filter(assignment_id=self.kwargs.get('assignment'))

    def perform_create(self, serializer):
        assignment = get_object_or_404(Assignment, id=self.kwargs.get('assignment'))
        serializer.save(assignment=assignment)
        
class QuizView(viewsets.ModelViewSet):
    
    serializer_class = QuizSerializer
    queryset = Quiz.objects.all()

    def create(self, request, **kwargs):
        section = Section.objects.get(id=kwargs.get('section'))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quiz = serializer.save(section=section)
        SubSection.objects.create(type=SubSection.QUIZ,quiz=quiz,section=section)
        serializer.save(section=section) # Add to subsection
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def create_question(self, request, **kwargs):
        serializer = QuizQuestionSerializer(context=self.get_serializer_context(),data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(quiz_id=kwargs.get('quiz'))
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update_question(self, request, **kwargs):
        question = QuizQuestion.objects.get(id = kwargs.get('question'))
        serializer = QuizQuestionSerializer(
            instance=question,
            data=request.data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class QuizQuestionsView(viewsets.ModelViewSet):
    serializer_class = QuizQuestionSerializer
    queryset = QuizQuestion.objects.select_related('quiz')

    def get_queryset(self):
        return super().get_queryset().filter(quiz_id=self.kwargs.get('quiz'))

    def perform_create(self, serializer):
        quiz = get_object_or_404(Quiz, id=self.kwargs.get('quiz'))
        serializer.save(quiz=quiz)