from rest_framework import serializers
from django.db.models import Count, Q

from apps.shares.models import InstructorGroup


class InstructorGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorGroup
        fields = '__all__'

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context.update({'total_users': instance.group_instructor.count()})
        return context

class GroupDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorGroup
        fields = '__all__'
