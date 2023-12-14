import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.status import CourseStatus
from .orders import Order
from apps.status.mixins import AutoCreatedUpdatedMixin


class Cart(AutoCreatedUpdatedMixin):
    """ user cart
    """
    class Meta:
        db_table = 'user_cart'
    # user is optional for users that have purchased
    # the course but haven't created an account yet.
    user = models.OneToOneField(get_user_model(),
        related_name="cart", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"<UserCart> {self.id}"

    def add_to_cart(self,course):
        """
            False,False it is the auth user course
            CartItem,False is already on cart
            CartItem,True is created
            True,True user already checkout the course
            False,True user already checkout the course
            None,False course is not published or it is free
        """
        if course.status != CourseStatus.STATUS_PUBLISHED: return None, False
        if course.pricing.is_free: return None, False

        if course.user.id == self.user.id: return False, False

        if self.user.user_classes.filter(course=course, is_purchased=True).exists():
            return True,True

        cart_items = self.items.filter(course=course)

        if cart_items.exists():
            return cart_items.first(),False

        return CartItem.objects.create(course=course,cart=self),True

    def clear(self):
        """ clear the items in the cart
        """
        self.items.all().delete()
        return

    def checkout(self, *args, **kwargs):
        """ prepare the item and create
            a purchase order.
        """
        order = Order.objects.create(user=self.user, **kwargs)
        order.add_courses(courses=[i.course for i in self.items.all()])

        return order


class CartItem(AutoCreatedUpdatedMixin):
    """ cart item
    """
    class Meta:
        db_table = 'cart_items'
        
    cart = models.ForeignKey(Cart,
        related_name="items", on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course',
        related_name="cartitems", on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"<CartItem> {self.id}"


class CreditCoupon(AutoCreatedUpdatedMixin):
    """ user coupon
    """
    class Meta:
        db_table = 'credit_coupons'
        
    code = models.UUIDField(default=uuid.uuid4, editable=False)
    

    def __str__(self):
        return f"{self.code}"


########## =========================  Signals ======================================##############


@receiver(post_save, sender=CartItem)
def post_delete_cart_item(instance,created, **kwargs):
    """ delete course in favorites if the course is within the wishlist
    """
    if created:
        user = instance.cart.user
        if user and instance.course in user.favorites.all():
            user.favorites.remove(instance.course)