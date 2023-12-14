from rest_framework import serializers
from apps.users.models import User, Instructor, NotificationSettings
from django.db.models import Count, Q
from apps.status import CourseStatus


class InstructorUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instructor
        fields = ['id', 'payout_pay_active']

    def to_representation(self, instance):
        from apps.apis.admin.sales.transactions.serializers import PaymentTypeSerializer
        context = super().to_representation(instance)
        context['payout_method'] = PaymentTypeSerializer(
            instance.payout_method).data
        return context


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name',
                  'email', 'is_active', 'is_superuser']

    def to_representation(self, instance):
        context = super().to_representation(instance)
        if hasattr(instance, 'instructor'):
            instructor = InstructorUserProfileSerializer(
                instance.instructor).data
            context.update(instructor)
        return context


class UserDetailProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email',
                  'is_active',  'date_joined', 'language']

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['courses'] = instance.courses.count()
        context.update(instance.courses.prefetch_related('classes').aggregate(
            students=Count('classes__user', filter=Q(classes__is_purchased=True), distinct=True)))
        if hasattr(instance, 'instructor'):
            instructor = InstructorUserProfileSerializer(
                instance.instructor).data
            context.update(instructor)
        return context


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'fullname',
                  'email', 'is_active',  'photo', 'date_joined', 'bio',
                  'profile_completion', 'inactive_reason', 'language',
                  'overall_ratings', 'headline',]
        read_only_fields = ['overall_ratings', 'profile_completion']


class InstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instructor
        fields = ['id', 'group_name','profile_completion', 'date_updated', 'date_created']

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['user'] = UserDetailSerializer(instance.user).data
        context['course_published'] = instance.user.courses.filter(
            status=CourseStatus.STATUS_PUBLISHED).count()
        context['course_draft'] = instance.user.courses.filter(
            status=CourseStatus.STATUS_DRAFT).count()
        return context


class InstructorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instructor
        fields = ['id', 'group_name', 'payout_pay_active', 'public_profile','public_courses']

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['user'] = UserDetailSerializer(instance.user).data
        return context

class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = ['id', 'course_recommendations', 'annoucements', 'promotional_emails']

