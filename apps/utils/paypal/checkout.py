import pdb
from django.conf import settings
from apps.utils.http import urlsafe

from .auth import Authorization
from .urls import PAYPAL_ORDERS_URL, SITE_API_URL

class Items(object):
    """ product items
    """
    def __init__(self, items, *args, **kwargs):
        self.items = items
        return super().__init__(*args, **kwargs)

    def _to_dict(self):
        """ prepare item to dict which is
            compatible to the api request
        """
        for item in self.items:
            yield {
                "name": item.title,
                "quantity": "1",
                "unit_amount": f"{item.price}",
                "description": item.subtitle,
                "sku": item.code.hex,
                "category": "DIGITAL_GOODS",
                #"tax": "" UNCOMMENT FOR NOW
            }

    def to_dict(self):
        return list(self._to_dict())


class Item(object):
    """ course
    """
    def __init__(self, item, **kwargs):
        self.item = item
        return super().__init__(**kwargs)

    def to_dict(self):
        """ prepare item to dict which is
            compatible to the api request
        """
        return {
            "name": self.item.course.title,
            "quantity": "1",
            "unit_amount": f"{self.item.price}",
            "description": self.item.course.subtitle,
            "sku": self.item.course.code.hex,
            "category": "DIGITAL_GOODS",
            #"tax": "" UNCOMMENT FOR NOW
        }


class PaypalOrder(Authorization):
    """ create paypal items, orders,
        and make actual payment
    """
    def __init__(self, order, classes=None, **kwargs):
        """ customer object.
            fields: (email_address, address,
                birth_date(YYYY-MM-DD), name, phone)
        """
        self.order = order
        self.classes = classes
        return super().__init__(**kwargs)

    def create(self):
        """ create an order
            https://developer.paypal.com/docs/api/orders/v2/
        """
        def __return_urls(url_):
            return urlsafe(SITE_API_URL, 'cart', url_)

        # purchase unit
        # (we only have one since we do one at a time)
        def __purchase(_class):
            return dict(
                amount=dict(
                    currency_code=_class.currency_code.upper(),
                    value=str(_class.price),
                    items=[Item(_class).to_dict()]
                ),
                custom_id=str(_class.id),
                reference_id=str(_class.id),
            )

        purchases = [__purchase(c) for c in self.classes]

        # application context. customize the payer experience
        # during the approval process for the payment with PayPal.
        context = dict()
        # The type of landing page to show on the PayPal
        # site for customer checkout.
        context.update({"landing_page": "BILLING"})
        # shipping preference. no shipping as we are digital goods
        context.update({"shipping_preference": "NO_SHIPPING"})
        # Configures a Continue or Pay Now checkout flow.
        context.update({"user_action": "PAY_NOW"})
        # return urls
        context.update({
            "return_url": __return_urls("paymentsuccess"),
            "cancel_url": __return_urls("cancel/"),
        })

        data = {
            "intent": "CAPTURE", # immediate payment
            "purchase_units": purchases,
            "processing_instruction": "NO_INSTRUCTION",
            "application_context": context
        }
        return self.POST(PAYPAL_ORDERS_URL, data=data)

    def pay(self):
        """ capture payment for order
        """
        return self.POST(urlsafe(PAYPAL_ORDERS_URL, self.order.paypal_orderid, 'capture'),)

