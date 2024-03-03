from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.conf import settings

from .models import Customer, Seller
from core.signals import superuser_created


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
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

