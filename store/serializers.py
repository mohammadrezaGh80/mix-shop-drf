from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify

from datetime import date

from .models import Category, Comment, Customer, Address, Seller, Product

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
    cv = serializers.FileField(validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
                               help_text=_('CV file size should be less than or equal to 5 megabytes.'))
    
    class Meta:
        model = Seller
        fields = ['id', 'first_name', 'last_name', 'birth_date', 'gender',
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
    user = serializers.CharField(source='user.phone', read_only=True)
    age = serializers.SerializerMethodField()

    class Meta:
        model = Seller
        fields = ['id', 'user', 'first_name', 'last_name', 'profile_image',
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
    cv = serializers.FileField(validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
                               help_text=_('CV file size should be less than or equal to 5 megabytes.'))

    class Meta:
        model = Seller
        fields = ['id', 'user', 'first_name', 'last_name', 'profile_image',
                  'national_code', 'birth_date', 'gender', 'cv']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation
    

class SellerDetailSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.phone', read_only=True)
    age = serializers.SerializerMethodField()
    addresses = AddressSellerSerializer(many=True, read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Seller
        fields = ['id', 'user', 'first_name', 'last_name', 'profile_image',
                  'national_code', 'age', 'birth_date', 'gender', 'cv', 'products_count', 'addresses']
    
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


class SellerListRequestsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Seller
        fields = ['id', 'first_name', 'last_name', 'cv']


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
        fields = ['id', 'title']
    

class CategoryDetailSerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'title', 'products_count']
    
    def get_products_count(self, category):
        return category.products.count()
    

class CommentObjectRelatedField(serializers.RelatedField):
    """
    A custom field to use for the `content_object` generic relationship.
    """

    def to_representation(self, value):
        if isinstance(value, Customer):
            return value.full_name
        elif isinstance(value, Seller):
            return value.full_name
        raise Exception('Unexpected type of comment object')


class CommentSerializer(serializers.ModelSerializer):
    user = CommentObjectRelatedField(source='content_object', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'title', 'body', 'status']
        read_only_fields = ['status']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation
    

class ProductSellerSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = Seller
        fields = ['id', 'user', 'first_name', 'last_name', 'gender']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation


class ProductSerializer(serializers.ModelSerializer):
    seller = serializers.CharField(source='seller.full_name', read_only=True)
    category = serializers.CharField(source='category.title', read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title','slug' ,'category', 'seller' ,'price', 'status']

    def get_status(self, product):
        return 'Available' if product.inventory > 0 else 'Unavailable'


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    seller = ProductSellerSerializer()
    status = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title','slug' ,'category', 'seller' ,'price', 'status', 'inventory', 'description', 'comments']

    def get_status(self, product):
        return 'Available' if product.inventory > 0 else 'Unavailable'


class ProductCreateSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'category',
                  'price', 'inventory', 'description']
    
    def create(self, validated_data):
        request = self.context.get('request')
        product = Product(**validated_data)
        product.slug = slugify(product.title)
        product.seller = request.user.seller
        product.save()
        return product
    
    def update(self, instance, validated_data):
        title = validated_data.get('title')
        instance.slug = slugify(title)
        instance.save()
        return super().update(instance, validated_data)
