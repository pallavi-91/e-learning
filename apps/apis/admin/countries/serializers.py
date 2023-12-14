from rest_framework import serializers
from apps.courses.models import CoursePrice
from apps.countries.models import Country

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'
           
