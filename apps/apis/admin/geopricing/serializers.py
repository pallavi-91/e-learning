from rest_framework import serializers
from apps.courses.models import CoursePrice
from apps.geopricing.models import GeoLocations, GeoPricing, GeoPricingTiers
from apps.apis.admin.pricing.serializers import CurrencySerializer

class CoursePriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoursePrice
        fields = '__all__'
        
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['currency'] = CurrencySerializer(instance.currency).data
        return context

class GeoPricingTiersSerializer(serializers.ModelSerializer):
    geo_tier_amount = serializers.SerializerMethodField()
    id = serializers.PrimaryKeyRelatedField(allow_null=True,required=False,queryset=GeoPricingTiers.objects.all())
    
    class Meta:
        model = GeoPricingTiers
        fields = ('id','percentage','geo_tier_amount')
        
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['pricing_tiers'] = CoursePriceSerializer(instance.pricing_tier).data
        return context
        
    def get_geo_tier_amount(self, instance):
        geo_tier_amount = instance.pricing_tier.price*(instance.percentage/100)
        geo_tier_amount = instance.pricing_tier.price + geo_tier_amount
        return geo_tier_amount

class GeoPricingSerializer(serializers.ModelSerializer):
    geo_pricing_tier = GeoPricingTiersSerializer(many= True)
    class Meta:
        model = GeoPricing
        fields = '__all__'
        
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['geopricing_tiers'] = GeoPricingTiersSerializer(instance.geo_pricing_tier, many=True).data
        return context
    
    def update(self,instance, validated_data):
        geo_pricing_tier = validated_data.pop('geo_pricing_tier')
        res = super(GeoPricingSerializer,self).update(instance,validated_data)
        for pricing_tier in geo_pricing_tier:
            obj = pricing_tier.get('id')
            obj.percentage = pricing_tier.get('percentage')
            obj.save()
        return res
    
class GeoLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoLocations
        fields = '__all__'
        
    def validate(self, data):
        geolocation = GeoLocations.objects.filter(country = data['country'], currency = data['currency'])
        if geolocation.exists():
            raise serializers.ValidationError("This geolocation is already exists")
        return data
    
           
