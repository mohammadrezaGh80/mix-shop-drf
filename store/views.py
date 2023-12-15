from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from django_filters.rest_framework import DjangoFilterBackend

from . import serializers
from .models import Customer
from .paginations import CustomLimitOffsetPagination
from .filters import CustomerFilter


class CustomerViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'put', 'patch']
    queryset = Customer.objects.all().select_related('user')
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
        customer = user.customer

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

    