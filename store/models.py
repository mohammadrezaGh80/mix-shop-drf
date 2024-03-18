from django.db import models
from django.db.models import Count
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError

import os
from uuid import uuid4
from PIL import Image, ImageChops
from mptt.models import TreeForeignKey, MPTTModel

from .validators import PostalCodeValidator, NationalCodeValidator


class Address(models.Model):
    postal_code_validator = PostalCodeValidator()

    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        limit_choices_to=models.Q(app_label="store", model="customer") | models.Q(app_label="store", model="seller")
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    province = models.CharField(max_length=255, verbose_name=_("Province"))
    city = models.CharField(max_length=255, verbose_name=_("City"))
    plaque = models.PositiveSmallIntegerField(verbose_name=_("Plaque"))
    postal_code = models.PositiveBigIntegerField(validators=[postal_code_validator], verbose_name=_("Postal code"))

    def clean(self):
        super().clean()

        if not self.content_object:
            raise ValidationError(_(f"There isn't any {self.content_type.model_class().__name__} with id={self.object_id}."))

    def __str__(self):
        return f"{self.province}(City: {self.city}): {self.postal_code}"
    
    class Meta:
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")


class Person(models.Model):
    PERSON_GENDER_MALE = "m"
    PERSON_GENDER_FEMALE = "f"
    PERSON_GENDER_NOT_DEFINED = ""

    PERSON_GENDER = [
        (PERSON_GENDER_MALE, _('Male')),
        (PERSON_GENDER_FEMALE, _('Female')),
        (PERSON_GENDER_NOT_DEFINED, _('Not defined'))
    ]

    first_name = models.CharField(max_length=255, blank=True, verbose_name=_("First name"))
    last_name = models.CharField(max_length=255, blank=True, verbose_name=_("Last name"))
    birth_date = models.DateField(blank=True, null=True, verbose_name=_("Birth date"))
    profile_image = models.ImageField(upload_to="store/profile_images/", blank=True, null=True, verbose_name=_("Profile image"))
    gender = models.CharField(max_length=1, choices=PERSON_GENDER, blank=True, verbose_name=_("Gender"))

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    class Meta:
        abstract = True


class Customer(Person):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer", verbose_name=_("User"))
    wallet_amount = models.PositiveIntegerField(default=0, verbose_name=_("Wallet amount"))

    addresses = GenericRelation(Address, related_query_name="customer")
    comments = GenericRelation('Comment', related_query_name="customer")

    def __str__(self):
        return self.full_name if self.full_name else 'Unknown'

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")


class Seller(Person):
    SELLER_STATUS_WAITING = "w"
    SELLER_STATUS_ACCEPTED = "a"
    SELLER_STATUS_REJECTED = "r" 

    SELLER_STATUS = [
        (SELLER_STATUS_WAITING, _('Waiting')),
        (SELLER_STATUS_ACCEPTED, _('Accepted')),
        (SELLER_STATUS_REJECTED, _('Rejected'))
    ]

    national_code_validator = NationalCodeValidator()

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller", verbose_name=_("User"))
    company_name = models.CharField(max_length=100, verbose_name=_("Company name"))
    cv = models.FileField(upload_to="store/cv_files/", blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['pdf'])], verbose_name=_("CV"))
    national_code = models.CharField(max_length=10, unique=True, null=True, validators=[national_code_validator], verbose_name=_("National code"))
    status = models.CharField(max_length=1, choices=SELLER_STATUS ,default=SELLER_STATUS_WAITING, verbose_name=_("Status"))

    addresses = GenericRelation(Address, related_query_name="seller")
    comments = GenericRelation('Comment', related_query_name="seller")

    def __str__(self):
        return f"{self.company_name}({self.national_code})"

    class Meta:
        verbose_name = _("Seller")
        verbose_name_plural = _("Sellers")


class Category(MPTTModel):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    sub_category = TreeForeignKey('self', blank=True, null=True, on_delete=models.CASCADE, related_name='sub_categories', verbose_name=_("Sub category"))

    def get_products_count_of_category(self):
        categories = self.get_descendants(include_self=True).annotate(
            products_count=Count('products')
        )
        products_count = 0

        for category in categories:
            products_count += category.products_count
        
        return products_count 

    def __str__(self):
        return self.title
    
    class MPTTMeta:
        order_insertion_by = ['title']
        parent_attr = 'sub_category'

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")


class Product(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    slug = models.SlugField(verbose_name=_("Slug"))
    seller = models.ForeignKey(Seller, on_delete=models.PROTECT, related_name="products", verbose_name=_("Seller"))
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products", verbose_name=_("Category"))
    description = models.TextField(verbose_name=_("Description"))
    price = models.PositiveIntegerField(verbose_name=_("Price"))
    inventory = models.PositiveSmallIntegerField(verbose_name=_("Inventory"))
    specifications = models.JSONField(blank=True, default=dict, verbose_name=_("Specifications"))

    created_datetime = models.DateTimeField(auto_now_add=True, verbose_name=_("Created datetime"))
    modified_datetime = models.DateTimeField(auto_now=True, verbose_name=_("Modified datetime"))

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True, related_name="images", verbose_name=_("Product"))
    image = models.ImageField(upload_to="store/product_images/",
                              validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg'], message=_("File extension not allowed. Allowed extensions include  .jpg, .jpeg"))],
                              verbose_name=_("Image"))
    name = models.CharField(max_length=100, blank=True, verbose_name=_("Name"))


    def clean(self):
        super().clean() 

        if not self.image:
            raise ValidationError(_("This field is required."))
         
        current_image = Image.open(self.image)

        for product_image in ProductImage.objects.filter(product=self.product):
            image = Image.open(product_image.image)

            if current_image.mode == image.mode:
                diff = ImageChops.difference(current_image,image)
                if not diff.getbbox():
                    if getattr(self.product, 'id', False):
                        raise ValidationError(_("This image for product is duplicated"))
                    else:
                        raise ValidationError(_("This image has already been uploaded"))
        
    def save(self, *args, **kwargs):
        if not self.name:
            self.name = os.path.basename(self.image.name).split('.')[0]
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product}({self.id})"
    
    class Meta:
        verbose_name = _("Product image")
        verbose_name_plural = _("Product images")


class Comment(MPTTModel):
    COMMENT_STATUS_WAITING = "w"
    COMMENT_STATUS_APPROVED = "a"
    COMMENT_STATUS_NOT_APPROVED = "na"
    COMMENT_STATUS = [
        (COMMENT_STATUS_WAITING, _("Waiting")),
        (COMMENT_STATUS_APPROVED, _("Approved")),
        (COMMENT_STATUS_NOT_APPROVED, _("Not approved"))
    ]

    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.PROTECT, 
        limit_choices_to=models.Q(app_label="store", model="customer") | models.Q(app_label="store", model="seller")
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="comments", verbose_name=_("Product"))
    title = models.CharField(max_length=255, blank=True, verbose_name=_("Title"))
    body = models.TextField(verbose_name=_("Body"))
    status = models.CharField(max_length=2, choices=COMMENT_STATUS, default=COMMENT_STATUS_WAITING, verbose_name=_("Status"))
    reply_to = TreeForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies', verbose_name=_("Reply to"))

    created_datetime = models.DateTimeField(auto_now_add=True, verbose_name=_("Created datetime"))
    modified_datetime = models.DateTimeField(auto_now=True, verbose_name=_("Modified datetime"))

    def __str__(self):
        return f"{self.title}({self.body[:15] + '...' if len(self.body) > 15 else self.body})"

    class MPTTMeta:
        order_insertion_by = ['title']
        parent_attr = 'reply_to'
    
    class Meta:
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, verbose_name=_("ID"))
    
    created_datetime = models.DateTimeField(auto_now_add=True, verbose_name=_("Created datetime"))
    modified_datetime = models.DateTimeField(auto_now=True, verbose_name=_("Modified datetime"))

    def __str__(self):
        return f"{self.id}"

    class Meta:
        verbose_name = _("Cart")
        verbose_name_plural = _("Carts")


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items", verbose_name=_("Cart"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items", verbose_name=_("Product"))
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)], verbose_name=_("Quantity"))

    def __str__(self):
        return f"Cart(id: {self.id}): {self.product} x {self.quantity}" # TODO: show proper string
    
    class Meta:
        unique_together = [["cart", "product"]]

    class Meta:
        verbose_name = _("Cart item")
        verbose_name_plural = _("Cart items")


class Order(models.Model):
    ORDER_STATUS_PAID = "p"
    ORDER_STATUS_UNPAID = "u"
    ORDER_STATUS_CANCELED = "c"
    ORDER_STATUS = [
        (ORDER_STATUS_PAID, _("Paid")),
        (ORDER_STATUS_CANCELED, _("Canceled")),
        (ORDER_STATUS_UNPAID, _("Unpaid"))
    ]

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=1, choices=ORDER_STATUS, default=ORDER_STATUS_UNPAID, verbose_name=_("Status"))

    created_datetime = models.DateTimeField(auto_now_add=True, verbose_name=_("Created datetime"))
    modified_datetime = models.DateTimeField(auto_now=True, verbose_name=_("Modified datetime"))


    def __str__(self):
        return f"Order {self.id}"
    
    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items", verbose_name=_("Order"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items", verbose_name=_("Product"))
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)], verbose_name=_("Quantity"))
    price = models.PositiveIntegerField(verbose_name=_("Price"))


    def __str__(self):
        return f"Orunique_togetherder item(id: {self.id}): {self.product} x {self.quantity}"

    class Meta:
        unique_together = [["order", "product"]]
        verbose_name = _("Order item")
        verbose_name_plural = _("Order items")
