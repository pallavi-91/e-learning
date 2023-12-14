from rest_framework import serializers
from apps.courses.models import Assignment, AssignmentQuestion
from apps.apis.marketfront.courses.serializers import CourseCategorySerializer, CourseSubCategorySerializer

class AssignmentQuestionSerializer(serializers.ModelSerializer):
        model = AssignmentQuestion
        read_only_fields = ['assignment']
        fields = '__all__'

    
class AssignmentSerializer(serializers.ModelSerializer):
    questions = AssignmentQuestionSerializer(many=True,required=False)
    class Meta:
        model = Course
        fields = ['id','title']  
        read_only_fields = ['section','questions'] 

    def to_representation(self, instance):
        context = super().to_representation(instance)
        return context