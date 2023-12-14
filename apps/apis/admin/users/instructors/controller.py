from django.db.models import Avg, Count, Prefetch, Q, Sum
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from apps.apis.admin.paginations import CommonPagination
from .serializers import InstructorSerializer, InstructorProfileSerializer, NotificationSettingsSerializer, UserDetailSerializer
from django_filters import rest_framework as filters
from apps.utils.filters import IOrderingFilter
from rest_framework.filters import SearchFilter
from apps.users.models import User, Instructor, NotificationSettings
from django.db.models import Avg, Q, Sum, Case, Count, F,  When
import arrow
from django.shortcuts import get_object_or_404 
from rest_framework import status


class InstructorView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = InstructorSerializer
    pagination_class = CommonPagination
    filter_backends = [IOrderingFilter,
                       SearchFilter, filters.DjangoFilterBackend]
    queryset = Instructor.objects.prefetch_related('user')
    search_fields = ['id', 'user__first_name', 'user__last_name', 'user__email']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def instructors_count(self, request, *args, **kwargs):
        current_start, current_end = arrow.utcnow().span('month')
        last_start_days = arrow.now().shift(days=-6)
        last_start, last_end = arrow.now().shift(months=-1).span('month')
        context = dict()
        queryset = self.get_queryset().prefetch_related('user')

        statistics = queryset.aggregate(total_instructors = Count('user', distinct=True),
                                    active_instructors = Count(Case(When(user__is_active = True, then='id'),), distinct=True),
                                    inactive_instructors = Count(Case(When(user__is_active = False, then='id'),), distinct=True),
                                    new_instructors = Count(Case(When(Q(user__date_joined__date__gte=last_start_days.date()), then='id'),), distinct=True))
        context['data'] = statistics
        current_month_instructors = queryset.filter(Q(user__date_joined__date__gte=current_start.date()) & \
                                        Q(user__date_joined__date__lte=current_end.date()))
        last_month_instructors = queryset.filter(Q(user__date_joined__date__gte=last_start.date()) & \
                                        Q(user__date_joined__date__lte=last_end.date()))
        current_month_instructors_count = current_month_instructors.count()
        last_month_instructors_count = last_month_instructors.count()
        
		# total instructors increased from last month
        context['current_month_instructors'] = current_month_instructors_count
        context['last_month_instructors'] = last_month_instructors_count
        increased_instructor = current_month_instructors_count - last_month_instructors_count 
        context['total_instructor_increase_from_last_month'] = round((increased_instructor/last_month_instructors_count or 1) * 100, 2) if (last_month_instructors_count > 0 and increased_instructor > 0) else 0
        
        # active instructors increased from last month
        active_instructors = current_month_instructors.filter(Q(user__is_active = True)).count()
        last_month_active_instructors = last_month_instructors.filter(Q(user__is_active = True)).count()
        increased_active_instructor = active_instructors - last_month_active_instructors 
        context['active_instructors'] = active_instructors
        context['last_month_active_instructors'] = last_month_active_instructors
        context['active_instructor_increase_from_last_month'] = round((increased_active_instructor/last_month_active_instructors or 1) * 100, 2) if (last_month_active_instructors > 0 and increased_active_instructor > 0) else 0
        
        # inactive instructors increased from last month
        inactive_instructors = current_month_instructors.filter(Q(user__is_active = False)).count()
        last_month_inactive_instructors = last_month_instructors.filter(Q(user__is_active = False)).count()
        increased_inactive_instructor = inactive_instructors - last_month_inactive_instructors 
        context['inactive_instructors'] = inactive_instructors
        context['last_month_inactive_instructors'] = last_month_inactive_instructors
        context['inactive_instructor_increase_from_last_month'] = round((increased_inactive_instructor/last_month_inactive_instructors or 1) * 100, 2) if (last_month_inactive_instructors > 0 and increased_inactive_instructor > 0) else 0
        
        
        return Response(context)

    def profile(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = InstructorProfileSerializer(instance)
        return Response(serializer.data)

    def update_profile(self, request, *args, **kwargs):
        """Updated user profile details"""
        instance = get_object_or_404(User, **kwargs)
        serializer = UserDetailSerializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def update_instructor(self, request, *args, **kwargs):
        """Updated instructor profile basic details"""
        instance = get_object_or_404(Instructor, **kwargs)
        serializer = InstructorProfileSerializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def change_password(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = InstructorProfileSerializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def update_notifications(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = NotificationSettingsSerializer(
            instance.user.notification_settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user.courses.count() > 0:
            raise Exception('Instructor cannot be deleted')
        instance.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
