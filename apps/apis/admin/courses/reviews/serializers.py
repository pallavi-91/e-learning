from rest_framework import serializers
from apps.apis.marketfront.users.serializers import UserShortSerializer
from apps.courses.models import CourseReview


class CourseReviewSerializer(serializers.ModelSerializer):
    user = UserShortSerializer()
    class Meta:
        model = CourseReview
        fields = ['id', 'rate', 'user', 'course', 'content', 'date_updated', 'date_created']
        read_only_fields = ['course']
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['likes'] = instance.likes.select_related('likes').count()
        context['dislikes'] = instance.dislikes.select_related('dislikes').count()
        context['is_reported'] = instance.is_reported
        return context