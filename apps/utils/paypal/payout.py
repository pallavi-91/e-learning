from django.conf import settings
from django.utils import timezone
from apps.users.models import Transaction, PayoutBatch, User
from apps.utils.http import urlsafe
from apps.utils.transactions import TransactionManager

from .auth import Authorization

PAYPAL_PAYOUTS_URL = f"{settings.PAYPAL_API_URL}/v1/payments/payouts"
PAYPAL_PAYOUT_TRANS_URL = f"{settings.PAYPAL_API_URL}/v1/payments/payouts-item"


class Payout(TransactionManager, Authorization):
    """ Use the `/payouts` resource to create a batch payout,
        update the status for a batch payout, show the status
        of a batch payout with the transaction status and other
        data for individual payout items, and request approval
        for a batch payout.
        https://developer.paypal.com/docs/api/payments.payouts-batch/v1/
    """
    def __init__(self, users=None, **kwargs):
        # list of users eligible for payout
        self.users = users
        return super().__init__(**kwargs)

    def __get_batch_id(self):
        """ generate a batch id based on the
            current time.
        """
        return timezone.now().strftime("Payouts_%Y_%m_%d")

    def __sender_batch_header(self):
        """ set the sender batch header
        """
        return {
            "sender_batch_id": self.__get_batch_id(),
            "email_subject": settings.PAYPAL_PAYOUT_SUBJECT,
            "email_message": settings.PAYPAL_PAYOUT_MESSAGE,
        }

    def __prepare_items(self):
        """ set values for each user
        """
        def __iter(users):
            for user in users:
                yield {
                    "recipient_type": "EMAIL",
                    "note": "Thanks for sharing your knowledge!",
                    "sender_item_id": f"{user.id}",
                    "receiver": user.paypal_email,
                    "amount": {
                        "value": f"{user.payout_balance}",
                        "currency": "USD"
                    }
                }
        
        return [i for i in __iter(self.users)]

    def send(self, data={}):
        """ send payouts
        """
        # set sender batch headers
        data.update({'sender_batch_header': self.__sender_batch_header()})
        # prepare payout items
        data.update({'items': self.__prepare_items()})

        resp = self.POST(PAYPAL_PAYOUTS_URL, data=data)
        # log the batch transaction
        batch_h = resp.get('batch_header')
        PayoutBatch.objects.create(raw=resp,
            batch_id=batch_h['payout_batch_id'], status=batch_h['batch_status'])

        # get batch information
        resp = self.GET(urlsafe(PAYPAL_PAYOUTS_URL, batch_h['payout_batch_id']))

        # create payout type transactions
        def __getamount(d, k): return d[k]['value'] 

        for i in resp['items']:
            p_item = i['payout_item']
            user_ = User.objects.get(id=p_item['sender_item_id'])

            self.create_payout(i['transaction_status'], i['transaction_status'], i['payout_item_id'],
                user_, __getamount(p_item, 'amount'), __getamount(i, 'payout_item_fee'),
                p_item['amount']['currency']
            )

        return resp

    def status(self, trans):
        """ get payout transaction status
        """
        resp = self.GET(urlsafe(PAYPAL_PAYOUT_TRANS_URL, trans.gateway_transaction_id))
        trans.payout_status = resp['transaction_status'].lower()

        # check if there are errors
        errors = resp.get('errors')
        if errors:
            trans.payout_error = errors

        trans.save()

        return trans