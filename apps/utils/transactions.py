from apps.status import PaymentMethods, SupportedGateway, TransactionStatus, TransactionTypes
from apps.utils.query import get_model

 
class TransactionManager(object):
    """ manage transactions
    """
    @property
    def model(self):
        return get_model('transactions.Transactions')

    def create_paypal_sale(self, trans_id, class_id, user, instructor,
        order, gross_amount, gateway_charge, currency, channel):
        """ create a order type transaction
        """
        from apps.transactions.models import PaymentType
        payment_type = PaymentType.objects.filter(payment_gateway=SupportedGateway.PAYPAL,
                                               payment_method=PaymentMethods.ONLINE_TRANSFER).last()
        
        return self.model.objects.create(type=TransactionTypes.SALE, 
                                         status=TransactionStatus.SUCCESS,
                                         payment_transaction_id=trans_id, 
                                         user_class_id=class_id, 
                                         student=user, 
                                         instructor=instructor, 
                                         order=order,
                                         gross_amount=gross_amount,
                                         currency=currency, 
                                         gateway_charge=gateway_charge, 
                                         channel=channel, 
                                         payment_type=payment_type)

    def create_payout(self, status, payout_status, trans_id, user, instructor, 
                      gross_amount, gateway_charge, currency, channel):
        """ create a payout type transaction
        """
        return self.model.objects.create(type=self.model.PAYOUT, 
                                         status=status.title(),
                                         payout_status=payout_status, 
                                         payment_transaction_id=trans_id, 
                                         student=user, 
                                         instructor=instructor, 
                                         gross_amount=gross_amount,
                                         gateway_charge=gateway_charge,
                                         currency=currency, 
                                         channel=channel)


