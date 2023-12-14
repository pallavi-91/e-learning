from apps.apis.admin.paginations import CommonPagination
from .serializers import LiveRateCurrencySerializer, PricingTierDetailSerializer, PricingTierSerializer, CurrencyDetailSerializer, CurrencySerializer
from rest_framework import viewsets
from apps.currency.models import Currency, currency_list
from apps.courses.models import CoursePrice
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from .filters import CurrencyFilter, PriceTierFilter, PriceTierSearchFilter, OrderingFilter, SearchFilter
from apps.currency.format import FormatCurrency
from rest_framework.permissions import IsAdminUser
from django.conf import settings
from rest_framework import status

class CurrencyView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all()
    # pagination_class = CommonPagination
    filter_backends = [OrderingFilter,SearchFilter,filters.DjangoFilterBackend]
    filterset_class  = CurrencyFilter
    filterset_fields = ['is_primary_exchange_rate_currency', 'is_primary_store_currency','pricing_tier_status', 'rate']
    ordering_fields = ['name','date_updated']
    search_fields = ['id', 'name', 'currency_code',]
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        # do your customization here
        instance = self.get_object()       
        serializer = CurrencyDetailSerializer(instance = instance)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.can_delete():
            raise Exception('Currency is linked with other resources.')
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def currency_code(self, request, *args, **kwargs):
        # do your customization here
        data = [{'currency_code': code, 'name': name} for code, name in currency_list]
        return Response(data)
    
    def currency_exchange(self, request, *args, **kwargs):
        pricing_tiers = CoursePrice.objects.all()
        instance = self.get_object() 
        data = list()
        formater = FormatCurrency(instance.currency_code)

        for pricing_tier in pricing_tiers:
            if instance.rate:
                # Use manual rate
                exchange_value = instance.rate*float(pricing_tier.price)
            else:
                # Use online rate
                exchange_value = instance.exchange.convert(pricing_tier.price, pricing_tier.currency.currency_code, instance.currency_code)
            
            exchange_value = round(exchange_value,2)
            currency_formater = FormatCurrency(pricing_tier.currency.currency_code)
            
            data.append({
                "id": pricing_tier.id ,
                "name": pricing_tier.name,
                "tier_level": pricing_tier.tier_level,
                "exchange_value": formater.get_money_with_currency_format(exchange_value),
                "amount": currency_formater.get_money_format(pricing_tier.price),
                "pricing_tier_status": pricing_tier.price_tier_status
            })
        
        return Response(data)
    
    def get_live_rates(self, request, *args, **kwargs):
        all_currency = Currency.objects.all()
        serializers = LiveRateCurrencySerializer(all_currency, many=True).data
        return Response(serializers)
    
class PricingTierView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = PricingTierSerializer
    # pagination_class = CommonPagination
    queryset = CoursePrice.objects.select_related('currency').all()
    filter_backends = [OrderingFilter,PriceTierSearchFilter,filters.DjangoFilterBackend]
    filterset_fields = ['price','price_tier_status', 'currency']
    filterset_class  = PriceTierFilter
    ordering_fields = ['name','date_updated']
    search_fields = ['id','name']
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()       
        serializer = PricingTierDetailSerializer (instance = instance)
        return Response(serializer.data)
    
    def primary_currency(self, request, *args, **kwargs):
        context= settings.PRIMARY_CURRENCY_CODE
        return Response(context)
    