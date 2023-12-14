from .serializers import SharePriceSerializer
from rest_framework import viewsets
from rest_framework.response import Response
from apps.shares.models import SharePrices
from rest_framework.permissions import IsAdminUser


class SharePricesView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = SharePriceSerializer
    queryset = SharePrices.objects.all()
    
