from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from datetime import date

from .models import Customer, Address

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
