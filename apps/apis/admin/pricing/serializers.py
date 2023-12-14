from rest_framework import serializers,exceptions
from apps.apis.admin.countries.serializers import CountrySerializer
from apps.currency.format import FormatCurrency
from apps.currency.models import Currency
from apps.courses.models import CoursePrice
from django.conf import settings

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['id','name', 'currency_code',
                  'rate',
                  'is_primary_exchange_rate_currency',
                  'is_primary_store_currency',
                  'rounding_type',
                  'country',
                  'force',
                  'pricing_tier_status',
                  'published',]
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['symbol'] = instance.symbol
        return context
           
class PricingTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoursePrice
        fields = ['id','tier_level', 'name', 'price','currency','price_tier_status','date_updated']
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['currency'] = CurrencySerializer(instance=instance.currency, context = self.context).data
        return context
    

class PricingTierDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoursePrice
        fields = ['id','tier_level', 'name','price','currency','price_tier_status','date_updated']
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['currency'] = CurrencySerializer(instance=instance.currency, context = self.context).data
        context['currency_exchange'] = []
        currency_list = Currency.objects.exclude(id=instance.currency.id)
        formater = FormatCurrency(instance.currency.currency_code)
        for currency in currency_list:
            if not currency.rate:
                exchange_value = currency.exchange.convert(instance.price, instance.currency.currency_code, currency.currency_code)
            else:
                exchange_value = currency.rate*float(instance.price)
            exchange_value = round(exchange_value,2)
            currency_formater = FormatCurrency(currency.currency_code)
            
            context['currency_exchange'].append({
                "exchange_value": currency_formater.get_money_format(exchange_value),
                "amount": formater.get_money_format(instance.price),
                "other_currency": currency.name,
                "exchange_rate": round(exchange_value/float(instance.price),2)
            })
        return context
        
class CurrencyDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['id','name',
                  'currency_code',
                  'rate',
                  'is_primary_exchange_rate_currency',
                  'is_primary_store_currency',
                  'pricing_tier_status',
                  'rounding_type',
                  'published',
                  'force',
                  'pricing_tiers']
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['country_list'] = CountrySerializer(instance.country.all(), many=True).data
        context['pricing_tiers'] = PricingTierSerializer(instance.pricing_tiers.all(), many=True).data
        return context


class LiveRateCurrencySerializer(serializers.ModelSerializer):
    live_rate = serializers.SerializerMethodField()
        
    class Meta:
        model = Currency
        fields = ['id',
                  'name', 
                  'currency_code',
                  'rate',
                  'live_rate',
                  'country',
                  'pricing_tier_status',
                  'published']
    
    def get_live_rate(self, obj):
        try:
            primary_currency = settings.PRIMARY_CURRENCY_CODE
            exchange_value = obj.exchange.convert(1, obj.currency_code, primary_currency.get('exchange_rate_currency'))
            rate_value = round(exchange_value,3)
            return rate_value
        except Exception as ex:
            print(ex)
            return obj.rate