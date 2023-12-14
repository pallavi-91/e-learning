from django.db.models import Avg, Case, Count, F, Func, Max, Min, Prefetch, Q, Sum, When, FloatField, Value
from django.db.models.functions import Coalesce, TruncDate, Round, Cast
from django.db.models.fields.json import KeyTextTransform
from django.db import models
# # Instructor shares
# instructor_share_text = Func(F('channel'), Value('instructor_share'), function='jsonb_extract_path_text')
# instructor_share = Cast(instructor_share_text, FloatField())
# # Plateform shares
# platform_share_text = Func(F('channel'), Value('platform_share'), function='jsonb_extract_path_text')
# platform_share = Cast(platform_share_text, FloatField())
# # Affiliate shares
# affiliate_share_text = Func(F('channel'), Value('affiliate_share'), function='jsonb_extract_path_text')
# affiliate_share = Cast(affiliate_share_text, FloatField())

affiliate_share = Cast(KeyTextTransform("affiliate_share", "channel"), models.FloatField())
instructor_share = Cast(KeyTextTransform("instructor_share", "channel"), models.FloatField())
platform_share = Cast(KeyTextTransform("platform_share", "channel"), models.FloatField())

def channel_key_value(key, field='channel'):
    share_text = Func(F(field), Value(key), function='jsonb_extract_path_text')
    key_value = Cast(share_text, FloatField())
    return key_value