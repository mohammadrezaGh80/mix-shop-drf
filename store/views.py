from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from rest_framework import generics

from django_filters.rest_framework import DjangoFilterBackend
from functools import cached_property

from . import serializers
from .models import Customer, Address, Seller
from .paginations import CustomLimitOffsetPagination
from .filters import CustomerFilter, SellerFilter
from .permissions import IsCustomerOrSeller, IsSeller


class CustomerViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'put', 'patch']
    queryset = Customer.objects.all().select_related('user').prefetch_related('addresses').order_by('-id')
    permission_classes = [IsAdminUser]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomerFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.CustomerSerializer
        return serializers.CustomerDetailSerializer        
    
    @action(detail=False, methods=['GET', 'PUT', 'PATCH'], permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        user = request.user
        customer = self.queryset.get(id=user.customer.id)

        if request.method == 'GET':
            serializer = serializers.CustomerDetailSerializer(customer, context=self.get_serializer_context())
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method in ['PUT', 'PATCH']:
            partial = False
            if request.method == 'PATCH':
                partial = True
            serializer = serializers.CustomerDetailSerializer(customer, data=request.data,  partial=partial, context=self.get_serializer_context())
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        

class AddressCustomerViewSet(ModelViewSet):
    serializer_class = serializers.AddressCustomerSerializer

    def get_permissions(self):
        customer_pk = self.kwargs.get('customer_pk')

        if customer_pk == 'me':
            return [IsAuthenticated()]
        return [IsAdminUser()]
    
    @cached_property
    def customer(self):
        """
            return customer based on value of customer_pk in url
            if customer_pk is 'me' return customer who is currently logged in
            otherwise if customer_pk is an integer that exist customer with
            this pk so return customer
        """
        customer_pk = self.kwargs.get('customer_pk')

        if customer_pk == 'me':
            customer = Customer.objects.get(user=self.request.user)
        else:
            try:
                customer_pk = int(customer_pk)
                customer = Customer.objects.get(user_id=customer_pk)
            except (ValueError, Customer.DoesNotExist):
                raise Http404

        return customer

    def get_queryset(self):
        return Address.objects.filter(customer=self.customer)
    
    def get_serializer_context(self):
        return {'customer_pk': self.customer.pk}
    


class RequestSellerGenericAPIView(generics.GenericAPIView):
    serializer_class = serializers.RequestSellerSerializer
    permission_classes = [IsAuthenticated, IsCustomerOrSeller]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(data=request.data, context={'request': request, 'user': user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Your request has been successfully registered.'}, status=status.HTTP_200_OK)


class SellerViewSet(ModelViewSet):
    queryset = Seller.objects.all().select_related('user').prefetch_related('addresses').order_by('-id')
    permission_classes = [IsAdminUser]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = SellerFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.SellerSerializer
        elif self.action == 'create':
            return serializers.SellerCreateSerializer
        return serializers.SellerDetailSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.products.count() >= 0:
            return Response({'error': 'There is some products relating this seller. Please remove them first.'})
        
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['GET', 'PUT', 'PATCH', 'DELETE'], permission_classes=[IsSeller])
    def me(self, request, *args, **kwargs):
        user = request.user
        seller = self.queryset.get(id=user.seller.id)

        if request.method == 'GET':
            serializer = serializers.SellerDetailSerializer(seller, context=self.get_serializer_context())
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method in ['PUT', 'PATCH']:
            partial = False
            if request.method == 'PATCH':
                partial = True
            serializer = serializers.SellerDetailSerializer(seller, data=request.data,  partial=partial, context=self.get_serializer_context())
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            seller.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        

class AddressSellerViewSet(ModelViewSet):
    serializer_class = serializers.AddressSellerSerializer

    def get_permissions(self):
        seller_pk = self.kwargs.get('seller_pk')

        if seller_pk == 'me':
            return [IsSeller()]
        return [IsAdminUser()]
    
    @cached_property
    def seller(self):
        """
            return seller based on value of seller_pk in url
            if seller_pk is 'me' return seller who is currently logged in
            otherwise if seller_pk is an integer that exist seller with
            this pk so return seller
        """
        seller_pk = self.kwargs.get('seller_pk')

        if seller_pk == 'me':
            seller = Seller.objects.get(user=self.request.user)
        else:
            try:
                seller_pk = int(seller_pk)
                seller = Seller.objects.get(user_id=seller_pk)
            except (ValueError, Seller.DoesNotExist):
                raise Http404

        return seller

    def get_queryset(self):
        return Address.objects.filter(seller=self.seller)
    
    def get_serializer_context(self):
        return {'seller_pk': self.seller.pk}
    

class SellerListRequestsViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'patch']
    queryset = Seller.objects.filter(status=Seller.SELLER_STATUS_WAITING)
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return serializers.SellerChangeStatusSerializer
        return serializers.SellerListRequestsSerializer
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        seller_status = serializer.validated_data.get('status')
        serializer.save()
        
        if seller_status == Seller.SELLER_STATUS_REJECTED:
            instance.delete()        
        
        return Response(serializer.data, status=status.HTTP_200_OK)
