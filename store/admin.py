from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.utils.translation import gettext as _
from django.db.models import Count
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.html import format_html
from django.contrib.contenttypes.models import ContentType

from .models import Customer, Seller, Category, Product, Address, Comment, Cart, CartItem, Order, OrderItem, Person


# Custom filters
class GenderFilter(admin.SimpleListFilter):
    title = 'gender status'
    parameter_name = 'gender'

    GENDER_MALE = 'm'
    GENDER_FEMALE = 'f'
    GENDER_NOT_DEFINED = 'n'

    def lookups(self, request, model_admin):
        return [
            (self.GENDER_MALE, _('Male')),
            (self.GENDER_FEMALE, _('Female')),
            (self.GENDER_NOT_DEFINED, _('Not defined'))
        ]
    
    def queryset(self, request, queryset):
        if self.value() == self.GENDER_MALE:
            return queryset.filter(gender=Person.PERSON_GENDER_MALE)
        elif self.value() == self.GENDER_FEMALE:
            return queryset.filter(gender=Person.PERSON_GENDER_FEMALE)
        elif self.value() == self.GENDER_NOT_DEFINED:
            return queryset.filter(gender=Person.PERSON_GENDER_NOT_DEFINED)


class InventoryFilter(admin.SimpleListFilter):
    title = 'inventory status'  
    parameter_name = 'inventory'

    INVENTORY_GREATER_THAN_TEN = '>10'
    INVENTORY_BETWEEN_FIVE_AND_TEN = '5<=10'
    INVENTORY_LOWER_THAN_FIVE = '<5'

    def lookups(self, request, model_admin):
        return [
            (self.INVENTORY_LOWER_THAN_FIVE, _('Low')),
            (self.INVENTORY_BETWEEN_FIVE_AND_TEN, _('Medium')),
            (self.INVENTORY_GREATER_THAN_TEN, _('High'))
        ]
    
    def queryset(self, request, queryset):
        if self.value() == self.INVENTORY_LOWER_THAN_FIVE:
            return queryset.filter(inventory__lt=5)
        elif self.value() == self.INVENTORY_BETWEEN_FIVE_AND_TEN:
            return queryset.filter(inventory__range=(5, 10))
        elif self.value() == self.INVENTORY_GREATER_THAN_TEN:
            return queryset.filter(inventory__gt=10)


# Custom admin 
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['get_phone', 'first_name', 'last_name', 'wallet_amount', 'gender', 'num_of_comments', 'num_of_addresses']
    list_editable = ['gender']
    list_per_page = 15
    list_filter = [GenderFilter]
    autocomplete_fields = ['user']
    search_fields = ['first_name', 'last_name']
    list_select_related = ['user']

    def get_queryset(self, request):
        return super().get_queryset(request)\
            .annotate(comments_count=Count('comments')).prefetch_related('addresses')
            
    @admin.display(description='# comments', ordering='comments_count')
    def num_of_comments(self, customer):
        url = (
            reverse('admin:store_comment_changelist')
            + '?'
            + urlencode({
                "object_id": customer.id
            })
        )
        return format_html('<a href={}>{}</a>', url, customer.comments_count)

    @admin.display(description='# addresses') # TODO: ordering
    def num_of_addresses(self, customer):
        content_type_id = ContentType.objects.get_for_model(customer).id
        
        url = (
            reverse('admin:store_address_changelist')
            + '?'
            + urlencode({
                'content_type_id': content_type_id,
                'object_id': customer.id
            })
        )
        return format_html('<a href={}>{}</a>', url, customer.addresses.count())
    
    @admin.display(description='phone', ordering='user__phone')
    def get_phone(self, customer):
        return customer.user.phone


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'national_code', 'gender', 'status', 'num_of_addresses']
    list_editable = ['gender']
    list_per_page = 10
    list_filter = [GenderFilter]
    autocomplete_fields = ['user']

    def get_queryset(self, request):
        return super().get_queryset(request)\
            .annotate(addresses_count=Count('addresses'))

    @admin.display(description='# addresses', ordering='addresses_count')
    def num_of_addresses(self, seller):
        content_type_id = ContentType.objects.get_for_model(seller).id
        
        url = (
            reverse('admin:store_address_changelist')
            + '?'
            + urlencode({
                'content_type_id': content_type_id,
                'object_id': seller.id
            })
        )
        return format_html('<a href={}>{}</a>', url, seller.addresses_count)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title']
    search_fields = ['title']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'category', 'seller', 'price', 'inventory', 'num_of_comments']
    list_per_page = 15
    list_filter = [InventoryFilter]
    autocomplete_fields = ['category']
    prepopulated_fields = {
        'slug': ['title']
    }

    def get_queryset(self, request):
        return super().get_queryset(request)\
            .prefetch_related('comments')\
            .annotate(comments_count=Count('comments'))

    @admin.display(description='# comments', ordering='comments_count')
    def num_of_comments(self, product):
        url = (
            reverse('admin:store_comment_changelist')
            + '?'
            + urlencode({
                'product_id': product.id
            })
        )

        return format_html('<a href={}>{}</a>', url, product.comments.count())


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'get_user_type', 'province', 'city', 'plaque', 'postal_code']
    list_per_page = 15

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('content_object').select_related('content_type')

    @admin.display(description='full_name')
    def get_full_name(self, address):
        return address.content_object
    
    @admin.display(description='user_type')
    def get_user_type(self, address):
        return address.content_type.model_class().__name__


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('content_object')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    pass


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_select_related = ['product']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_select_related = ['customer']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_select_related = ['product']
