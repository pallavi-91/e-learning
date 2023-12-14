from django.conf.global_settings import LANGUAGES

from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext as _
from django.db.models.query import QuerySet

from rest_framework import serializers, exceptions
from rest_framework.serializers import Serializer, ModelSerializer
from apps.transactions.models import Transactions
from apps.utils.query import get_object_or_none

from apps.courses.models import Course
from apps.users.models import Instructor, UserClass

class InstructorSerializer(ModelSerializer):

    class Meta:
        model = Instructor
        fields = (
            'id',
            'user',
            'date_created',
            'date_updated',
        )


class UserSerializer(ModelSerializer):

    instructor = InstructorSerializer(read_only=True)
    languages = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'handle',
            'instructor',

            'first_name',
            'last_name',
            'email',
            'headline',
            'bio',
            'photo',
            'language',
            'languages',
            'stats',
            'balance',
            'paypal_email',
        )

    def get_languages(self, instance):
        """ return the list of available
            languages
        """
        return dict(LANGUAGES)

    def get_stats(self, instance):
        """ return user statistics
        """
        return instance.stats


class PersonalInfoSerializer(ModelSerializer):
    email = serializers.CharField(required=False)
    bio = serializers.CharField(min_length=60,required=False)

    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'first_name',
            'last_name',
            'photo',
            'headline',
            'language',
            'bio',
            'email',
            'paypal_email',
        )

    def validate_email(self,email): 
        request= self.context.get("request")
        user = get_object_or_none(get_user_model(),email=email); 
        if not user: return email

        if user.id == request.user.id:
            raise serializers.ValidationError(_('This is your current email')) 

        raise serializers.ValidationError(_('Email already taken')) 



class UserShortSerializer(ModelSerializer):


    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'first_name',
            'last_name',
            'headline',
            'bio',
            'language',
            'email',
            'photo',
        )

    def to_representation(self, instance):
        d = super().to_representation(instance)
        d['stats'] = instance.stats
        return d


class TransactionSerializer(ModelSerializer):
    class Meta:
        model = Transactions
        fields = (
            'id',
            'order',
            'type',
            'status',
            'gross_amount',
            'gateway_charge',
            'currency_code',
            'channel_type',
            'payout_status',
            'date_updated',
            'platform_fee',
            'net_amount',
            'can_refund',
        )



class ReportSerializer(Serializer):

    month = serializers.CharField()
    transactions = TransactionSerializer(many=True)

    class Meta:
        model = Transactions


class TransactionMonthTotalSerializer(Serializer):

    class Meta:
        model = Transactions


    def calculate_totals(self,qs: QuerySet):
        affiliates = qs.filter(channel_type=self.Meta.model.AFFILIATE)
        ad_programs = qs.filter(channel_type=self.Meta.model.AD)
        organics = qs.filter(channel_type=self.Meta.model.ORGANIC)
        affiliates_total = ad_programs_total = organics_total = 0

        for aff in affiliates:
            affiliates_total += aff.net_amount

        for aff in ad_programs:
            ad_programs_total += aff.net_amount

        for aff in organics:
            organics_total += aff.net_amount


        return {
            'affiliates_total': round(affiliates_total,2), 
            'ad_programs_total': round(ad_programs_total,2), 
            'organics_total': round(organics_total,2), 
            'totals': round(affiliates_total + organics_total + ad_programs_total,2) 
        }
