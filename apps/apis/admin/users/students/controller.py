from django.db.models import Avg, Count, Prefetch, Q, Sum
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from apps.apis.admin.paginations import CommonPagination
from .serializers import StudentSerializer, StudentProfileSerializer
from django_filters import rest_framework as filters
from apps.utils.filters import IOrderingFilter
from rest_framework.filters import SearchFilter
from apps.users.models import User
from django.db.models import Avg, Q, Sum, Case, Count, F,  When
import arrow

class StudentView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = StudentSerializer
    pagination_class = CommonPagination
    filter_backends = [IOrderingFilter,
                       SearchFilter, filters.DjangoFilterBackend]
    queryset = User.objects.filter(instructor__isnull=True)
    search_fields = ['id', 'user__first_name', 'user__last_name', 'email']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def students_count(self, request, *args, **kwargs):
        current_start, current_end = arrow.utcnow().span('month')
        last_start_days = arrow.now().shift(days=-6)
        last_start, last_end = arrow.now().shift(months=-1).span('month')
        context = dict()

        # total students increased from last month
        total_students = self.get_queryset().filter(Q(date_joined__date__gte=current_start.date()) &
                                                    Q(date_joined__date__lte=current_end.date())).count()

        last_month_students = self.get_queryset().filter(Q(date_joined__date__gte=last_start.date()) &
                                                         Q(date_joined__date__lte=last_end.date())).count()

        increased_student = total_students - last_month_students
        context['total_student_increase_from_last_month'] = round(
            (increased_student/total_students) * 100, 2) if increased_student > 0 else 0

        # active students increased from last month
        active_students = self.get_queryset().filter(Q(date_joined__date__gte=current_start.date()) &
                                                     Q(date_joined__date__lte=current_end.date()) & Q(is_active=True)).count()

        last_month_active_students = self.get_queryset().filter(Q(date_joined__date__gte=last_start.date()) &
                                                                Q(date_joined__date__lte=last_end.date())).count()

        increased_active_student = active_students - last_month_active_students
        context['active_student_increase_from_last_month'] = round(
            (increased_active_student/active_students) * 100, 2) if increased_active_student > 0 else 0

        # inactive students increased from last month
        inactive_students = total_students - active_students
        last_month_inactive_students = last_month_students - last_month_active_students
        increased_inactive_student = inactive_students - last_month_inactive_students
        context['inactive_student_increase_from_last_month'] = round(
            (increased_inactive_student/inactive_students) * 100, 2) if increased_inactive_student > 0 else 0

        context['data'] = self.get_queryset().aggregate(total_students=Count('id', distinct=True),
                                                        active_students=Count(
                                                            Case(When(is_active=True, instructor__isnull=True, then='id'),), distinct=True),
                                                        inactive_students=Count(
                                                            Case(When(is_active=False, instructor__isnull=True, then='id'),), distinct=True),
                                                        new_students=Count(Case(When(Q(date_joined__date__gte=last_start_days.date()) &
                                                                                     Q(date_joined__date__lte=current_start.date()) & Q(instructor__isnull=True), then='id'),), distinct=True))
        return Response(context)

    def profile(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = StudentProfileSerializer(instance)
        return Response(serializer.data)

    def update_profile(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = StudentProfileSerializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
