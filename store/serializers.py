from django.http import Http404
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db.models import Count

from datetime import date
from types import NoneType
from mptt.exceptions import InvalidMove

from .models import Category, Comment, Customer, Address, Person, ProductImage, Seller, Product

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
                               help_text=_('CV file size should be less than or equal to 5 megabytes.'))
    
    class Meta:
        model = Seller
        fields = ['id', 'first_name', 'last_name', 'company_name', 'birth_date', 'gender',
                  'national_code', 'cv']
        read_only_fields = ['id']
        
    def validate_gender(self, gender):
        if gender not in [Seller.PERSON_GENDER_MALE, Seller.PERSON_GENDER_FEMALE]:
            raise serializers.ValidationError(
                _("Please choose your gender.")
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
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    birth_date = serializers.DateField()
    profile_image = serializers.ImageField()
    gender = serializers.ChoiceField(choices=Person.PERSON_GENDER)
    cv = serializers.FileField(validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
                               help_text=_('CV file size should be less than or equal to 5 megabytes.'))

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
                _("Please choose your gender.")
            )
        return gender
    

class SellerDetailSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    profile_image = serializers.ImageField()
    birth_date = serializers.DateField()
    gender = serializers.ChoiceField(choices=Person.PERSON_GENDER)
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
                _("Please choose your gender.")
            )
        return gender


class SellerListRequestsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Seller
        fields = ['id', 'first_name', 'last_name', 'company_name', 'cv']


class SellerChangeStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Seller
        fields = ['status']
    
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
            raise serializers.ValidationError({'detail': _('A category may not be made a sub_category of any of its descendants or itself.')})

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

    class Meta:
        model = Comment
        fields = ['id', 'display_name', 'user_type', 'title', 'body', 'rating', 'reply_to', 'replies']
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
    
    def validate_reply_to(self, reply_to):
        if reply_to:
            product_pk = self.context.get('product_pk')
            product = get_object_or_404(Product, pk=product_pk)

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
        product_pk = self.context.get('product_pk')
        user = self.context.get('user')
        
        validated_data['product_id'] = product_pk
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
    category = serializers.CharField(source='category.title', read_only=True)
    status = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title','slug' ,'category', 'thumbnail', 'seller' ,'price', 'status']

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

    class Meta:
        model = Product
        fields = ['id', 'title','slug' ,'category', 'images', 'seller' ,'price', 'status', 'inventory', 'description', 'specifications', 'comments']

    def get_status(self, product):
        return 'Available' if product.inventory > 0 else 'Unavailable'


class ProductCreateSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    image_ids = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'category', 'images', 'image_ids',
                  'price', 'inventory', 'description', 'specifications']
    
    def validate_image_ids(self, image_ids):
        for image_id in image_ids:
            try:
                product_image = ProductImage.objects.get(pk=image_id)
            except ProductImage.DoesNotExist:
                raise serializers.ValidationError(_(f"There isn't any product image with id={image_id}."))
            else:
                if product_image.product:
                    raise serializers.ValidationError(_(f"There is one or more images that belong to another products."))
        
        return image_ids
    
    def validate_specifications(self, specifications):
        if isinstance(specifications, NoneType):
            raise serializers.ValidationError(_("This field may not be null."))
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
        
    def update(self, instance, validated_data):
        title = validated_data.get('title')
        if title:
            instance.slug = slugify(title)
            instance.save()

        image_ids = validated_data.pop('image_ids', [])
        product_images = []
        for image_id in image_ids:
            product_image = ProductImage.objects.get(pk=image_id)
            product_image.product = instance
            product_images.append(product_image)
        
        ProductImage.objects.bulk_update(product_images, fields=['product'])

        return super().update(instance, validated_data)


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
