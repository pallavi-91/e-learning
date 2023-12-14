from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from rest_framework.response import Response
from rest_framework import exceptions
from rest_framework.filters import OrderingFilter,SearchFilter
from rest_framework.viewsets import GenericViewSet
from apps.courses.paginations import StudentAssignmentPagination, QuizPagination, AssignmentPagination
from rest_framework import status
from apps.utils.query import SerializerProperty
from apps.utils.paginations import CursorViewSetPagination, ViewSetPagination
from django.db import transaction
from apps.courses.models import SubSection
from .serializers import (
    AssignmentSerializer,
    QuizQuestionSerializer,
    QuizSerializer,
    SectionSerializer,
    StudentAssignmentDetailSerializer,
    StudentAssignmentSerializer,
    StudentQuizSerializer,
    SubSectionSerializer,
)

class StudentAssignmentView(SerializerProperty, ViewSetPagination, GenericViewSet):
    
    serializer_class = StudentAssignmentSerializer
    pagination_class = StudentAssignmentPagination

    def list(self,request,**kwargs):
        """ get the student answers by assignment id """
        qs = self.filter_queryset(self._model.objects.filter(**kwargs)) 
        serializer = self.get_serializer(qs.last())
        return Response(serializer.data)

    def get(self,request, **kwargs):
        student_assignment = get_object_or_404(self._model,**kwargs)
        serializer = StudentAssignmentDetailSerializer(student_assignment,context=self.get_serializer_context())
        return Response(serializer.data)

    def answer(self,request, **kwargs):
        subsection = get_object_or_404(SubSectionSerializer.Meta.model, **kwargs)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(assignment=subsection.assignment,user=request.user)
     
        return Response(serializer.data)
        
    def update_answer(self,request, **kwargs):
        student_assignment = get_object_or_404(self._model, **kwargs)
        serializer = self.get_serializer(student_assignment,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(assignment=student_assignment.assignment, user=request.user)
        return Response(serializer.data)

    def retry(self,request, **kwargs):
        student_assignment = get_object_or_404(self._model, **kwargs)
        student_assignment.delete()
        return Response()
    
    
class AssignmentView(SerializerProperty, ViewSetPagination, GenericViewSet):
    
    serializer_class = AssignmentSerializer
    pagination_class = AssignmentPagination
    filter_backends = [OrderingFilter,SearchFilter]
    search_fields = ['title']

    def get(self,request,**kwargs):
        object = get_object_or_404(self._model,**kwargs)
        return Response(self.get_serializer(object).data)  

    def get_assignments(self,request,**kwargs):
        """ get the course reviews by course id on view course """
        code = kwargs.get('code') 
        qs = self.filter_queryset(
                self._model.objects.filter(
                    section__course__code=code,
                    section__course__user=request.user,
                )) 
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page,many=True)
        return self.get_paginated_response(serializer.data)


    def create(self,request,**kwargs):
        section = get_object_or_404(
            SectionSerializer.Meta.model,
            course__user=request.user,
            **kwargs
        )
        
        if not section.course.is_editable:
            raise exceptions.PermissionDenied()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(section=section)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    def update(self,request,**kwargs):
        quiz = get_object_or_404(
            self._model,
            section__course__user=request.user,
            **kwargs
        )
        if not quiz.section.course.is_editable:
            raise exceptions.PermissionDenied()

        serializer = self.get_serializer(quiz,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class StudentQuizView(SerializerProperty, GenericViewSet):
    
    serializer_class = StudentQuizSerializer

    def answer(self,request, **kwargs):
        subsection = get_object_or_404(SubSectionSerializer.Meta.model, **kwargs)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(quiz=subsection.quiz,user=request.user)
        return Response(serializer.data)

    def delete_answer(self,request, **kwargs):
        student_assignment = get_object_or_404(request.user.student_quizzes, **kwargs)
        student_assignment.delete()
        return Response()


class QuizView(SerializerProperty, CursorViewSetPagination, GenericViewSet):
    
    serializer_class = QuizSerializer
    pagination_class = QuizPagination

    def create_question(self,request,**kwargs):
        serializer = QuizQuestionSerializer(
            context=self.get_serializer_context(),
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(quiz_id=kwargs.get('quiz_id'))
        return Response(serializer.data,status=status.HTTP_201_CREATED)

    def update_question(self,request,**kwargs):
        question = get_object_or_404(
            QuizQuestionSerializer.Meta.model,
            quiz__section__course__user=request.user,
            **kwargs
        )
        serializer = QuizQuestionSerializer(
            instance=question,
            data=request.data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def delete(self,request,**kwargs):
        question = get_object_or_404(
            QuizQuestionSerializer.Meta.model,
            quiz__section__course__user=request.user,
            **kwargs
        )
        if not question.quiz.section.course.is_editable:
            raise exceptions.PermissionDenied()

        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @transaction.atomic
    def update_quiz(self,request,**kwargs):
        subsection = get_object_or_404(self._model,section__course__user=request.user, **kwargs)

        if not subsection.section.course.is_editable:
            raise exceptions.PermissionDenied()

        serializer = QuizSerializer( 
            subsection.quiz,
            context=self.get_serializer_context(),
            data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
    def create_quiz(self,request,**kwargs):
        section = get_object_or_404(
            SectionSerializer.Meta.model,
            course__user=request.user, 
            **kwargs)

        if not section.course.is_editable:
            raise exceptions.PermissionDenied()

        serializer = QuizSerializer( 
            context=self.get_serializer_context(),
            data=request.data)
        serializer.is_valid(raise_exception=True)
        quiz = serializer.save(section=section)
        subs = SubSection.objects.create(
            type=SubSection.QUIZ,
            quiz=quiz,
            section=section
        )
        return Response(self.get_serializer(subs).data, status=status.HTTP_201_CREATED)
    
    @transaction.atomic
    def create_assignment(self,request,**kwargs):
        section = get_object_or_404(
            SectionSerializer.Meta.model,
            course__user=request.user, 
            **kwargs)

        if not section.course.is_editable:
            raise exceptions.PermissionDenied()

        serializer = AssignmentSerializer( 
            context=self.get_serializer_context(),
            data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save(section=section)
        subs = SubSection.objects.create(
            type=SubSection.ASSIGNMENT,
            assignment=assignment,
            section=section
        )
        return Response(self.get_serializer(subs).data, status=status.HTTP_201_CREATED)


    @transaction.atomic
    def update_assignment(self,request,**kwargs):
        subsection = get_object_or_404(self._model,section__course__user=request.user, **kwargs)

        if not subsection.section.course.is_editable:
            raise exceptions.PermissionDenied()

        serializer = AssignmentSerializer( 
            subsection.assignment,
            context=self.get_serializer_context(),
            data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self.get_serializer(subsection).data)