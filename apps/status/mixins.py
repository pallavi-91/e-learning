from django.db import models
from django.db.models import BooleanField

class AutoCreatedUpdatedMixin(models.Model):
    """Django model mixin providing created_at, updated_at fields"""

    date_created = models.DateTimeField(auto_now_add=True, db_index=True)
    date_updated = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        abstract = True

class AtMostOneBooleanField(BooleanField):
    def pre_save(self, model_instance, add: bool):
        objects = model_instance.__class__.objects
        # If True, then set all other as False
        if getattr(model_instance, self.attname):
            objects.update(**{self.attname: False})
        return getattr(model_instance, self.attname)