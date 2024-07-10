from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status as status_code
from rest_framework import generics
from rest_framework import mixins
from django.http import Http404
from django.db.models import Prefetch, Case, When, Value, Sum
from django.utils.translation import gettext as _
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.conf import settings

from django_filters.rest_framework import DjangoFilterBackend
from functools import cached_property

from . import serializers
from .models import Cart, CartItem, Category, Comment, CommentLike, CommentDislike, Customer, Address, Menu, Order, OrderItem, Product, ProductImage, Seller, IncreaseWalletCredit
from .paginations import CustomLimitOffsetPagination
from .filters import CustomerFilter, OrderFilter, SellerFilter, ProductFilter, SellerMeProductFilter, OrderMeFilter, IncreaseWalletCreditFilter
from .permissions import IsCustomerOrSeller, IsSeller, IsAdminUserOrReadOnly, IsAdminUserOrSeller, IsAdminUserOrSellerOwner, IsAdminUserOrCommentOwner, IsCommentOwner, IsSellerMe, ProductImagePermission, IsCustomerInfoComplete, IsOrderOwner
from .ordering import ProductOrderingFilter
from .payment import ZarinpalSandbox


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
        customer = self.queryset.prefetch_related('addresses').get(id=user.customer.id)

        if request.method == 'GET':
            serializer = serializers.CustomerDetailSerializer(customer, context=self.get_serializer_context())
            return Response(serializer.data, status=status_code.HTTP_200_OK)
        elif request.method in ['PUT', 'PATCH']:
            partial = False
            if request.method == 'PATCH':
                partial = True
            serializer = serializers.CustomerDetailSerializer(customer, data=request.data,  partial=partial, context=self.get_serializer_context())
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status_code.HTTP_200_OK)
        

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
        return Response({'detail': _('Your request has been successfully registered.')}, status=status_code.HTTP_200_OK)


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
            return Response({'detail': _('There is some products relating this seller, Please remove them first.')}, status=status_code.HTTP_400_BAD_REQUEST)
        
        instance.delete()
        return Response(status=status_code.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['GET', 'PUT', 'PATCH', 'DELETE'], permission_classes=[IsSeller])
    def me(self, request, *args, **kwargs):
        user = request.user
        seller = self.queryset.prefetch_related('products').prefetch_related('addresses').get(id=user.seller.id)

        if request.method == 'GET':
            serializer = serializers.SellerDetailSerializer(seller, context=self.get_serializer_context())
            return Response(serializer.data, status=status_code.HTTP_200_OK)
        elif request.method in ['PUT', 'PATCH']:
            partial = False
            if request.method == 'PATCH':
                partial = True
            serializer = serializers.SellerDetailSerializer(seller, data=request.data,  partial=partial, context=self.get_serializer_context())
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status_code.HTTP_200_OK)
        elif request.method == 'DELETE':
            if seller.products.count() > 0:
                return Response({'detail': _('There is some products relating to you, Please remove them first.')}, status=status_code.HTTP_400_BAD_REQUEST)
            seller.delete()
            return Response(status=status_code.HTTP_204_NO_CONTENT)
        

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
    

class SellerMeProductViewSet(ModelViewSet):
    permission_classes = [IsSellerMe]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend, ProductOrderingFilter]
    filterset_class = SellerMeProductFilter
    ordering_fields = ['price', 'inventory', 'created_datetime', 'viewer', 'sales_count']

    def get_queryset(self):
        seller = self.request.user.seller

        queryset = Product.objects.filter(seller=seller).select_related('category').annotate(
                    sales_count=Case(When(order_items__order__status=Order.ORDER_STATUS_PAID, then=Sum('order_items__quantity')),
                                     default=Value(0))
                ).order_by('-created_datetime')

        if self.action == 'list':
            return queryset.prefetch_related(
                Prefetch('images', to_attr="product_images")
            )
        elif self.action == 'retrieve':
            return queryset.prefetch_related('images')

        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.SellerMeProductSerializer
        elif self.action == 'retrieve':
            return serializers.SellerMeProductDetailSerializer
        elif self.action == 'create':
            return serializers.ProductCreateSerializer
        return serializers.ProductUpdateSerializer


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
        
        return Response(serializer.data, status=status_code.HTTP_200_OK)


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.select_related('sub_category').order_by('-id')
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
            return Response({'detail': _('There is some products relating this category, Please remove them first.')}, status=status_code.HTTP_400_BAD_REQUEST)
        
        instance.delete()
        return Response(status=status_code.HTTP_204_NO_CONTENT)


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.select_related('seller').select_related('category').annotate(
                    sales_count=Case(When(order_items__order__status=Order.ORDER_STATUS_PAID, then=Sum('order_items__quantity')),
                                     default=Value(0))
                ).order_by('-created_datetime')
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend, ProductOrderingFilter]
    filterset_class = ProductFilter
    ordering_fields = ['price', 'inventory', 'created_datetime', 'viewer', 'sales_count']

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
        elif self.action == 'create':
            return serializers.ProductCreateSerializer
        elif self.action == 'upload_image':
            return serializers.ProductImageSerializer
        return serializers.ProductUpdateSerializer
    
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
            return Response({'detail': _('There is some order items relating this product, Please remove them first.')}, status=status_code.HTTP_400_BAD_REQUEST)
        
        instance.delete()
        return Response(status=status_code.HTTP_204_NO_CONTENT)
    
    @action(detail=False, url_path='upload-image', methods=['POST'], permission_classes=[IsAdminUserOrSeller])
    def upload_image(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status_code.HTTP_201_CREATED)
    

class CommentViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'post', 'delete', 'patch']
    pagination_class = CustomLimitOffsetPagination

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

    def get_queryset(self):
        product = self.product

        if self.action == 'list':
            queryset = Comment.objects.filter(
                product=product,
                reply_to__isnull=True,
                status=Comment.COMMENT_STATUS_APPROVED)
        else:
            queryset = Comment.objects.filter(
                    product=product,
                    status=Comment.COMMENT_STATUS_APPROVED)
        
        return queryset.select_related('content_type').prefetch_related('content_object').prefetch_related('likes').prefetch_related('dislikes').order_by('-created_datetime')
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'partial_update']:
            return serializers.CommentDetailSerializer
        return serializers.CommentSerializer
    
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
        
        return Response(serializer.data, status=status_code.HTTP_200_OK)


class ProductImageViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'post', 'delete']
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
            return Response({'detail': _("There isn't comment with id=%(comment_id)d in the %(product_title)s product.") % {'comment_id': comment_pk, 'product_title': product.title}}, status=status_code.HTTP_400_BAD_REQUEST)
        
        if comment.reply_to:
            return Response({'detail': _('A comment that is a reply cannot be liked.')}, status=status_code.HTTP_400_BAD_REQUEST)
        
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
            return Response({'detail': _('The comment like was removed.')}, status=status_code.HTTP_200_OK)
        else:
            CommentLike.objects.create(content_object=user_type, comment_id=comment_pk)

        return Response({'detail': _('The comment was successfully liked.')}, status=status_code.HTTP_201_CREATED)


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
            return Response({'detail': _("There isn't comment with id=%(comment_id)d in the %(product_title)s product.") % {'comment_id': comment_pk, 'product_title': product.title}}, status=status_code.HTTP_400_BAD_REQUEST)
        
        if comment.reply_to:
            return Response({'detail': _('A comment that is a reply cannot be disliked.')}, status=status_code.HTTP_400_BAD_REQUEST)
        
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
            return Response({'detail': _('The comment dislike was removed.')}, status=status_code.HTTP_200_OK)
        else:
            CommentDislike.objects.create(content_object=user_type, comment_id=comment_pk)

        return Response({'detail': _('The comment was successfully disliked.')}, status=status_code.HTTP_201_CREATED)


class CartViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options']
    queryset = Cart.objects.select_related('customer__user').order_by('-created_datetime')
    permission_classes = [IsAdminUser]
    pagination_class = CustomLimitOffsetPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action == 'retrieve':
            return queryset.prefetch_related(
                Prefetch('items',
                         queryset=CartItem.objects.select_related('product')
                )
            )
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.CartDetailSerializer
        return serializers.CartSerializer
    
    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        queryset = self.get_queryset().prefetch_related(
                Prefetch('items',
                         queryset=CartItem.objects.select_related('product')
                )
            )
        customer = request.user.customer
        cart = queryset.get(customer_id=customer.id)

        serializer = serializers.CartDetailSerializer(cart)
        return Response(serializer.data, status=status_code.HTTP_200_OK)


class CartItemViewset(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'post', 'patch', 'delete']

    def get_permissions(self):
        cart_pk = self.kwargs.get('cart_pk')

        if cart_pk == 'me':
            return [IsAuthenticated()]
        return [IsAdminUser()]

    @cached_property
    def cart(self):
        cart_pk = self.kwargs.get('cart_pk')

        if cart_pk == 'me':
            cart = Cart.objects.get(customer=self.request.user.customer)
        else:
            try:
                cart_pk = int(cart_pk)
                cart = Cart.objects.get(id=cart_pk)
            except (ValueError, Cart.DoesNotExist):
                raise Http404
    
        return cart
    
    def get_queryset(self):
        cart = self.cart

        return CartItem.objects.filter(cart=cart).select_related('product')

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.CartItemCreateSerializer
        elif self.action == 'partial_update':
            return serializers.CartItemUpdateSerializer
        return serializers.CartItemSerializer
    
    def get_serializer_context(self):
        return {'cart_pk': self.cart.pk}


class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'options', 'head', 'post', 'patch', 'delete']
    queryset = Order.objects.all().select_related('customer__user').order_by('-created_datetime')
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter
    pagination_class = CustomLimitOffsetPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action in ['retrieve', 'create']:
            return queryset.prefetch_related(
                Prefetch('items',
                         queryset=OrderItem.objects.select_related('product')
                )
            ).select_related('address')

        return queryset

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsCustomerInfoComplete()]
        return [IsAdminUser()]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.OrderDetailSerializer
        elif self.action == 'partial_update':
            return serializers.OrderUpdateSerializer
        return serializers.OrderSerializer
    
    def create(self, request, *args, **kwargs):
        created_order_serializer = self.get_serializer(data=request.data)
        created_order_serializer.is_valid(raise_exception=True)
        created_order = created_order_serializer.save()
        created_order = self.get_queryset().get(id=created_order.pk)

        serializer = serializers.OrderDetailSerializer(created_order)
        return Response(serializer.data, status=status_code.HTTP_201_CREATED)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        order_status = serializer.validated_data.get('status')
        serializer.save()

        order_items = []
        if order_status == Order.ORDER_STATUS_PAID:
            for order_item in instance.items.all():
                order_item.price = order_item.product.price
                order_items.append(order_item)
        else:
            for order_item in instance.items.all():
                order_item.price = None
                order_items.append(order_item)

        OrderItem.objects.bulk_update(order_items, fields=['price'])

        return Response(serializer.data, status=status_code.HTTP_200_OK)        


class OrderMeViewSet(ModelViewSet):
    http_method_names = ['get', 'options', 'head', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderMeFilter
    pagination_class = CustomLimitOffsetPagination

    def get_queryset(self):
        customer = self.request.user.customer
        queryset = Order.objects.filter(customer=customer).select_related('customer__user').order_by('-created_datetime')

        if self.action =='retrieve':
            return queryset.prefetch_related(
                Prefetch('items',
                         queryset=OrderItem.objects.select_related('product')
                )
            ).select_related('address')
        
        return queryset
    
    def get_permissions(self):
        if self.action in ['destroy', 'partial_update']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.OrderMeDetailSerializer
        elif self.action == 'partial_update':
            return serializers.OrderUpdateSerializer
        return serializers.OrderMeSerializer
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        order_status = serializer.validated_data.get('status')
        serializer.save()

        order_items = []
        if order_status == Order.ORDER_STATUS_PAID:
            for order_item in instance.items.all():
                order_item.price = order_item.product.price
                order_items.append(order_item)
        else:
            for order_item in instance.items.all():
                order_item.price = None
                order_items.append(order_item)

        OrderItem.objects.bulk_update(order_items, fields=['price'])

        return Response(serializer.data, status=status_code.HTTP_200_OK)


class ClearAllCartAPIView(APIView):

    def get_permissions(self):
        cart_pk = self.kwargs.get('cart_pk')

        if cart_pk:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def post(self, request, *args, **kwargs):
        cart_pk = self.kwargs.get('cart_pk')
        
        if cart_pk:
            cart = get_object_or_404(Cart, id=cart_pk)
        else:    
            customer = request.user.customer
            cart = Cart.objects.get(customer_id=customer.id)
        
        if cart.items.count() == 0:
            return Response({'detail': _('The cart is empty.')}, status=status_code.HTTP_400_BAD_REQUEST)

        cart.items.all().delete()
        return Response(status=status_code.HTTP_204_NO_CONTENT)


class PaymentProcessSandboxGenericAPIView(generics.GenericAPIView):
    serializer_class = serializers.OrderPaymentSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = request.user.customer
        payment_method = serializer.validated_data.get('payment_method')
        order_id = serializer.validated_data.get('order_id')

        order = get_object_or_404(Order, id=order_id, customer_id=customer.id, status=Order.ORDER_STATUS_UNPAID)

        rial_total_price = order.get_total_price()

        if payment_method == Order.ORDER_PAYMENT_METHOD_ONLINE:
            zarinpal_sandbox = ZarinpalSandbox(settings.ZARINPAL_MERCHANT_ID)
            data = zarinpal_sandbox.payment_request(
                rial_total_price=rial_total_price, 
                description=f'#{order.id}: {customer.full_name}',
                callback_url=request.build_absolute_uri(reverse('store:payment-callback-sandbox'))
            )

            authority = data['Authority']
            
            order.zarinpal_authority = authority
            order.save(update_fields=['zarinpal_authority'])

            if 'errors' not in data or len(data['errors']) == 0:
                return redirect(zarinpal_sandbox.generate_payment_page_url(authority=authority))
            else:
                return Response({'detail': _('Error from zarinpal.')}, status=status_code.HTTP_400_BAD_REQUEST)
        else:
            if customer.wallet_amount < rial_total_price:
                return Response({'detail': _('Your wallet balance is not enough.')}, status=status_code.HTTP_400_BAD_REQUEST)
            
            order.status = Order.ORDER_STATUS_PAID
            order.payment_method = Order.ORDER_PAYMENT_METHOD_WALLET
            order.save(update_fields=['status', 'payment_method'])

            return Response({'detail': _('Your payment has been successfully complete.')}, status=status_code.HTTP_200_OK) 


class PaymentCallbackSandboxAPIView(APIView):

    def get(self, request, *args, **kwargs):
        status = request.query_params.get('Status')
        authority = request.query_params.get('Authority')

        order = get_object_or_404(Order, zarinpal_authority=authority)

        if status == 'OK':
            zarinpal_sandbox = ZarinpalSandbox(settings.ZARINPAL_MERCHANT_ID)
            data = zarinpal_sandbox.payment_verify(
                rial_total_price=order.get_total_price(), 
                authority=authority
            )
            
            payment_status = data['Status']

            if payment_status == 100:
                order.status = Order.ORDER_STATUS_PAID
                order.zarinpal_ref_id = data['RefID']
                order.save(update_fields=['status', 'zarinpal_ref_id'])

                return Response({'detail': _('Your payment has been successfully complete.')}, status=status_code.HTTP_200_OK)
            elif payment_status == 101:
                return Response({'detail': _('Your payment has been successfully complete and has already been register.')}, status=status_code.HTTP_200_OK)
            else:
                return Response({'detail': _('The payment was unsuccessful.')}, status=status_code.HTTP_400_BAD_REQUEST)
        else:
            return Response({'detail': _('The payment was unsuccessful.')}, status=status_code.HTTP_400_BAD_REQUEST)


class IncreaseWalletCreditViewSet(mixins.ListModelMixin,
                                  mixins.CreateModelMixin,
                                  GenericViewSet):
    queryset = IncreaseWalletCredit.objects.select_related('customer__user').order_by('-created_datetime')
    filter_backends = [DjangoFilterBackend]
    filterset_class = IncreaseWalletCreditFilter
    pagination_class = CustomLimitOffsetPagination
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        return [IsAdminUser()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.IncreaseWalletCreditCreateSerializer
        return serializers.IncreaseWalletCreditSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        increase_wallet_credit = serializer.save()

        customer = request.user.customer

        zarinpal_sandbox = ZarinpalSandbox(settings.ZARINPAL_MERCHANT_ID)
        data = zarinpal_sandbox.payment_request(
            rial_total_price=increase_wallet_credit.amount, 
            description=f'#{increase_wallet_credit.id}: {customer.full_name if customer.full_name else customer.user.phone}',
            callback_url=request.build_absolute_uri(reverse('store:wallet-credit-callback'))
        )

        authority = data['Authority']
        
        increase_wallet_credit.zarinpal_authority = authority
        increase_wallet_credit.save(update_fields=['zarinpal_authority'])

        if 'errors' not in data or len(data['errors']) == 0:
            return redirect(zarinpal_sandbox.generate_payment_page_url(authority=authority))
        else:

            return Response({'detail': _('Error from zarinpal.')}, status=status_code.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def callback(self, request, *args, **kwargs):
        status = request.query_params.get('Status')
        authority = request.query_params.get('Authority')

        increase_wallet_credit = get_object_or_404(IncreaseWalletCredit, zarinpal_authority=authority)

        if status == 'OK':
            zarinpal_sandbox = ZarinpalSandbox(settings.ZARINPAL_MERCHANT_ID)
            data = zarinpal_sandbox.payment_verify(
                rial_total_price=increase_wallet_credit.amount, 
                authority=authority
            )
            
            payment_status = data['Status']

            if payment_status == 100:
                increase_wallet_credit.is_paid = True
                increase_wallet_credit.zarinpal_ref_id = data['RefID']
                increase_wallet_credit.save(update_fields=['is_paid', 'zarinpal_ref_id'])

                return Response({'detail': _('Your payment has been successfully complete.')}, status=status_code.HTTP_200_OK)
            elif payment_status == 101:
                return Response({'detail': _('Your payment has been successfully complete and has already been register.')}, status=status_code.HTTP_200_OK)
            else:
                increase_wallet_credit.delete()
                return Response({'detail': _('The payment was unsuccessful.')}, status=status_code.HTTP_400_BAD_REQUEST)
        else:
            increase_wallet_credit.delete()
            return Response({'detail': _('The payment was unsuccessful.')}, status=status_code.HTTP_400_BAD_REQUEST)


class MenuViewset(mixins.CreateModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    queryset = Menu.objects.all().order_by('-id')
    permission_classes = [IsAdminUserOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if self.action == 'list':
            max_depth = 0
            for menu in queryset:
                depth = menu.level
                if depth > max_depth:
                    max_depth = depth
        
            return queryset.filter(sub_menu__isnull=True).prefetch_related(
                '__'.join(['sub_menus' for _ in range(max_depth + 1)])
            )
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.MenuSerializer
        return serializers.MenuCreateSerializer
