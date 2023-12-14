import string
import random, uuid
import json
from django.conf import settings
from types import SimpleNamespace

def get_coupon_code_length(length=8):
    return settings.DSC_COUPON_CODE_LENGTH if hasattr(settings, 'DSC_COUPON_CODE_LENGTH') else length


def get_user_model():
    return settings.AUTH_USER_MODEL


def get_random_code(length=8):
    length = get_coupon_code_length(length=length)
    code = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))
    
    return f"TK{code}"

def get_transaction_code(length=5):
    times = uuid.uuid1().time*length
    return f'TRN{times}TK'


class JSONDecoder(json.JSONDecoder):
    def decode(self, json_string):
        json_data = json.loads(json_string)
        return SimpleNamespace(**json_data)