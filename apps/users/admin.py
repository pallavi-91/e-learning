from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    Instructor,
    OrderToken,
    PasswordToken,
    Cart,
    CartItem,
    Order,
    UserClass,
    NotificationSettings
) 
from apps.transactions.models import RefundRequest

@admin.register(PasswordToken)
class PasswordTokenAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'is_activated')


class InstructorInline(admin.StackedInline):
    """ instructor admin config
    """
    model = Instructor
    extra = 0
    readonly_fields = ('date_created', 'date_updated')


@admin.register(get_user_model())
class UserAdmin(BaseUserAdmin):
    """ user admin config
    """
    readonly_fields = ('date_joined',)
    ordering = ('email',)
    search_fields = ("first_name", "last_name", "email")

    filter_horizontal = ('groups', 'user_permissions',)
    list_display = ('id','email', 'first_name', 'last_name', 'is_instructor', 'date_joined',)
    inlines = (InstructorInline,)


    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'photo', 'headline', 'bio', 'language')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                       'groups', 'user_permissions', 'paypal_email')
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined')
        })
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

    def is_instructor(self, obj):
        return  "Yes" if obj.is_instructor else 'No'

class CartItemInline(admin.StackedInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline,]


@admin.register(UserClass)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('course', 'code', 'user', 'order', 'is_purchased', 'date_created')

class ClassInline(admin.StackedInline):
    model = UserClass
    extra = 0
    filter_horizontal = ('subsections',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'paypal_orderid', 'status', 'date_created', 'date_updated')
    inlines = (ClassInline,)



@admin.register(RefundRequest)
class AdminRefundRequest(admin.ModelAdmin):
    list_display = ('__str__','course_name','status','date_created',)
    list_filter = ['status']
    readonly_fields = ('course_name',)

    def course_name(self,instance):
        return instance.transaction.user_class.course


@admin.register(OrderToken)
class OrderTokenRefundRequest(admin.ModelAdmin):
    list_display = ('__str__','date_added','is_used',)
    search_fields = ['email']
    
@admin.register(NotificationSettings)
class NotificationSettings(admin.ModelAdmin):
    list_display = ('__str__','user')


    

class UserInstructor(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'user', 'payout_method', 'payout_pay_active']
    
admin.site.register(Instructor, UserInstructor)

# unregister the built-in models from
# the admin panel
from django.contrib.auth.models import Group

admin.site.unregister(Group)