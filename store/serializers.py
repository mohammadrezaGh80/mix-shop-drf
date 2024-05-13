from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db import transaction

from datetime import date, timedelta
from types import NoneType
from mptt.exceptions import InvalidMove

from .models import Cart, CartItem, Category, Comment, Customer, Address, Order, OrderItem, Person, ProductImage, Seller, Product

User = get_user_model()


class AddressCustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ['id', 'province', 'city', 'plaque', 'postal_code']
    
    def create(self, validated_data):
        customer_pk = self.context.get('customer_pk')
        customer = get_object_or_404(Customer, pk=customer_pk)
        return Address.objects.create(content_object=customer, **validated_data)


class AddressSellerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ['id', 'province', 'city', 'plaque', 'postal_code']
    
    def create(self, validated_data):
        seller_pk = self.context.get('seller_pk')
        seller = get_object_or_404(Seller, pk=seller_pk)
        return Address.objects.create(content_object=seller, **validated_data)


class CustomerSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.phone')
    age = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'user', 'first_name', 'last_name', 
                  'profile_image', 'gender', 'age']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation
    
    def get_age(self, customer):
        if customer.birth_date:
            return (date.today() - customer.birth_date).days // 365
        return None


class CustomerDetailSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.phone', read_only=True)
    age = serializers.SerializerMethodField()
    addresses = AddressCustomerSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'user', 'first_name', 'last_name', 'profile_image', 
                  'age', 'birth_date', 'gender', 'wallet_amount', 'addresses']
        read_only_fields = ['wallet_amount']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation
    
    def get_age(self, customer):
        if customer.birth_date:
            return (date.today() - customer.birth_date).days // 365
        return None


class RequestSellerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    birth_date = serializers.DateField()
    gender = serializers.ChoiceField(choices=Person.PERSON_GENDER)
    cv = serializers.FileField(validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
                               help_text=_('CV file size should be less than or equal to 5 megabytes'))
    
    class Meta:
        model = Seller
        fields = ['id', 'first_name', 'last_name', 'company_name', 'birth_date', 'gender',
                  'national_code', 'cv']
        read_only_fields = ['id']
        
    def validate_gender(self, gender):
        if gender not in [Seller.PERSON_GENDER_MALE, Seller.PERSON_GENDER_FEMALE]:
            raise serializers.ValidationError(
                _("Please choose your gender")
            )
        return gender
    
    def validate_cv(self, cv):
        cv_size = cv.size
        if cv_size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                _('CV file size should be less than or equal to 5 megabytes.')
            )
        return cv
    
    def get_initial(self):
        initial_dict = super().get_initial()
        customer = self.context.get('request').user.customer
        field_names = ['first_name', 'last_name', 'birth_date', 'gender']

        for field in field_names:
            initial_dict[field] = getattr(customer, field)

        return initial_dict
    
    def create(self, validated_data):
        user = self.context.get('user')
        validated_data['user'] = user
        return super().create(validated_data)


class SellerSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()

    class Meta:
        model = Seller
        fields = ['id', 'company_name', 'first_name', 'last_name', 'profile_image',
                  'national_code', 'gender', 'age']
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation
    
    def get_age(self, seller):
        if seller.birth_date:
            return (date.today() - seller.birth_date).days // 365
        return None 
    

class SellerCreateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255, label=_('First name'))
    last_name = serializers.CharField(max_length=255, label=_('Last name'))
    birth_date = serializers.DateField(label=_('Birth date'))
    profile_image = serializers.ImageField(label=_('Profile image'))
    gender = serializers.ChoiceField(choices=Person.PERSON_GENDER, label=_('Gender'))
    cv = serializers.FileField(validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
                               help_text=_('CV file size should be less than or equal to 5 megabytes'),
                               label=_('CV'))

    class Meta:
        model = Seller
        fields = ['id', 'user', 'company_name', 'first_name', 'last_name', 'profile_image',
                  'national_code', 'birth_date', 'gender', 'cv']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation
    
    def validate_gender(self, gender):
        if gender not in [Seller.PERSON_GENDER_MALE, Seller.PERSON_GENDER_FEMALE]:
            raise serializers.ValidationError(
                _("Please choose your gender")
            )
        return gender
    

class SellerDetailSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255, label=_('First name'))
    last_name = serializers.CharField(max_length=255, label=_('Last name'))
    profile_image = serializers.ImageField(label=_('Profile image'))
    birth_date = serializers.DateField(label=_('Birth date'))
    gender = serializers.ChoiceField(choices=Person.PERSON_GENDER, label=_('Gender'))
    age = serializers.SerializerMethodField()
    addresses = AddressSellerSerializer(many=True, read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Seller
        fields = ['id', 'company_name', 'first_name', 'last_name', 'profile_image',
                  'national_code', 'age', 'birth_date', 'gender', 'cv', 'products_count', 'addresses']
        read_only_fields = ['company_name', 'cv', 'national_code']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation
    
    def get_age(self, seller):
        if seller.birth_date:
            return (date.today() - seller.birth_date).days // 365
        return None 
    
    def get_products_count(self, seller):
        return seller.products.count()
    
    def validate_gender(self, gender):
        if gender not in [Seller.PERSON_GENDER_MALE, Seller.PERSON_GENDER_FEMALE]:
            raise serializers.ValidationError(
                _("Please choose your gender")
            )
        return gender


class SellerListRequestsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Seller
        fields = ['id', 'first_name', 'last_name', 'company_name', 'cv']


class SellerChangeStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Seller
        fields = ['id', 'status']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ['id', 'title', 'sub_category']
    
    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except InvalidMove:
            raise serializers.ValidationError({'detail': _('A category may not be made a sub_category of any of its descendants or itself')})

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.sub_category:
            representation['sub_category'] = instance.sub_category.title
        return representation
    

class CategoryDetailSerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'title', 'sub_category', 'products_count']
    
    def get_products_count(self, category):
        return category.get_products_count_of_category()    
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.sub_category:
            representation['sub_category'] = instance.sub_category.title
        return representation
    

class CommentObjectRelatedField(serializers.RelatedField):
    """
    A custom field to use for the `content_object` generic relationship.
    """

    def to_representation(self, instance):
        if isinstance(instance, Customer):
            return instance.full_name if instance.full_name else 'Unknown'
        elif isinstance(instance, Seller):
            return instance.company_name 
        raise Exception('Unexpected type of comment object')
    

class ReplyCommentSerializer(serializers.ModelSerializer):
    display_name = CommentObjectRelatedField(source='content_object', read_only=True)
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'reply_to', 'display_name', 'user_type', 'title', 'body']
    
    def get_user_type(self, comment):
        return comment.content_type.model_class().__name__


class CommentSerializer(serializers.ModelSerializer):
    display_name = CommentObjectRelatedField(source='content_object', read_only=True)
    user_type = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    count_likes = serializers.SerializerMethodField()
    count_dislikes = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'display_name', 'user_type', 'title', 'body', 'rating', 'count_likes', 'count_dislikes', 'reply_to', 'replies']
        extra_kwargs = {
            'reply_to': {'write_only': True}
        }
    
    def get_replies(self, comment):
        queryset = comment.get_descendants(include_self=False).select_related('content_type').prefetch_related('content_object')\
                    .filter(status=Comment.COMMENT_STATUS_APPROVED)
        serializer = ReplyCommentSerializer(queryset, many=True)
        return serializer.data
       
    def get_user_type(self, comment):
        return comment.content_type.model_class().__name__
    
    def get_count_likes(self, comment):
        return comment.likes.count()
    
    def get_count_dislikes(self, comment):
        return comment.dislikes.count()
    
    def validate_reply_to(self, reply_to):
        if reply_to:
            product = self.context.get('product')

            try:
                product.comments.get(id=reply_to.id)
            except Comment.DoesNotExist:
                raise serializers.ValidationError({'detail': _("There isn't comment with id=%(reply_to_id)d in the %(product_title)s product.") % {'reply_to_id': reply_to.id, 'product_title': product.title}})

        return reply_to
    
    def validate(self, attrs):
        instance = Comment(**attrs)

        try:
            instance.clean()
        except ValidationError as e:
            raise serializers.ValidationError({"detail": e.messages})

        return super().validate(attrs)
    
    def create(self, validated_data):
        product = self.context.get('product')
        user = self.context.get('user')
        
        validated_data['product'] = product
        validated_data['content_object'] = user
        return super().create(validated_data)


class CommentDetailSerializer(serializers.ModelSerializer):
    display_name = CommentObjectRelatedField(source='content_object', read_only=True)
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'reply_to', 'display_name', 'user_type', 'title', 'body', 'rating']
        read_only_fields = ['reply_to', 'rating']
    
    def get_user_type(self, comment):
        return comment.content_type.model_class().__name__
   

class ProductSellerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Seller
        fields = ['id', 'first_name', 'last_name', 'company_name', 'gender']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation


class ProductImageSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'name']
    
    def validate(self, attrs):
        product_pk = self.context.get('product_pk')
        product = None

        if product_pk:
            product = get_object_or_404(Product, pk=product_pk)
        attrs['product'] = product

        instance = ProductImage(**attrs)

        try:
            instance.clean()
        except ValidationError as e:
            raise serializers.ValidationError({"detail": e.messages})

        return super().validate(attrs)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')

        representation['image'] = request.build_absolute_uri(instance.image.url)

        return representation


class ProductSerializer(serializers.ModelSerializer):
    seller = serializers.CharField(source='seller.company_name', read_only=True)
    category = CategorySerializer(read_only=True)
    status = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title','slug' ,'category', 'thumbnail', 'seller' ,'price', 'viewer', 'status']

    def get_status(self, product):
        return 'Available' if product.inventory > 0 else 'Unavailable'
    
    def get_thumbnail(self, product):
        if not product.product_images:
            return None
        
        product = product.product_images[0]
        serializer = ProductImageSerializer(product, context=self.context)
        return serializer.data


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    seller = ProductSellerSerializer()
    status = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title','slug' ,'category', 'images', 'seller' ,'price', 'status', 'inventory', 'description', 'viewer', 'specifications', 'average_rating', 'comments']

    def get_status(self, product):
        return 'Available' if product.inventory > 0 else 'Unavailable'
    
    def get_average_rating(self, product):
        queryset = Comment.objects.filter(product=product, status=Comment.COMMENT_STATUS_APPROVED)
        
        return round(sum([comment.rating for comment in queryset]) / queryset.count(), 1)


class ProductCreateSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    image_ids = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True, label=_('Image ids'))

    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'category', 'images', 'image_ids',
                  'price', 'inventory', 'description', 'specifications']
    
    def validate_image_ids(self, image_ids):
        for image_id in image_ids:
            try:
                product_image = ProductImage.objects.get(pk=image_id)
            except ProductImage.DoesNotExist:
                raise serializers.ValidationError(_("There isn't any product image with id=%(image_id)s.") % {"image_id": image_id})
            else:
                if product_image.product:
                    raise serializers.ValidationError(_("There is one or more images that belong to another products."))
        
        return image_ids
    
    def validate_specifications(self, specifications):
        if isinstance(specifications, NoneType):
            raise serializers.ValidationError(_("This field may not be null"))
        return specifications

    def create(self, validated_data):
        request = self.context.get('request')
        image_ids = validated_data.pop('image_ids', [])

        product = Product(**validated_data)
        product.slug = slugify(product.title)
        product.seller = request.user.seller
        product.save()

        product_images = []
        for image_id in image_ids:
            product_image = ProductImage.objects.get(pk=image_id)
            product_image.product = product
            product_images.append(product_image)
        
        ProductImage.objects.bulk_update(product_images, fields=['product'])

        return product


class ProductUpdateSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'category', 'images',
                  'price', 'inventory', 'description', 'specifications']
    
    def validate_specifications(self, specifications):
        if isinstance(specifications, NoneType):
            raise serializers.ValidationError(_("This field may not be null"))
        return specifications
        
    def update(self, instance, validated_data):
        title = validated_data.get('title')
        if title:
            instance.slug = slugify(title)
            instance.save(update_fields=['slug'])

        return super().update(instance, validated_data)


class SellerMeProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    status = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title','slug' ,'category', 'thumbnail' ,'price', 'viewer', 'status']

    def get_status(self, product):
        return 'Available' if product.inventory > 0 else 'Unavailable'
    
    def get_thumbnail(self, product):
        if not product.product_images:
            return None
        
        product = product.product_images[0]
        serializer = ProductImageSerializer(product, context=self.context)
        return serializer.data


class SellerMeProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    status = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title','slug' ,'category', 'images' ,'price', 'status', 'inventory', 'description', 'viewer', 'specifications']

    def get_status(self, product):
        return 'Available' if product.inventory > 0 else 'Unavailable'


class CommentListWaitingSerializer(serializers.ModelSerializer):
    user = CommentObjectRelatedField(source='content_object', read_only=True)
    user_type = serializers.SerializerMethodField()
    product = serializers.CharField(source='product.title')

    class Meta:
        model = Comment
        fields = ['id', 'product', 'user', 'user_type', 'title', 'body']
    
    def get_user_type(self, comment):
        return comment.content_type.model_class().__name__


class CommentChangeStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ['status']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation


class CartItemProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ['id', 'title', 'price']


class CartItemSerializer(serializers.ModelSerializer):
    product = CartItemProductSerializer()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']
    
    def get_total_price(self, cart_item):
        return cart_item.product.price * cart_item.quantity


class CartItemCreateSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']
    
    def validate_product(self, product):
        cart_pk = self.context.get('cart_pk')

        try:
            CartItem.objects.get(cart_id=cart_pk, product=product)
        except CartItem.DoesNotExist:
            return product
        else:
            raise serializers.ValidationError({"detail": _("This product is exist in the customer's cart.")})

    def validate(self, attrs):
        product = attrs.get('product')
        quantity = attrs.get('quantity')

        if quantity > product.inventory:
            raise serializers.ValidationError(
                {"detail": _("You can't add product more than product's inventory(%(product_quantity)d) to your cart.") % {'product_quantity': product.inventory}}
            )

        return super().validate(attrs)
    
    def get_total_price(self, cart_item):
        return cart_item.product.price * cart_item.quantity
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['product'] = CartItemProductSerializer(instance.product).data
        return representation

    def create(self, validated_data):
        cart_pk = self.context.get('cart_pk')

        return CartItem.objects.create(
            cart_id=cart_pk,
            **validated_data
        )


class CartItemUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CartItem
        fields = ['id', 'quantity']
    
    def validate(self, attrs):
        product = self.instance.product
        quantity = attrs.get('quantity')

        if isinstance(quantity, int) and quantity > product.inventory:
            raise serializers.ValidationError(
                {"detail": _("You can't add product more than product's inventory(%(product_quantity)d) to your cart.") % {'product_quantity': product.inventory}}
            )
        
        return super().validate(attrs)



class CartSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()

    class Meta:
        model = Cart
        fields = ['id', 'customer']


class CartDetailSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    items = CartItemSerializer(many=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'customer', 'items', 'total_price']
    
    def get_total_price(self, cart):
        return sum([cart_item.product.price * cart_item.quantity for cart_item in cart.items.all()])


class OrderItemSerializer(serializers.ModelSerializer):
    product = CartItemProductSerializer()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'total_price']
    
    def get_total_price(self, order_item):
        if order_item.order.status == Order.ORDER_STATUS_PAID:
            return order_item.price * order_item.quantity
        return order_item.product.price * order_item.quantity


class OrderDetailSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    items = OrderItemSerializer(many=True)
    total_price = serializers.SerializerMethodField()
    address = AddressCustomerSerializer()
    created_datetime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'status', 'created_datetime', 'delivery_date', 'address', 'items', 'total_price']
    
    def get_total_price(self, order):
        if order.status == Order.ORDER_STATUS_PAID:
            return sum([order_item.price * order_item.quantity for order_item in order.items.all()])
        return sum([order_item.product.price * order_item.quantity for order_item in order.items.all()])        

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation


class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    created_datetime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'address', 'status', 'created_datetime', 'delivery_date']
        read_only_fields = ['status']
        extra_kwargs = {
            'address': {'write_only': True}
        }
    
    def validate_address(self, address):
        customer = self.context.get('request').user.customer

        if not address.content_object == customer:
            raise serializers.ValidationError(_("The address with id=%(address_id)d doesn't belong to you.")  % {'address_id': address.id})
            
        return address
    
    def validate_delivery_date(self, delivery_date):
        today = date.today()
        next_day = today + timedelta(days=3)
        valid_dates = []

        for i in range(3):
            if next_day.weekday() == 4:
                next_day = next_day + timedelta(days=1)
            valid_dates.append(next_day)
            next_day = next_day + timedelta(days=1)

        if delivery_date not in valid_dates:
            raise serializers.ValidationError(_("It's not possible to deliver the order on the selected day(Valid dates: %(valid_dates)s).") % {"valid_dates": ", ".join([date.strftime("%d-%m-%Y") for date in valid_dates])})
        return delivery_date
    
    def validate(self, attrs):
        customer = self.context.get('request').user.customer
        cart = customer.cart
        
        if CartItem.objects.filter(cart=cart).count() == 0:
            raise serializers.ValidationError({'detail': _('Your cart is empty, Please add some products to it first.')})
        
        return super().validate(attrs)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation
    
    def create(self, validated_data):
        with transaction.atomic():
            customer = self.context.get('request').user.customer
            cart = customer.cart
            cart_items = cart.items.select_related('product')

            order = Order(**validated_data)
            order.customer = customer
            order.save()

            order_items = [
                OrderItem(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                ) for cart_item in cart_items
            ]

            OrderItem.objects.bulk_create(order_items)
        
            cart_items.all().delete()

            return order


class OrderMeSerializer(serializers.ModelSerializer):
    created_datetime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Order
        fields = ['id', 'status', 'created_datetime']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation


class OrderMeDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total_price = serializers.SerializerMethodField()
    address = AddressCustomerSerializer()
    created_datetime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'status', 'created_datetime', 'delivery_date', 'address', 'items', 'total_price']
    
    def get_total_price(self, order):
        if order.status == Order.ORDER_STATUS_PAID:
            return sum([order_item.price * order_item.quantity for order_item in order.items.all()])
        return sum([order_item.product.price * order_item.quantity for order_item in order.items.all()])        

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation


class OrderUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = ['id', 'status']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation
    