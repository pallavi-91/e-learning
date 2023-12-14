from django.conf import settings
from .auth import Authorization

PAYPAL_PARTNER_ONBOARDING = f"{settings.PAYPAL_API_URL}/v2/customer/partner-referrals"

### TODO: This cannot be implemented unless requested
###       from support (paypal)

class Partner(Authorization):
    """ on board product sellers to the
        merchant account
        https://developer.paypal.com/docs/api/partner-referrals/v2/
    """
    def __init__(self, user, **kwargs):
        # on-boarding user (instructor)
        self.user = user
        return super().__init__(**kwargs)

    def onboard(self):
        """ Creates a partner referral that is shared by the API caller.
            The referrals contains the client's personal, business, financial
            and operations that the partner wants to onbaord the client.
        """
        result = self.POST(PAYPAL_PARTNER_ONBOARDING, {
            "email": self.user.email,
            "individual_owners": [
                {
                    "names": [
                        {
                            "given_name": self.user.first_name,
                            "surname": self.user.last_name,
                            "type": "LEGAL",
                        }
                    ],
                    "id": f"{self.user.id}",
                    "type": "PRIMARY",
                }
            ],
            "partner_config_override": {
                "return_url": "/api/users/payout/onboarding/success/",
                "return_url_description": "the url to return the instructors after the paypal onboarding process.",
            },
            "legal_consents": [
                {
                    "type": "SHARE_DATA_CONSENT",
                    "granted": True
                }
            ],
            "products": [
                "EXPRESS_CHECKOUT"
            ],
            "business_entity": {
                "business_type": {
                    "type": "INDIVIDUAL",
                    "subtype": "ASSO_TYPE_INCORPORATED"
                },
                "beneficial_owners": {
                    "individual_beneficial_owners": [
                        {
                            "names": [
                                {
                                    "given_name": self.user.first_name,
                                    "surname": self.user.last_name,
                                    "type": "LEGAL",
                                }
                            ],
                            "percentage_of_ownership": "50",
                        }
                    ],
                    "business_beneficial_owners": [
                        {
                            "business_type": {
                                "type": "INDIVIDUAL",
                                "subtype": "ASSO_TYPE_INCORPORATED"
                            },
                            "names": [
                                {
                                "business_name": "Test Enterprise",
                                "type": "LEGAL_NAME"
                                }
                            ],
                            "emails": [
                                {
                                "type": "CUSTOMER_SERVICE",
                                "email": "customerservice@example.com"
                                }
                            ],
                            "percentage_of_ownership": "50"
                        }
                    ]
                }
            }
        })

        return result