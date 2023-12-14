from lib2to3.pytree import Base
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from apps.utils.paypal.payout import Payout
from apps.transactions.models import Transactions, TransactionTypes, TransactionStatus

class Command(BaseCommand):
    """ management command to update
        the payout transaction statuses
    """
    help = "check and update payout transaction status"

    def handle(self, *args, **kwargs):
        transactions = Transactions.objects.filter(
            payout_status=TransactionStatus.PENDING, type=TransactionTypes.PAYOUT)

        for trans in transactions:
            Payout().status(trans)