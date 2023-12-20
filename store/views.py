from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404

from django_filters.rest_framework import DjangoFilterBackend
from functools import cached_property

from . import serializers
from .models import Customer, Address
from .paginations import CustomLimitOffsetPagination
from .filters import CustomerFilter


class CustomerViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'put', 'patch']
    queryset = Customer.objects.all().select_related('user').prefetch_related('addresses')
    permission_classes = [IsAdminUser]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomerFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.CustomerSerializer
        elif self.action == 'create':
            return serializers.CustomerCreateSerializer
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
        

class AddressViewSet(ModelViewSet):
    serializer_class = serializers.AddressSerializer

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
    