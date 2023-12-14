from functools import cached_property
import os
import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from apps.status.mixins import AutoCreatedUpdatedMixin

class Verification(AutoCreatedUpdatedMixin):
    """ user verification token
    """
    class Meta:
        db_table = 'user_verification'
        
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    code = models.CharField(max_length=8, null=True, blank=True)
    is_used = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"<Verification> {self.id}"


    @transaction.atomic
    def verified(self):
        self.is_used = True
        self.save()

        self.user.is_active = True
        self.user.save()

        return

    @cached_property
    def absolute_url(self):
        return os.path.join(settings.SITE_URL, f"verify/{self.code.hex}")

    def send(self):
        """ send verification code to the user's email
        """
        html_content = render_to_string(
            'users/emails/account_verification.html',
            {'obj': self},
        )
        text_content = render_to_string(
            'users/emails/account_verification.txt',
            {'obj': self},
        )
        msg = EmailMultiAlternatives(
            "Verify your Account",
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [self.user.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        self.is_sent = True
        self.save()
        
        return

class AccountDeactivated(AutoCreatedUpdatedMixin):
    """
        This will hold entry when any user get diactivated by admin user
    """
    class Meta:
        db_table = 'deactivated_account'
        
    user = models.OneToOneField(get_user_model(), related_name="user_account", on_delete=models.CASCADE)
    hold_by = models.ForeignKey(get_user_model(), related_name="hold_by", on_delete=models.CASCADE)
    inactive_reason = models.TextField(blank=True)

class PasswordToken(AutoCreatedUpdatedMixin):
    """ forgot password token
    """
    class Meta:
        db_table = 'password_token'
        
    user = models.ForeignKey(get_user_model(),
        related_name="passwordtokens", on_delete=models.CASCADE)
    code = models.UUIDField(default=uuid.uuid4, editable=False)
    is_activated = models.BooleanField(default=False)

    def __str__(self):
        return f"<PasswordToken> {self.id}"

    @cached_property
    def absolute_url(self):
        """ get url password reset
        """
        return os.path.join(
            settings.SITE_PROTOCOL,
            settings.SITE_DOMAIN_URL,
            'p/r',
            self.code.hex
        )

    def send(self):
        """ send the token to the user's email
        """
        # TO DO. setup email host
        return

class ForgotPasswordToken(AutoCreatedUpdatedMixin):
    """ password request token
    """
    class Meta:
        db_table = 'forgot_password_token'
        
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    code = models.UUIDField(default=uuid.uuid4,editable=False,null=True,blank=True)
    is_used = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
            
    def __str__(self):
        return f"[{self.user}] {self.code}"

    def send(self):
        """ send password reset code to
            the user's email.
        """
        html_content = render_to_string(
            'users/emails/password_reset.html',
            {'obj': self},
        )
        text_content = render_to_string(
            'users/emails/password_reset.txt',
            {'obj': self}
        )

        msg = EmailMultiAlternatives(
            "Reset your password",
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [self.user.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        self.is_sent = True
        self.save()

        return


########## =========================  Signals ======================================##############

@receiver(post_save, sender=Verification, weak=False)
def after_save_verification(instance=None, created=False, **kwargs):
    """ events after save
    """
    # check if the is_used is set to true.
    # delete all other verification code that
    # is connected to the specified user.
    if not created and instance.is_used:
        Verification.objects \
            .filter(user=instance.user) \
            .exclude(id=instance.id) \
            .delete()

    if created:
        instance.code = get_user_model().objects \
            .make_random_password(length=8)
        instance.save()
    

@receiver(post_save, sender=PasswordToken)
def after_save_token(instance=None, created=False, **kwargs):
    if not created and instance.is_activated:
        # remove all tokens of the user excluding the one
        # which is activated.
        PasswordToken.objects \
            .filter(user=instance.user, is_activated=False) \
            .exclude(id=instance.id) \
            .delete()