from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from rest_framework import generics
from django.db.models import Prefetch
from django.utils.translation import gettext as _
from rest_framework.views import APIView

from django_filters.rest_framework import DjangoFilterBackend
from functools import cached_property

from . import serializers
from .models import Category, Comment, CommentLike, CommentDislike, Customer, Address, Product, ProductImage, Seller
from .paginations import CustomLimitOffsetPagination
from .filters import CustomerFilter, SellerFilter, ProductFilter
from .permissions import IsCustomerOrSeller, IsSeller, IsAdminUserOrReadOnly, IsAdminUserOrSeller, IsAdminUserOrSellerOwner, IsAdminUserOrCommentOwner, IsCommentOwner, ProductImagePermission
from .ordering import ProductOrderingFilter


class CustomerViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'put', 'patch']
    queryset = Customer.objects.all().select_related('user').order_by('-id')
    permission_classes = [IsAdminUser]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomerFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.CustomerSerializer
        return serializers.CustomerDetailSerializer 

    def get_queryset(self):
        queryset = super().get_queryset()  

        if self.action =='retrieve':
            return queryset.prefetch_related('addresses')
        return queryset
    
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
                customer = Customer.objects.get(id=customer_pk)
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
    queryset = Seller.objects.all().select_related('user').order_by('-id')
    permission_classes = [IsAdminUser]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = SellerFilter

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action =='retrieve':
            return queryset.prefetch_related('products').prefetch_related('addresses')
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.SellerSerializer
        elif self.action == 'create':
            return serializers.SellerCreateSerializer
        return serializers.SellerDetailSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.products.count() > 0:
            return Response({'detail': _('There is some products relating this seller, Please remove them first.')}, status=status.HTTP_400_BAD_REQUEST)
        
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['GET', 'PUT', 'PATCH', 'DELETE'], permission_classes=[IsSeller])
    def me(self, request, *args, **kwargs):
        user = request.user
        seller = self.queryset.prefetch_related('products').prefetch_related('addresses').get(id=user.seller.id)

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
            if seller.products.count() > 0:
                return Response({'detail': _('There is some products relating to you, Please remove them first.')}, status=status.HTTP_400_BAD_REQUEST)
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
                seller = Seller.objects.get(id=seller_pk)
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


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.select_related('sub_category').order_by("-id")
    permission_classes = [IsAdminUserOrReadOnly]
    pagination_class = CustomLimitOffsetPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action == 'retrieve':
            queryset.prefetch_related('products')
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.CategoryDetailSerializer
        return serializers.CategorySerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.get_products_count_of_category() > 0:
            return Response({'detail': _('There is some products relating this category, Please remove them first.')}, status=status.HTTP_400_BAD_REQUEST)
        
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.select_related('seller').select_related('category').order_by('-created_datetime')
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend, ProductOrderingFilter]
    filterset_class = ProductFilter
    ordering_fields = ['price', 'inventory', 'created_datetime', 'viewer']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        if self.action == 'list':
            return queryset.prefetch_related(
                Prefetch('images', to_attr="product_images")
            )
        elif self.action == 'retrieve':
            return queryset.prefetch_related(
                Prefetch('comments',
                queryset=Comment.objects.prefetch_related('content_object').select_related('content_type').prefetch_related('likes').prefetch_related('dislikes').filter(status=Comment.COMMENT_STATUS_APPROVED, reply_to__isnull=True))
            ).prefetch_related('images')
            
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.ProductSerializer
        elif self.action == 'retrieve':
            return serializers.ProductDetailSerializer
        elif self.action == 'upload_image':
            return serializers.ProductImageSerializer
        return serializers.ProductCreateSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAdminUserOrSeller()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminUserOrSellerOwner()]
        return super().get_permissions()
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.viewer += 1
        instance.save(update_fields=['viewer'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.order_items.count() > 0:
            return Response({'detail': _('There is some order items relating this product, Please remove them first.')}, status=status.HTTP_400_BAD_REQUEST)
        
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, url_path='upload-image', methods=['POST'], permission_classes=[IsAdminUserOrSeller])
    def upload_image(self, request, *args, **kwargs):
        serializer = serializers.ProductImageSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class CommentViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'post', 'delete', 'patch']
    pagination_class = CustomLimitOffsetPagination

    def get_queryset(self):
        product_pk = self.kwargs.get('product_pk')

        if self.action == 'list':
            try:
                queryset = Comment.objects.filter(
                    product_id=product_pk,
                    reply_to__isnull=True,
                    status=Comment.COMMENT_STATUS_APPROVED)
            except ValueError:
                raise Http404
        else:
            queryset = Comment.objects.filter(
                    product_id=product_pk,
                    status=Comment.COMMENT_STATUS_APPROVED)
        
        return queryset.select_related('content_type').prefetch_related('content_object').prefetch_related('likes').prefetch_related('dislikes').order_by('-created_datetime')
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'partial_update']:
            return serializers.CommentDetailSerializer
        return serializers.CommentSerializer
    
    @cached_property
    def product(self):
        product_pk = self.kwargs.get('product_pk')
        try:
            product_pk = int(product_pk)
            product = Product.objects.get(id=product_pk)
        except (ValueError, Product.DoesNotExist):
            raise Http404
        else:
            return product
    
    def get_serializer_context(self):
        product = self.product
        
        if self.action == 'create':
            user = self.request.user
            if getattr(user, 'seller', False) and user.seller.status == Seller.SELLER_STATUS_ACCEPTED:
                user_type = user.seller
            else:
                user_type = user.customer
            return {'product': product,
                    'user': user_type}
        return super().get_serializer_context()
    
    def get_permissions(self):
        if self.action in ['retrieve', 'destroy']:
            return [IsAdminUserOrCommentOwner()]
        elif self.action == 'partial_update':
            return [IsCommentOwner()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        return super().get_permissions()
    

class CommentListWaitingViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'patch']
    queryset = Comment.objects.prefetch_related('content_object').select_related('content_type').select_related('product').filter(status=Comment.COMMENT_STATUS_WAITING).order_by('-created_datetime')
    permission_classes = [IsAdminUser]
    pagination_class = CustomLimitOffsetPagination

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return serializers.CommentChangeStatusSerializer
        return serializers.CommentListWaitingSerializer
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        comment_status = serializer.validated_data.get('status')
        serializer.save()
        
        if comment_status == Comment.COMMENT_STATUS_NOT_APPROVED:
            instance.delete()        
        
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductImageViewSet(ModelViewSet):
    serializer_class = serializers.ProductImageSerializer
    permission_classes = [ProductImagePermission]

    def get_queryset(self):
        product_pk = self.kwargs.get('product_pk')
        return ProductImage.objects.filter(product_id=product_pk)
    
    def get_serializer_context(self):
        return {'request': self.request, 'product_pk': self.kwargs.get('product_pk')}
    

class CommentLikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        product_pk = self.kwargs.get('product_pk')
        comment_pk = self.kwargs.get('comment_pk')

        try:
            product = Product.objects.get(id=product_pk)
        except Product.DoesNotExist:
            raise Http404
        
        try:
            comment = Comment.objects.get(id=comment_pk, product_id=product_pk)
        except Comment.DoesNotExist:
            return Response({'detail': _("There isn't comment with id=%(comment_id)d in the %(product_title)s product.") % {'comment_id': comment_pk, 'product_title': product.title}}, status=status.HTTP_400_BAD_REQUEST)
        
        if comment.reply_to:
            return Response({'detail': _('A comment that is a reply cannot be liked.')}, status=status.HTTP_400_BAD_REQUEST)
        
        user = self.request.user
        if getattr(user, 'seller', False) and user.seller.status == Seller.SELLER_STATUS_ACCEPTED:
            user_type = user.seller
            queryset = CommentLike.objects.filter(
                seller=user_type, comment_id=comment_pk
            )
        else:
            user_type = user.customer
            queryset = CommentLike.objects.filter(
                customer=user_type, comment_id=comment_pk
            )

        if queryset.exists():
            queryset.first().delete()
            return Response({'detail': _('The comment like was removed.')}, status=status.HTTP_200_OK)
        else:
            CommentLike.objects.create(content_object=user_type, comment_id=comment_pk)

        return Response({'detail': _('The comment was successfully liked.')}, status=status.HTTP_201_CREATED)


class CommentDisLikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        product_pk = self.kwargs.get('product_pk')
        comment_pk = self.kwargs.get('comment_pk')

        try:
            product = Product.objects.get(id=product_pk)
        except Product.DoesNotExist:
            raise Http404
        
        try:
            comment = Comment.objects.get(id=comment_pk, product_id=product_pk)
        except Comment.DoesNotExist:
            return Response({'detail': _("There isn't comment with id=%(comment_id)d in the %(product_title)s product.") % {'comment_id': comment_pk, 'product_title': product.title}}, status=status.HTTP_400_BAD_REQUEST)
        
        if comment.reply_to:
            return Response({'detail': _('A comment that is a reply cannot be disliked.')}, status=status.HTTP_400_BAD_REQUEST)
        
        user = self.request.user
        if getattr(user, 'seller', False) and user.seller.status == Seller.SELLER_STATUS_ACCEPTED:
            user_type = user.seller
            queryset = CommentDislike.objects.filter(
                seller=user_type, comment_id=comment_pk
            )
        else:
            user_type = user.customer
            queryset = CommentDislike.objects.filter(
                customer=user_type, comment_id=comment_pk
            )

        if queryset.exists():
            queryset.first().delete()
            return Response({'detail': _('The comment dislike was removed.')}, status=status.HTTP_200_OK)
        else:
            CommentDislike.objects.create(content_object=user_type, comment_id=comment_pk)

        return Response({'detail': _('The comment was successfully disliked.')}, status=status.HTTP_201_CREATED)

