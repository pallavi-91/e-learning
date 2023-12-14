import datetime
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import localdate
from apps.utils.paypal.payout import Payout
from apps.transactions.models import Transactions, TransactionTypes

class Command(BaseCommand):
    """ management command to send
        payouts to instuctors
    """
    help = "send payouts to instructors"

    def __get_threshold_date(self):
        return localdate() - datetime.timedelta(days=settings.PAYOUT_THRESHOLD)

    def handle(self, *args, **options):
        # get the transactions
        transactions = Transactions.objects.filter(type=TransactionTypes.SALE,
            date_updated__date__lt=self.__get_threshold_date()).distinct('user')

        payout_users = []

        for t in transactions:
            # check if the user has available balance.
            # user needs to have a paypal email.
            if t.user.payout_balance > 0 and t.user.paypal_email:
                payout_users.append(t.user)

        # send payment through paypal
        Payout(users=payout_users).send()