from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.contrib.auth import get_user_model


from .models import Customer, Seller
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
def change_user_type_user_for_comments(sender, instance, **kwargs):
    if instance.id:
        previous_instance = Seller.objects.get(id=instance.id)
        customer_instance = instance.user.customer
        if instance.status != previous_instance.status:
            if previous_instance.status == Seller.SELLER_STATUS_ACCEPTED:
                comments = [comment for comment in instance.comments.all()]
            else:
                comments = [comment for comment in customer_instance.comments.all()]

            if instance.status == Seller.SELLER_STATUS_ACCEPTED:
                for comment in comments:
                    comment.content_object = instance
                    comment.save()
            else:
                for comment in comments:
                    comment.content_object = customer_instance
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
