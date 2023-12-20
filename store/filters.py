import django_filters
from django.db.models import F, IntegerField, ExpressionWrapper
from django.utils.translation import gettext_lazy as _

from datetime import date

from .models import Customer


CONVERT_AGE_TO_MICROSECONDS = 365 * 24 * 60 * 60 * 1000000

class CustomerFilter(django_filters.FilterSet):
    """
        Filtering based on age, age_min, age_max and gender, because 
        It's not currently possible to filter by an empty string so
        define CUSTOMER_GENDER_NOT_DEFINED as 'n' 
    """
    CUSTOMER_GENDER_MALE = "m"
    CUSTOMER_GENDER_FEMALE = "f"
    CUSTOMER_GENDER_NOT_DEFINED = "n"

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
        return queryset.annotate(
            age_microseconds=ExpressionWrapper(date.today() - F(field_name), 
                                  output_field=IntegerField())
            ).filter(age_microseconds__range=(value * CONVERT_AGE_TO_MICROSECONDS, (value + 1) * CONVERT_AGE_TO_MICROSECONDS))
    
    def filter_age_min(self, queryset, field_name, value):
        return queryset.annotate(
            age_microseconds=ExpressionWrapper(date.today() - F(field_name), 
                                  output_field=IntegerField())
            ).filter(age_microseconds__gte=value * CONVERT_AGE_TO_MICROSECONDS).order_by('age_microseconds')
    
    def filter_age_max(self, queryset, field_name, value):
        return queryset.annotate(
            age_microseconds=ExpressionWrapper(date.today() - F(field_name), 
                                  output_field=IntegerField())
            ).filter(age_microseconds__lte=(value + 1) * CONVERT_AGE_TO_MICROSECONDS).order_by('-age_microseconds')
    
    def filter_gender(self, queryset, filed_name, value):
        if value == self.CUSTOMER_GENDER_MALE:
            return queryset.filter(gender=self.CUSTOMER_GENDER_MALE)
        elif value == self.CUSTOMER_GENDER_FEMALE:
            return queryset.filter(gender=self.CUSTOMER_GENDER_FEMALE)
        elif value == self.CUSTOMER_GENDER_NOT_DEFINED:
            return queryset.filter(gender=Customer.PERSON_GENDER_NOT_DEFINED)

    class Meta:
        model = Customer
        fields = []
