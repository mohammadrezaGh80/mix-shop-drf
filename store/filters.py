import django_filters
from django.db.models import F, IntegerField, ExpressionWrapper

from datetime import date

from .models import Customer


CONVERT_AGE_TO_MICROSECONDS = 365 * 24 * 60 * 60 * 1000000

class CustomerFilter(django_filters.FilterSet):
    age = django_filters.NumberFilter(field_name='birth_date', method='filter_age', label='age')
    age_min = django_filters.NumberFilter(field_name='birth_date', method='filter_age_min', label='age_min')
    age_max = django_filters.NumberFilter(field_name='birth_date', method='filter_age_max', label='age_max')

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

    class Meta:
        model = Customer
        fields = ['gender']
