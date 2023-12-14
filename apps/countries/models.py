from django.db import models
from django.core.validators import RegexValidator
from django.core.validators import MinLengthValidator
from apps.status.mixins import AutoCreatedUpdatedMixin

# alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')
ALPHA = RegexValidator(r'^[A-Z]*$', 'Only Alphabetic characters are allowed.')
NUMERIC = RegexValidator(r'^[0-9]*$', 'Only Numeric characters are allowed.')

def auto_increase():
    count = Country.objects.count()
    return count+1
# Create your models here.
class Country(AutoCreatedUpdatedMixin): 
    class Meta:
        db_table = "countries"
        ordering = ['sort_number']
        
    name = models.CharField(max_length=200, unique=True)
    two_letter_iso_code = models.CharField(max_length=2, unique=True, validators=[ALPHA,MinLengthValidator(2)])
    three_letter_iso_code = models.CharField(max_length=3, unique=True, validators=[ALPHA,MinLengthValidator(3)])
    numeric_iso_code = models.CharField(max_length=3, unique=True, validators=[NUMERIC,MinLengthValidator(3)])
    subject_to_vat = models.BooleanField(default=False)
    allow_billing = models.BooleanField(default=False)
    sort_number = models.PositiveIntegerField(unique=True,default=auto_increase)
    

    def __str__(self) -> str:
        return f"<Country> {self.name}"