from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """ user manager
    """
    def create_user(self, email, password=None, **kwargs):
        """ create normal user
        """
        if not email:
            raise ValueError("Email field is required.")
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.is_active = True
        user.save()

        return user

    def create_superuser(self, email, password, **kwargs):
        """ create superuser
        """
        user = self.create_user(email, password, **kwargs)
        user.is_staff = True
        user.is_superuser = True
        user.save()

        return user
