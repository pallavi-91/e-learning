from rest_framework import serializers
from apps.courses.models import Course, Topic, CoursePrice
from apps.courses.models.change_history import CourseChangeHistory
from apps.currency.models import Currency
from apps.apis.marketfront.courses.serializers import CourseCategorySerializer, CourseSubCategorySerializer

class InstructorCourseSerializer(serializers.ModelSerializer):
    statistics = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields = ['id','title','code','image','pricing','currency','status','statistics']   

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['category'] = CourseCategorySerializer(instance.category).data
        context['subcategory'] = CourseSubCategorySerializer(instance.subcategory).data
        return context
    
    def get_statistics(self,instance):
        favorites = instance.favorites.count()
        purchased = instance.classes.filter(is_purchased = True).count()
        statistics = {"favorites":favorites, "purchased":purchased}
        return statistics

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = [
            'name',
            'id',
        ]  

class InstructorCourseDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Course
        fields = [
            'slug',
            'id',
            'code',
            'user',
            'title',
            'subtitle',
            'description',
            'pricing',
            'currency',
            'image',
            'desc',
            'promo_video',
            'skill_level',
            'video_info',
            'type',
            'language',
            'category',
            'subcategory',
            'topics',
            'status',
            'included_in_promo',
        ]
        read_only_fields = ['user']
    
    def to_representation(self, instance):
        context =  super().to_representation(instance)
        context['topics'] = TopicSerializer(instance.topics.all(),many=True).data
        context['valid_for_review'] = instance.is_valid_for_review
        return context
    
    
    def update(self, instance, validated_data):
        topics_data = validated_data.pop('topics', None)
        instance.topics.clear()
        if topics_data:
            instance.topics.set([topic for topic in topics_data])
        return super().update(instance, validated_data)

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['id','name', 
                  'currency_code',
                  'country',
                  'pricing_tier_status',
                  'published']
        
class PricingTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoursePrice
        fields = ['id','tier_level', 'name', 'price','currency','price_tier_status','date_updated']
    

class CourseChangeHistorySerializer(serializers.ModelSerializer):
    """Course feedback history"""
    class Meta:
        model = CourseChangeHistory
        fields = '__all__'
        read_only_fields = ['course', 'user']