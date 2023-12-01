from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

from uuid import uuid4

from .validators import PostalCodeValidator


class Address(models.Model):
    postal_code_validator = PostalCodeValidator()

    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.PROTECT, 
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

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        abstract = True


class Customer(Person):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="customer", verbose_name=_("User"))
    wallet_amount = models.PositiveIntegerField(default=0, verbose_name=_("Wallet amount"))

    addresses = GenericRelation(Address, related_query_name="customer")
    comments = GenericRelation('Comment', related_query_name="customer")

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")


class Seller(Person):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="seller", verbose_name=_("User"))
    cv = models.FileField(upload_to="store/cv_files/", blank=True, null=True, verbose_name=_("CV"))

    addresses = GenericRelation(Address, related_query_name="seller")
    comments = GenericRelation('Comment', related_query_name="seller")

    class Meta:
        verbose_name = _("Seller")
        verbose_name_plural = _("Sellers")


class Category(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"))

    def __str__(self):
        return self.title
    
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

    created_datetime = models.DateTimeField(auto_now_add=True, verbose_name=_("Created datetime"))
    modified_datetime = models.DateTimeField(auto_now=True, verbose_name=_("Modified datetime"))

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")


class Comment(models.Model):
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
        limit_choices_to=models.Q(app_label="store", model="customer") | models.Q(app_label="store", model="seller") # TODO: is need seller?
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="comments", verbose_name=_("Product"))
    title = models.CharField(max_length=255, blank=True, verbose_name=_("Title"))
    body = models.TextField(verbose_name=_("Body"))
    status = models.CharField(max_length=2, choices=COMMENT_STATUS, default=COMMENT_STATUS_WAITING, verbose_name=_("Status"))

    created_datetime = models.DateTimeField(auto_now_add=True, verbose_name=_("Created datetime"))
    modified_datetime = models.DateTimeField(auto_now=True, verbose_name=_("Modified datetime"))


    def __str__(self):
        return f"{self.title}({self.content_object})"
    
    class Meta:
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, verbose_name=_("ID"))
    
    created_datetime = models.DateTimeField(auto_now_add=True, verbose_name=_("Created datetime"))
    modified_datetime = models.DateTimeField(auto_now=True, verbose_name=_("Modified datetime"))

    def __str__(self):
        return f"Created at {self.created_datetime}"
    
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
        return f"Order {self.id}(Customer: {self.customer})"
    
    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items", verbose_name=_("Cart"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items", verbose_name=_("Product"))
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)], verbose_name=_("Quantity"))
    price = models.PositiveIntegerField(verbose_name=_("Price"))


    def __str__(self):
        return f"Order item(id: {self.id}): {self.product} x {self.quantity}"

    class Meta:
        unique_together = [["order", "product"]]
        verbose_name = _("Order item")
        verbose_name_plural = _("Order items")
