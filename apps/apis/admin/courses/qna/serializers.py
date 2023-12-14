from rest_framework import serializers
from apps.apis.marketfront.users.serializers import UserShortSerializer
from apps.courses.models import QnA, QnAReplys

class CourseQnAReplysSerializer(serializers.ModelSerializer):
    user = UserShortSerializer()
    class Meta:
        model = QnAReplys
        fields = ['id', 'user', 'comment', 'date_updated', 'date_created']

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['upvoted'] = instance.upvoted_users.select_related('upvoted_qna_reply').count()
        return context
    

class CourseQnASerializer(serializers.ModelSerializer):
    user = UserShortSerializer()
    class Meta:
        model = QnA
        fields = ['id', 'title', 'user', 'user_class', 'description', 'approved', 'date_updated', 'date_created']
        read_only_fields = ['user_class']
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['upvoted'] = instance.upvoted_users.select_related('upvoted_qna').count()
        context['reply'] = CourseQnAReplysSerializer(instance.qnas.select_related('user').all(), many=True).data
        return context