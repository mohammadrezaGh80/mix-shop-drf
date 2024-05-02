import django_filters
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404

from datetime import date, timedelta

from .models import Category, Customer, Order, Product, Seller


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
    age_max = django_filters.NumberFilter(field_name='birth_date', method='filter_age_max', label='age_max')
    age_min = django_filters.NumberFilter(field_name='birth_date', method='filter_age_min', label='age_min')
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

    SELLER_GENDER_MALE = 'm'
    SELLER_GENDER_FEMALE = 'f'

    SELLER_GENDER = [
        (SELLER_GENDER_MALE, _('Male')),
        (SELLER_GENDER_FEMALE, _('Female')),
    ]

    gender = django_filters.ChoiceFilter(field_name='gender', choices=SELLER_GENDER, method='filter_gender', label='gender')

    def filter_gender(self, queryset, field_name, value):
        if value == self.SELLER_GENDER_MALE:
            filter_condition = {field_name: self.SELLER_GENDER_MALE}
            return queryset.filter(**filter_condition)
        elif value == self.CUSTOMER_GENDER_FEMALE:
            filter_condition = {field_name: self.SELLER_GENDER_FEMALE}
            return queryset.filter(**filter_condition)

    class Meta:
        model = Seller
        fields = []


class SellerMeProductFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte', label='price_min')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte', label='price_max')
    has_inventory = django_filters.BooleanFilter(field_name='inventory', method='filter_has_inventory', label='has_inventory')
    category = django_filters.NumberFilter(field_name='category', method='filter_category', label='category')

    def filter_has_inventory(self, queryset, field_name, value):
        filter_condition = {}
        if value is True:
            filter_condition = {f'{field_name}__gte': 1}
        elif value is False:
          filter_condition = {f'{field_name}': 0}
        return queryset.filter(**filter_condition)

    def filter_category(self, queryset, field_name, value):
        category = get_object_or_404(Category, pk=value)
        list_category_descendants = list(category.get_descendants(include_self=True))

        filter_condition = {f'{field_name}__in': list_category_descendants}
        return queryset.filter(**filter_condition)
    
    class Meta:
        model = Seller
        fields = []


class ProductFilter(SellerMeProductFilter):
    seller = django_filters.NumberFilter(field_name='seller', lookup_expr='exact', label='seller')

    class Meta:
        model = Product
        fields = []


class OrderFilter(django_filters.FilterSet):

    ORDER_STATUS_PAID = "p"
    ORDER_STATUS_UNPAID = "u"
    ORDER_STATUS_CANCELED = "c"
    ORDER_STATUS = [
        (ORDER_STATUS_PAID, _("Paid")),
        (ORDER_STATUS_CANCELED, _("Canceled")),
        (ORDER_STATUS_UNPAID, _("Unpaid"))
    ]

    status = django_filters.ChoiceFilter(field_name='status', choices=ORDER_STATUS, method='filter_status', label='status')
    customer = django_filters.NumberFilter(field_name='customer', lookup_expr='exact', label='customer')

    def filter_status(self, queryset, field_name, value):
        if value == self.ORDER_STATUS_UNPAID:
            filter_condition = {field_name: self.ORDER_STATUS_UNPAID}
            return queryset.filter(**filter_condition)
        elif value == self.ORDER_STATUS_CANCELED:
            filter_condition = {field_name: self.ORDER_STATUS_CANCELED}
            return queryset.filter(**filter_condition)
        elif value == self.ORDER_STATUS_PAID:
            filter_condition = {field_name: self.ORDER_STATUS_PAID}
            return queryset.filter(**filter_condition)
    
    class Meta:
        model = Order
        fields = []
