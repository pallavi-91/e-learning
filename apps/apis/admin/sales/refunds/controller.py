from email.policy import default
import pdb

from django.shortcuts import get_object_or_404

from apps.status import RefundType
from .serializers import RefundRequestDetailSerializer, RefundRequestSerializer
from apps.transactions.models import RefundRequest, RefundStatus, Transactions, TransactionTypes
from apps.users.models import Order
from django.db.models.functions import Coalesce
from django.db.models import Count, F, Case, When, IntegerField, Value, Avg, DurationField, ExpressionWrapper
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
import base64, time
    
class RefundRequestView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = RefundRequestSerializer
    queryset = RefundRequest.objects.select_related('user','transaction', 'transaction__user_class', 'transaction__payment_type', 'transaction__user_class__course').all()
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()       
        serializer = RefundRequestDetailSerializer(instance = instance)
        return Response(serializer.data)
    
    def case_volume_by_status(self, request, *args, **kwargs):
        context = RefundRequest.objects.values('id', 'status').aggregate(
            total_requests=Count('id'),
            total_pending=Count(
                                Case(
                                        When(status=RefundStatus.REFUND_PENDING, then='id'),
                                    ),
                                ),
            total_approved=Count(
                                Case(
                                        When(status=RefundStatus.REFUND_APPROVED, then='id'),
                                    ),
                                ), 
            total_rejected=Count(
                                Case(
                                        When(status=RefundStatus.REFUND_REJECTED, then='id'),
                                    ),
                                ), 
            total_cancelled=Count(
                                Case(
                                        When(status=RefundStatus.REFUND_CANCELED, then='id'),
                                    ),
                                ),
            total_chargeback=Count(
                                Case(
                                        When(status=RefundStatus.REFUND_CHARGEBACK, then='id'),
                                    ),
                                ),
            avg_resolve_time=Avg(
                    F('date_updated') - F('date_created'),
                    output_field=DurationField()
                )
            )
        
        if context.get('avg_resolve_time', False):
            context['avg_resolve_time'] = time.strftime('%H:%M:%S', time.gmtime(context.get('avg_resolve_time').total_seconds()))
        else:
            context['avg_resolve_time'] = '00:00:00'
        return Response(context)
    
    def approve_refund(self, request, *args, **kwargs):
        instance = self.get_object()
        force_key = request.query_params.get('force')
        instance_id = None
        if force_key:
            try:
                instance_id = int(base64.b64decode(force_key).decode('utf-8').split('-')[0])
            except:
                pass
        if instance.transaction.can_refund or instance_id == instance.id:
            instance.reason = request.query_params.get('reason', '')
            instance.approve()
            serializer = RefundRequestDetailSerializer(instance = instance)
            return Response(serializer.data)
        raise ValidationError(detail={"detail":"Can not refund"})
    
    def reject_refund(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.reason = request.query_params.get('reason', '')
        instance.reject()
        serializer = RefundRequestDetailSerializer(instance = instance)
        return Response(serializer.data)  
    
    
    def thkee_issue_refund(self, request, *args, **kwargs):
        is_many = isinstance(request.data.get('data'), list)
        serializer = RefundRequestSerializer(data=request.data.get('data'), many=is_many)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    
    def thkee_issue_refund_cancel(self, request, *args, **kwargs):
        transaction = get_object_or_404(Transactions, **kwargs)
        rr = transaction.refund_requests.filter(status=RefundStatus.REFUND_PENDING, refund_type=RefundType.THKEE)
        rr.update(status=RefundStatus.REFUND_CANCELED)
        return Response({})