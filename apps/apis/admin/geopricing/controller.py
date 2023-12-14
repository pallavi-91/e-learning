from apps.apis.admin.paginations import CommonPagination
from .serializers import GeoLocationSerializer, GeoPricingTiersSerializer, GeoPricingSerializer
from rest_framework import viewsets
from apps.geopricing.models import GeoLocations, GeoPricing, GeoPricingTiers
from apps.courses.models import CoursePrice
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.shortcuts import get_object_or_404
from apps.geopricing.tasks import create_geo_pricing


class GeoLocationView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = GeoLocationSerializer
    queryset = GeoLocations.objects.all()
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        create_geo_pricing(instance.id)
        return Response(serializer.data, status=201)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset().filter(is_deleted=False))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, **kwargs):
        instance = get_object_or_404(GeoLocations, is_deleted=False)
        instance.is_deleted = True
        instance.save()
        return Response()
    
    def geo_pricing_tiers(self, request, **kwargs):
        instance = self.get_object()
        tiers = GeoPricingTiers.objects.filter(geo_pricing = instance.geo_pricing)
        serializer = GeoPricingTiersSerializer(tiers, many=True)
        return Response(serializer.data)
    
    def update_geopricing(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = GeoPricingSerializer(instance.geo_pricing, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
