from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings

from .models import Customer, Seller
from core.signals import superuser_created


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_for_newly_created_user(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)


@receiver(superuser_created)
def create_seller_for_newly_created_superuser(sender, instance, **kwargs):
    Seller.objects.create(user=instance, status=Seller.SELLER_STATUS_ACCEPTED)
