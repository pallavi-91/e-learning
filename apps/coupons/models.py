from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils.timezone import localtime
from apps.courses.models import Course
from apps.status.mixins import AutoCreatedUpdatedMixin
from apps.transactions.utility import get_random_code, get_transaction_code
from django.db.models.signals import post_save

PERCENTAGE_VALIDATOR = [MinValueValidator(0), MaxValueValidator(100)]
# Create your models here.
class DiscountCoupons(AutoCreatedUpdatedMixin):
    """
        Preconfigured Promo code that can be applied over the order or on course.
    """
    class Meta:
        db_table = 'discount_coupons'
        verbose_name_plural = "Discount Coupons"
        
    name = models.CharField(max_length=100, blank=True, null=True)
    code = models.CharField(max_length=20, blank=True)
    discount = models.FloatField(default=0.0, validators=PERCENTAGE_VALIDATOR)
    expiration_date = models.DateTimeField(verbose_name="Expiration date")
    is_active = models.BooleanField(default=False, verbose_name="Is active?")
    
    times_used = models.IntegerField(default=0, editable=False, verbose_name="Times used")
    max_uses = models.BigIntegerField(default=1, verbose_name="Maximum uses")
    
    def __str__(self) -> str:
        return f"<DiscountCoupons> : {self.discount}"
    
    @property
    def is_valid(self):
        return self.is_active and (self.expiration_date.date() >= localtime().date())
    

class CourseDiscount(AutoCreatedUpdatedMixin):
    """
        (For Display pupose) Discount added with the course
    """
    class Meta:
        db_table = 'course_discount_coupons'
        verbose_name_plural = "Course Discount Coupons"
        
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="discounts")
    coupon = models.ForeignKey(DiscountCoupons, on_delete=models.CASCADE, verbose_name="Coupon")
    is_active = models.BooleanField(default=False, verbose_name="Is active?")
    times_used = models.IntegerField(default=0, editable=False, verbose_name="Times used")

    def __str__(self):
        return f"<CourseDiscount> : {self.id}"
    
    @property
    def discounted_price(self) -> float:
        initial_value = float(self.course.pricing.price)
        
        new_price = initial_value - (initial_value * self.coupon.discount / 100)
        new_price = new_price if new_price >= 0.0 else 0.0

        return new_price
    
    @property
    def discount_value(self) -> float:
        initial_value = float(self.course.pricing.price)
        new_price = initial_value * self.coupon.discount / 100
        return new_price


# Signals

def update_coupon_code(sender, instance, created, *args, **kwargs):
    if created and not instance.code:
        prepared_code = get_random_code()
        while DiscountCoupons.objects.filter(code=prepared_code).count():
            prepared_code = get_random_code()
        instance.code = prepared_code;
        instance.save()

post_save.connect(update_coupon_code, DiscountCoupons)