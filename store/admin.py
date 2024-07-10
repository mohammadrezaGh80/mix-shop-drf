from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Case, When, Sum, Value
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.html import format_html

from datetime import date

from .models import Customer, IncreaseWalletCredit, Seller, Category, Product, Address, Comment, Cart, CartItem, \
                    Order, OrderItem, Person, ProductImage, CommentLike, CommentDislike, Menu


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
        

class IsPaidFilter(admin.SimpleListFilter):
    title = 'is paid status'
    parameter_name = 'is_paid'

    IS_PAID_TRUE = '1'
    IS_PAID_FALSE = '0'

    def lookups(self, request, model_admin):
        return [
            (self.IS_PAID_TRUE, _('True')),
            (self.IS_PAID_FALSE, _('False'))
        ]
    
    def queryset(self, request, queryset):
        if self.value() == self.IS_PAID_TRUE:
            return queryset.filter(is_paid=True)
        elif self.value() == self.IS_PAID_FALSE:
            return queryset.filter(is_paid=False)


# Custom admin 
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['get_phone', 'first_name', 'last_name', 'wallet_amount', 'get_age', 'gender', 'num_of_comments', 'num_of_addresses']
    list_editable = ['gender']
    list_per_page = 15
    list_filter = [GenderFilter]
    autocomplete_fields = ['user']
    search_fields = ['first_name', 'last_name']
    list_select_related = ['user']

    def get_queryset(self, request):
        return super().get_queryset(request)\
            .annotate(comments_count=Count('comments', distinct=True), addresses_count=Count('addresses', distinct=True)).prefetch_related('addresses')
            
    @admin.display(description='# comments', ordering='comments_count')
    def num_of_comments(self, customer):
        url = (
            reverse('admin:store_comment_changelist')
            + '?'
            + urlencode({
                "customer": customer.id
            })
        )
        return format_html('<a href={}>{}</a>', url, customer.comments_count)

    @admin.display(description='# addresses', ordering='addresses_count')
    def num_of_addresses(self, customer):
        url = (
            reverse('admin:store_address_changelist')
            + '?'
            + urlencode({
                'customer': customer.id
            })
        )
        return format_html('<a href={}>{}</a>', url, customer.addresses_count)
    
    @admin.display(description=_('phone'), ordering='user__phone')
    def get_phone(self, customer):
        return customer.user.phone
    
    @admin.display(description=_('age'), ordering='birth_date')
    def get_age(self, customer):
        if customer.birth_date:
            return (date.today() - customer.birth_date).days // 365
        return None 


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'first_name', 'last_name', 'national_code', 'gender', 'status', 'num_of_addresses', 'num_of_products']
    list_editable = ['gender']
    list_per_page = 10
    list_filter = [GenderFilter]
    autocomplete_fields = ['user']
    search_fields = ['company_name']

    def get_queryset(self, request):
        return super().get_queryset(request)\
            .annotate(addresses_count=Count('addresses', distinct=True), products_count=Count('products', distinct=True))

    @admin.display(description='# addresses', ordering='addresses_count')
    def num_of_addresses(self, seller):        
        url = (
            reverse('admin:store_address_changelist')
            + '?'
            + urlencode({
                'seller': seller.id
            })
        )
        return format_html('<a href={}>{}</a>', url, seller.addresses_count)
    
    @admin.display(description='# products', ordering='products_count')
    def num_of_products(self, seller):
        url = (
            reverse('admin:store_product_changelist')
            + '?'
            + urlencode({
                'seller': seller.id
            })
        )

        return format_html('<a href={}>{}</a>', url, seller.products_count)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'sub_category', 'level', 'lft', 'rght', 'num_of_sub_categories', 'num_of_products']
    search_fields = ['title']
    list_per_page = 15

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sub_category').prefetch_related('products')\
            .annotate(sub_categories_count=Count('sub_categories'))
    
    @admin.display(description='# sub_categories', ordering='sub_categories_count')
    def num_of_sub_categories(self, category):
        url = (
            reverse('admin:store_category_changelist')
            + '?'
            + urlencode({
                'sub_category': category.id
            })
        )

        return format_html('<a href={}>{}</a>', url, category.sub_categories_count)
    
    @admin.display(description='# products')
    def num_of_products(self, category):
        url = (
            reverse('admin:store_product_changelist')
            + '?'
            + urlencode({
                'category': category.id
            })
        )

        return format_html('<a href={}>{}</a>', url, category.products.count())


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'category', 'seller', 'price', 'inventory', 'num_of_comments', 'num_of_sales', 'viewer', 'created_datetime']
    list_per_page = 15
    list_filter = [InventoryFilter]
    autocomplete_fields = ['category', 'seller']
    prepopulated_fields = {
        'slug': ['title']
    }
    search_fields = ['title']
    readonly_fields = ['viewer']
    ordering = ['-created_datetime']

    def get_queryset(self, request):
        return super().get_queryset(request)\
            .prefetch_related('comments')\
            .annotate(comments_count=Count('comments', distinct=True),
                      sales_count=Case(When(order_items__order__status=Order.ORDER_STATUS_PAID, then=Sum('order_items__quantity', distinct=True)),
                                       default=Value(0)))

    @admin.display(description='# comments', ordering='comments_count')
    def num_of_comments(self, product):
        url = (
            reverse('admin:store_comment_changelist')
            + '?'
            + urlencode({
                'product_id': product.id
            })
        )

        return format_html('<a href={}>{}</a>', url, product.comments_count)
    
    @admin.display(description='# sales', ordering='sales_count')
    def num_of_sales(self, product):
        return product.sales_count


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['get_content_object', 'get_user_type', 'province', 'city', 'plaque', 'postal_code']
    search_fields = ['province', 'city']
    list_per_page = 15

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('content_object').select_related('content_type')

    @admin.display(description='user')
    def get_content_object(self, address):
        return address.content_object
    
    @admin.display(description='user_type')
    def get_user_type(self, address):
        return address.content_type.model_class().__name__


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'get_content_object', 'product', 'status', 'reply_to', 'num_of_likes', 'num_of_dislikes', 'created_datetime']
    autocomplete_fields = ['product', 'reply_to']
    ordering = ['-created_datetime']
    search_fields = ['title']
    list_per_page = 15
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('content_object', 'likes', 'dislikes')\
               .select_related('product', 'reply_to').annotate(likes_count=Count('likes'), dislikes_count=Count('dislikes'))

    @admin.display(description='user')
    def get_content_object(self, commnet):
        return commnet.content_object
    
    @admin.display(description='# likes', ordering='likes_count')
    def num_of_likes(self, comment):
        url = (
            reverse('admin:store_commentlike_changelist')
            + '?'
            + urlencode({
                'comment': comment.id
            })
        )

        return format_html('<a href={}>{}</a>', url, comment.likes_count)
    
    @admin.display(description='# dislikes', ordering='dislikes_count')
    def num_of_dislikes(self, comment):
        url = (
            reverse('admin:store_commentdislike_changelist')
            + '?'
            + urlencode({
                'comment': comment.id
            })
        )

        return format_html('<a href={}>{}</a>', url, comment.dislikes_count)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'get_phone', 'created_datetime']
    search_fields = ['id']
    autocomplete_fields = ['customer']
    list_per_page = 15
    ordering = ['-created_datetime']

    @admin.display(description=_('phone'))
    def get_phone(self, cart):
        return cart.customer.user.phone


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart_id', 'product', 'quantity']
    list_select_related = ['cart', 'product']
    autocomplete_fields = ['cart', 'product']
    list_per_page = 15


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer', 'status', 'zarinpal_authority', 'zarinpal_ref_id', 'created_datetime', 'delivery_date', 'payment_method', 'num_of_items']
    list_select_related = ['customer']
    search_fields = ['id']
    autocomplete_fields = ['customer', 'address']
    list_per_page = 15

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(items_count=Count('items'))
    
    @admin.display(description='# items', ordering='items_count')
    def num_of_items(self, order):
        url = (
            reverse('admin:store_orderitem_changelist')
            + '?'
            + urlencode({
                'order': order.id
            })
        )

        return format_html('<a href={}>{}</a>', url, order.items_count)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order_customer', 'order', 'product', 'quantity', 'price']
    list_select_related = ['order__customer', 'product']
    autocomplete_fields = ['order', 'product']
    list_per_page = 15

    @admin.display(description="order's customer", ordering='order__customer__first_name')
    def order_customer(self, order_item):
        return order_item.order.customer


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image', 'name']
    autocomplete_fields = ['product']
    list_select_related = ['product']
    list_per_page = 15


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ['get_content_object', 'comment']
    list_per_page = 15

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('comment').prefetch_related('content_object')
    
    @admin.display(description='user')
    def get_content_object(self, comment):
        return comment.content_object


@admin.register(CommentDislike)
class CommentDislikeAdmin(admin.ModelAdmin):
    list_display = ['get_content_object', 'comment']
    list_per_page = 15

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('comment').prefetch_related('content_object')
    
    @admin.display(description='user')
    def get_content_object(self, comment):
        return comment.content_object


@admin.register(IncreaseWalletCredit)
class IncreaseWalletCreditAdmin(admin.ModelAdmin):
    list_display = ['customer', 'amount', 'is_paid', 'zarinpal_authority', 'zarinpal_ref_id', 'created_datetime']
    autocomplete_fields = ['customer']
    list_select_related = ['customer']
    list_editable = ['is_paid']
    list_filter = [IsPaidFilter]
    list_per_page = 15


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ['title', 'url', 'sub_menu']
    search_fields = ['title']
    autocomplete_fields = ['sub_menu']
    list_per_page = 15

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sub_menu')
