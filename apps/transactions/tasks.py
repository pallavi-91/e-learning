import pdb
from huey.contrib.djhuey import db_periodic_task, db_task
from huey import crontab
from apps.statements.models import Statement, StatementStatus, StatementTransactions
from apps.users.models import Instructor
from .models import InstructorPayouts, TransactionPayout, TransactionTypes, PayoutStatus, PayoutType
from .models import Transactions, PayoutDirectTransition
import arrow
from rest_framework import serializers
from django.db.models import Avg, Q, Sum
from apps.apis.admin.pricing.serializers import CurrencySerializer
from apps.apis.admin.sales.transactions.serializers import PaymentTypeSerializer
        
# Convert the model object to json
class TransModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transactions
        fields = '__all__'
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['currency'] = CurrencySerializer(instance.currency).data
        context['payment_type'] = PaymentTypeSerializer(instance.payment_type).data
        context['payment_type'] .update({
                'gateway_charge': instance.gateway_charge
            })
        return context

@db_task(name="generate_all_months_statements")
def all_statements():
    transactions = Transactions.objects.order_by('date_created')
    if transactions.exists():
        start_transaction = transactions.first().date_created
        last_ransaction = transactions.last().date_created
        for d in arrow.Arrow.range('month', start_transaction, last_ransaction):
            period = d.format('MMMM YYYY')
            current_start, current_end = d.span('month')
            current_month_statement, _ = Statement.objects.get_or_create(start_date=current_start.date(),end_date = current_end.date())
            current_month_statement.period = period
            current_month_statement.save()

@db_periodic_task(crontab(minute='30', hour='23'))
def update_statements():
    """
     Statement will be updated everyday by EOD (11:30 PM).
    """
    # Get the current month statements
    current_month_start, current_month_end = arrow.utcnow().span('month')
    current_month_statement, created = Statement.objects.get_or_create(start_date=current_month_start.date(),end_date = current_month_end.date())
    if created:
        current_month_statement.status = StatementStatus.CURRENT
        current_month_statement.period = current_month_start.format("MMMM YYYY")
        current_month_statement.save()
    # Get all transaction of today
    current_start, current_end = arrow.utcnow().span('day')
    todays_tansactions = Transactions.objects.filter(Q(date_updated__gte=current_start.datetime) & Q(date_updated__lte=current_end.datetime))
    
    transactions = []
    
    for trans in todays_tansactions:
        transaction = TransModelSerializer(trans).data
        transactions.append(StatementTransactions(statement=current_month_statement,transaction_detail= transaction))

    StatementTransactions.objects.bulk_create(transactions)
    
    #update last month status
    last_month_start, last_month_end = arrow.utcnow().shift(months=-1).span('month')
    Statement.objects.filter(start_date=last_month_start.date(),end_date = last_month_end.date()).update(status=StatementStatus.OPEN)
    Statement.objects.filter(Q(start_date__lt=last_month_start.date())).update(status=StatementStatus.CLOSED)
    
# Payout
    
@db_periodic_task(crontab(minute='40', hour='23'))
def setup_instructor_ongoing_payouts():
    """
    Update Payout transactions everyday EOD at (11:40 PM)
    """
    instructors = Instructor.objects.select_related('user').order_by('date_created')
    current_month_start, _ = arrow.utcnow().span('month')
    ongoing_period = current_month_start.date()
    today_start, today_end = arrow.utcnow().span('month')
    
    for instructor in instructors:
        ongoing_payout , ongoing_created= InstructorPayouts.objects.get_or_create(period = ongoing_period, user = instructor.user)
        if ongoing_created:
            ongoing_payout.due_date = current_month_start.shift(months=+2, days=+2).datetime
            ongoing_payout.save()
            
        # Add transactions ongoing payout
        ongoing_transactions  = Transactions.objects.select_related('instructor').sales_transactions().filter(instructor = instructor.user, date_updated__gte=today_start.datetime , date_updated__lte=today_end.datetime)
        ongoing_payout_transactions = []
        for trans in ongoing_transactions:
            ongoing_payout_transactions.append(TransactionPayout(payout=ongoing_payout, transaction=trans))
        TransactionPayout.objects.bulk_create(ongoing_payout_transactions, update_conflicts = False)
       
       
@db_periodic_task(crontab(minute='50', hour='23'))
def setup_instructor_upcoming_payouts():
    """
    Update Payout transactions everyday EOD at (11: 50 PM)
    """
    instructors = Instructor.objects.select_related('user').order_by('date_created')
    last_month_start, last_month_end = arrow.utcnow().shift(months=-1).span('month')
    upcoming_period = last_month_start.date()
    
    for instructor in instructors:
        # Upcoming Payouts
        upcoming_payout , upcoming_created= InstructorPayouts.objects.get_or_create(period = upcoming_period, user = instructor.user)
        if upcoming_created:
            upcoming_payout.payout_type = PayoutType.UPCOMING
            upcoming_payout.save()
        # Add transaction upcoming payout
        upcoming_transactions  = Transactions.objects.select_related('instructor').sales_transactions().filter(instructor = instructor.user, date_updated__date__gte=last_month_start.date() , date_updated__date__lte=last_month_end.date())
        upcoming_payout_transactions = []
        for trans in upcoming_transactions:
            upcoming_payout_transactions.append(TransactionPayout(payout=upcoming_payout, transaction=trans))
        
        TransactionPayout.objects.bulk_create(upcoming_payout_transactions, update_conflicts = False)


@db_periodic_task(crontab(minute='0', hour='23'))
def update_inactive_instructor_payouts(user_id=None):
    """
    Update Payout for inactive instructir to keep hold, EOD at (11: 00 PM)
    """
    if not user_id:
        # Run for all
        instructors = Instructor.objects.select_related('user').filter(Q(user__is_active=False)|Q(payout_pay_active=False))
        for instructor in instructors:
            payouts = InstructorPayouts.objects.select_related('user').filter(Q(user = instructor.user) & (~Q(status=PayoutStatus.SUCCESS) | ~Q(payout_type=PayoutType.PAID)))
            for payout in payouts:
                payout.payout_type = PayoutType.INACTIVE
                payout.save()
                notify_inactive_payout(payout)
    else:
        payouts = InstructorPayouts.objects.select_related('user').filter(Q(user_id = user_id) & (~Q(status=PayoutStatus.SUCCESS) | ~Q(payout_type=PayoutType.PAID)))
        for payout in payouts:
            payout.payout_type = PayoutType.INACTIVE
            payout.save()
            notify_inactive_payout(payout)


@db_task()
def notify_inactive_payout(payout, *args, **kwargs):
     # Send mail to instructor and notify that his payouts are inactrive due to some reasaon.
    print(f"Huey is working!! Payout is {payout}")


@db_task()
def add_paid_payout_transactions(payout, *args, **kwargs):
    # Add a new transaction on the orders and classes
    # Send mail to instructor and notify that his payouts are inactrive due to some reasaon.
    print(f"Huey is working!! Payout is {payout}")
    instance, created = PayoutDirectTransition.objects.get_or_create(payout_id=payout, status=kwargs.get('action'), user_id=kwargs.get('user'))
    instance.reason = kwargs.get('reason', '')
    instance.save()


@db_periodic_task(crontab( minute='0', hour='23', day='3'))
def process_batch_payout(*args, **kwargs):
    """
        Send payment to the instructor as a payout in batch
        on every 3rd of the month at '11 PM'
    """
    pass
