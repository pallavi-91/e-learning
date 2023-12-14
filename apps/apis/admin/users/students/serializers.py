from rest_framework import serializers
from apps.users.models import User
from django.db.models import Count, Q


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context.update(instance.courses.prefetch_related('classes').aggregate(enrolled_courses=Count('classes', filter=Q(classes__is_purchased=True), distinct=True)))
        return context

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
