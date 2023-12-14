from multiprocessing import context
import pdb
from rest_framework.permissions import IsAdminUser
from rest_framework import  viewsets
from apps.apis.admin.sales.statements.serializers import StatementTransactionSerializer
from apps.statements.models import Statement, StatementTransactions
from apps.status import OrderStatus
from .filters import OrderingFilter, InstructorSearchFilter, filters
from .serializers import InstructorSerializer, InstructorStatementSerializer
from apps.users.models import Order, User
from apps.courses.models import CourseReview
from apps.transactions.models import Transactions, TransactionTypes
from rest_framework.response import Response
from django.db.models import Avg, Q, Sum, Count
import arrow, math
from itertools import chain

class InstructorView(viewsets.ModelViewSet):
	permission_classes = [IsAdminUser]
	serializer_class = InstructorSerializer
	filter_backends = [InstructorSearchFilter,filters.DjangoFilterBackend]
	search_fields = ['id',]
	queryset = User.objects.select_related('instructor').prefetch_related('instructor_transactions').exclude(instructor=None)
			
	def count_by_date(self, request, *args, **kwargs):
		current_start, current_end = arrow.utcnow().span('month')
		last_start, last_end = arrow.now().shift(months=-1).span('month')

		startDate = request.GET.get('from')
		endDate = request.GET.get('to')
		if not startDate or not endDate:
			startDate = current_start
			endDate = current_end
		else:
			startDate = arrow.get(startDate)
			endDate = arrow.get(endDate)
			last_start, last_end = startDate.shift(months=-1).span('month')
		# Make query to get count of instructors
		context = dict()
		context['total_instructors'] = self.get_queryset()\
		.filter(Q(date_joined__date__gte=startDate.date()) & Q(date_joined__date__lte=endDate.date())).count()
  
		context['last_month_instructors'] = self.get_queryset()\
		.filter(Q(date_joined__date__gte=last_start.date()) & Q(date_joined__date__lte=last_end.date())).count()
		
		# Make query to get count of Orders
		context['total_orders'] = Order.objects.select_related('user')\
		.filter(Q(date_created__date__gte=startDate.date()) & Q(date_created__date__lte=endDate.date()) & Q(status=OrderStatus.COMPLETED)).count()
  
		context['last_month_orders'] = Order.objects.select_related('user')\
		.filter(Q(date_created__date__gte=last_start.date()) & Q(date_created__date__lte=last_end.date()) & Q(status=OrderStatus.COMPLETED)).count()
		
		increased_instructor = context['total_instructors'] - context['last_month_instructors']
		increased_order = context['total_orders'] - context['last_month_orders']
  
		context['order_increase_from_last_month'] = round((increased_order/context['total_orders']) * 100, 2) if increased_order > 0 else 0
		context['instructor_increase_from_last_month'] = round((increased_instructor/context['total_instructors']) * 100, 2) if increased_instructor > 0 else 0

		return Response(context)
	
	def top_n(self, request, n, *args, **kwargs):
		instructor_list = CourseReview.objects.select_related('user', 'course__user__instructor').values('course').annotate(total_rate=Avg('rate')).order_by('-total_rate').values_list('course__user__instructor',flat=True)
		sales_instructor = self.get_queryset().values('id').annotate(total_sales=Count('instructor_transactions')).order_by('-total_sales').values_list('id', flat=True)[:n]
		result_list = list(chain(instructor_list, sales_instructor))
		queryset  = self.get_queryset().filter(id__in=result_list)[:n]
		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data)
			
	def instructor_statements(self, request, *args, **kwargs):
		instructor = self.get_object()
		queryset = Statement.objects.for_instructor(instructor).distinct()
		serializer = InstructorStatementSerializer(queryset, context={'instructor': instructor}, many=True)
		return Response(serializer.data)
    

	def instructor_statement_transactions(self, request, *args, **kwargs):
		instructor = self.get_object()
		statement_id = self.kwargs.get('st_pk', None)
		statements_transactions = StatementTransactions.objects.filter(transaction_detail__instructor=instructor.id, statement=statement_id)
		serializer = StatementTransactionSerializer(statements_transactions, many=True)
		return Response(serializer.data)