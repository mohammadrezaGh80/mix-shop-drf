import django_filters
from django.db.models import F, IntegerField, ExpressionWrapper
from django.utils.translation import gettext_lazy as _

from datetime import date, timedelta

from .models import Customer, Seller


class CustomerFilter(django_filters.FilterSet):
    """
        Filtering based on age, age_min, age_max and gender, because 
        It's not currently possible to filter by an empty string so
        define CUSTOMER_GENDER_NOT_DEFINED as 'n' 
    """
    CUSTOMER_GENDER_MALE = 'm'
    CUSTOMER_GENDER_FEMALE = 'f'
    CUSTOMER_GENDER_NOT_DEFINED = 'n'

    CUSTOMER_GENDER = [
        (CUSTOMER_GENDER_MALE, _('Male')),
        (CUSTOMER_GENDER_FEMALE, _('Female')),
        (CUSTOMER_GENDER_NOT_DEFINED, _('Not defined'))
    ]

    age = django_filters.NumberFilter(field_name='birth_date', method='filter_age', label='age')
    age_min = django_filters.NumberFilter(field_name='birth_date', method='filter_age_min', label='age_min')
    age_max = django_filters.NumberFilter(field_name='birth_date', method='filter_age_max', label='age_max')
    gender = django_filters.ChoiceFilter(field_name='gender', choices=CUSTOMER_GENDER, method='filter_gender', label='gender')

    def filter_age(self, queryset, field_name, value):
        max_birth_date = date.today() - timedelta(days=int(value * 365))
        min_birth_date = date.today() - timedelta(days=int((value + 1) * 365))
        filter_condition = {f'{field_name}__range': (min_birth_date, max_birth_date)}
        return queryset.filter(**filter_condition).order_by('-id')
    
    def filter_age_min(self, queryset, field_name, value):
        max_birth_date = date.today() - timedelta(days=int(value * 365))
        filter_condition = {f'{field_name}__lte': max_birth_date}
        return queryset.filter(**filter_condition).order_by('-birth_date')
    
    def filter_age_max(self, queryset, field_name, value):
        min_birth_date = date.today() - timedelta(days=int((value + 1) * 365))
        filter_condition = {f'{field_name}__gte': min_birth_date}
        return queryset.filter(**filter_condition).order_by('birth_date')
    
    def filter_gender(self, queryset, field_name, value):
        if value == self.CUSTOMER_GENDER_MALE:
            filter_condition = {field_name: self.CUSTOMER_GENDER_MALE}
            return queryset.filter(**filter_condition)
        elif value == self.CUSTOMER_GENDER_FEMALE:
            filter_condition = {field_name: self.CUSTOMER_GENDER_FEMALE}
            return queryset.filter(**filter_condition)
        elif value == self.CUSTOMER_GENDER_NOT_DEFINED:
            filter_condition = {field_name: Customer.PERSON_GENDER_NOT_DEFINED}
            return queryset.filter(**filter_condition)

    class Meta:
        model = Customer
        fields = []


class SellerFilter(CustomerFilter):

    class Meta:
        model = Seller
        fields = []
