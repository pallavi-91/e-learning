from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.status import ShareTypes, InstructorGroups
from apps.status.mixins import AutoCreatedUpdatedMixin
from rest_framework import serializers
import uuid

PERCENTAGE_VALIDATOR = [MinValueValidator(0), MaxValueValidator(100)]
    
class InstructorGroup(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = "instructor_groups"
    
    group_name = models.CharField(max_length=50, default=InstructorGroups.DEFAULT, unique=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self) -> str:
        return f"<InstructorGroup> {self.group_name}"
    


class SharePrices(AutoCreatedUpdatedMixin):
    """This class is the channel of the course purchase"""
    class Meta:
        db_table = "shareprices"
        unique_together = ('share_types', 'group',)
    
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    share_types = models.CharField(max_length=20, choices = ShareTypes.choices, default=ShareTypes.ORGANICS)
    instructor_share = models.FloatField(default=0.0, validators=PERCENTAGE_VALIDATOR)
    platform_share = models.FloatField(default=0.0, validators=PERCENTAGE_VALIDATOR)
    affiliate_share = models.FloatField(default=0.0, validators=PERCENTAGE_VALIDATOR)
    thkee_credit = models.FloatField(default=0.0, validators=PERCENTAGE_VALIDATOR)
    group_name = models.CharField(max_length=20, choices = InstructorGroups.choices, default=InstructorGroups.DEFAULT, blank=True)
    group = models.ForeignKey(InstructorGroup, null=True, blank=True, on_delete=models.SET_NULL)
    
    def __str__(self) -> str:
        return f'<SharePrices> {self.share_types}'

    def to_json(self):
        return ChannelModelSerializer(self).data

# Convert the model object to json
class ChannelModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharePrices
        fields = '__all__'