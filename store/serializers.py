from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.core.validators import FileExtensionValidator

from datetime import date

from .models import Customer, Address, Seller

User = get_user_model()


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ['id', 'province', 'city', 'plaque', 'postal_code']
    
    def create(self, validated_data):
        customer_pk = self.context.get('customer_pk')
        customer = get_object_or_404(Customer, pk=customer_pk)
        return Address.objects.create(content_object=customer, **validated_data)


class CustomerSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.phone')
    profile_image_url = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'user', 'first_name', 'last_name', 'gender', 'profile_image_url', 'age']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation

    def get_profile_image_url(self, customer):
        request = self.context.get('request')
        if customer.profile_image:
            return request.build_absolute_uri(customer.profile_image.url)
        return None
    
    def get_age(self, customer):
        if customer.birth_date:
            return (date.today() - customer.birth_date).days // 365
        return None

class CustomerCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = ['id', 'user', 'profile_image', 'first_name', 
                  'last_name', 'gender', 'birth_date']


class CustomerDetailSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.phone', read_only=True)
    profile_image_url = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'user', 'first_name', 'last_name', 'profile_image_url', 
                  'age', 'birth_date', 'gender', 'wallet_amount', 'addresses']
        read_only_fields = ['wallet_amount']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation
    
    def get_profile_image_url(self, customer):
        request = self.context.get('request')
        if customer.profile_image:
            return request.build_absolute_uri(customer.profile_image.url)
        return None
    
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
