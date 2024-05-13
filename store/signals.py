from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.contrib.auth import get_user_model


from .models import CartItem, Customer, Seller, Cart, Order, OrderItem, Product
from core.signals import superuser_created, add_user_to_staff, remove_users_from_staff

User = get_user_model()


@receiver(post_save, sender=User)
def create_customer_for_newly_created_user(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)


@receiver(superuser_created)
def create_seller_for_newly_created_superuser(sender, instance, national_code, **kwargs):
    Seller.objects.create(user=instance, company_name='Mix shop', national_code=national_code, status=Seller.SELLER_STATUS_ACCEPTED)

@receiver(pre_save, sender=Seller)
def change_type_user_when_update_seller_for_comments(sender, instance, **kwargs):
    if instance.id:
        customer_instance = instance.user.customer
        previous_instance = Seller.objects.get(id=instance.id)
        if instance.status != previous_instance.status:
            if previous_instance.status == Seller.SELLER_STATUS_ACCEPTED:
                comments = [comment for comment in instance.comments.all()]
            elif previous_instance.status == Seller.SELLER_STATUS_WAITING:
                comments = [comment for comment in customer_instance.comments.all()]

            if instance.status == Seller.SELLER_STATUS_ACCEPTED:
                for comment in comments:
                    comment.content_object = instance
                    comment.save()
            elif instance.status == Seller.SELLER_STATUS_WAITING:
                for comment in comments:
                    comment.content_object = customer_instance
                    comment.save()


@receiver(post_save, sender=Seller)
def change_type_user_after_create_seller_for_comments(sender, instance, created, **kwargs):
    if created:
        customer_instance = instance.user.customer
        comments = [comment for comment in customer_instance.comments.all()]

        if instance.status == Seller.SELLER_STATUS_ACCEPTED:
            for comment in comments:
                    comment.content_object = instance
                    comment.save()


@receiver(add_user_to_staff)
def create_seller_for_newly_staff_user(sender, instance, **kwargs):
    if not getattr(instance, 'seller', False):
        Seller.objects.create(user=instance, company_name='Mix shop', status=Seller.SELLER_STATUS_ACCEPTED)


@receiver(remove_users_from_staff)
def remove_users_from_seller(sender, queryset, **kwargs):
    for user in queryset:
        if (seller := getattr(user, 'seller', False)):
            seller.delete()


@receiver(pre_save, sender=Seller)
def change_type_user_when_update_seller_for_comment_likes(sender, instance, **kwargs):
    if instance.id:
        customer_instance = instance.user.customer
        previous_instance = Seller.objects.get(id=instance.id)
        if instance.status != previous_instance.status:
            if previous_instance.status == Seller.SELLER_STATUS_ACCEPTED:
                comment_likes = [comment_like for comment_like in instance.comment_likes.all()]
            elif previous_instance.status == Seller.SELLER_STATUS_WAITING:
                comment_likes = [comment_like for comment_like in customer_instance.comment_likes.all()]

            if instance.status == Seller.SELLER_STATUS_ACCEPTED:
                for comment_like in comment_likes:
                    comment_like.content_object = instance
                    comment_like.save()
            elif instance.status == Seller.SELLER_STATUS_WAITING:
                for comment_like in comment_likes:
                    comment_like.content_object = customer_instance
                    comment_like.save()


@receiver(post_save, sender=Seller)
def change_type_user_after_create_seller_for_comment_likes(sender, instance, created, **kwargs):
    if created:
        customer_instance = instance.user.customer
        comment_likes = [comment_like for comment_like in customer_instance.comment_likes.all()]

        if instance.status == Seller.SELLER_STATUS_ACCEPTED:
            for comment_like in comment_likes:
                    comment_like.content_object = instance
                    comment_like.save()


@receiver(pre_save, sender=Seller)
def change_type_user_when_update_seller_for_comment_dislikes(sender, instance, **kwargs):
    if instance.id:
        customer_instance = instance.user.customer
        previous_instance = Seller.objects.get(id=instance.id)
        if instance.status != previous_instance.status:
            if previous_instance.status == Seller.SELLER_STATUS_ACCEPTED:
                comment_dislikes = [comment_dislike for comment_dislike in instance.comment_dislikes.all()]
            elif previous_instance.status == Seller.SELLER_STATUS_WAITING:
                comment_dislikes = [comment_dislike for comment_dislike in customer_instance.comment_dislikes.all()]

            if instance.status == Seller.SELLER_STATUS_ACCEPTED:
                for comment_dislike in comment_dislikes:
                    comment_dislike.content_object = instance
                    comment_dislike.save()
            elif instance.status == Seller.SELLER_STATUS_WAITING:
                for comment_dislike in comment_dislikes:
                    comment_dislike.content_object = customer_instance
                    comment_dislike.save()


@receiver(post_save, sender=Seller)
def change_type_user_after_create_seller_for_comment_dislikes(sender, instance, created, **kwargs):
    if created:
        customer_instance = instance.user.customer
        comment_dislikes = [comment_like for comment_like in customer_instance.comment_dislikes.all()]

        if instance.status == Seller.SELLER_STATUS_ACCEPTED:
            for comment_like in comment_dislikes:
                    comment_like.content_object = instance
                    comment_like.save()


@receiver(post_save, sender=Seller)
def remove_seller_when_status_change_to_rejected(sender, instance, created, **kwargs):
    if not created and instance.status == Seller.SELLER_STATUS_REJECTED:
        instance.delete()


@receiver(post_save, sender=Customer)
def create_cart_for_newly_created_customer(sender, instance, created, **kwrgs):
    if created:
        Cart.objects.create(customer=instance)


@receiver(pre_save, sender=Order)
def change_price_order_items_based_on_change_status_order(sender, instance, **kwargs):
    if instance.id:
        previous_instance = Order.objects.get(id=instance.id)
        if instance.status != previous_instance.status:
            order_items = []
            if instance.status == Order.ORDER_STATUS_PAID:
                for order_item in instance.items.all():
                    order_item.price = order_item.product.price
                    order_items.append(order_item)
            else:
                for order_item in instance.items.all():
                    order_item.price = None
                    order_items.append(order_item)

            OrderItem.objects.bulk_update(order_items, fields=['price'])


@receiver(pre_save, sender=Product)
def manage_product_in_cart_items_based_on_change_product_inventory(sender, instance, **kwargs):
    if instance.id:
        previous_instance = Product.objects.get(id=instance.id)
        if instance.inventory < previous_instance.inventory:
            cart_items_queryset = CartItem.objects.filter(product=instance)
            
            for cart_item in cart_items_queryset:
                if cart_item.quantity > instance.inventory:
                    cart_item.delete()


@receiver(pre_save, sender=Product)
def manage_product_in_order_items_based_on_change_product_inventory(sender, instance, **kwargs):
    if instance.id:
        previous_instance = Product.objects.get(id=instance.id)
        if instance.inventory < previous_instance.inventory:
            order_items_queryset = OrderItem.objects.filter(product=instance, order__status__in=[Order.ORDER_STATUS_UNPAID, Order.ORDER_STATUS_CANCELED])
            
            for order_item in order_items_queryset:
                if order_item.quantity > instance.inventory:
                    order_item.delete()
