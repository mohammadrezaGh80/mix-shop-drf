from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory
from django.db.models import signals

import random
import string
import factory
from datetime import datetime, timedelta
from faker import Faker

from . import models

User = get_user_model()
faker = Faker()


class AddressFactory(DjangoModelFactory):
    class Meta:
        model = models.Address
    
    province = factory.Faker('word')
    city = factory.Faker('city')
    plaque = factory.LazyFunction(lambda: random.randint(1, 32767))
    postal_code = factory.LazyFunction(lambda: random.randint(1000000000, 9999999999))


@factory.django.mute_signals(signals.post_save)
class CustomUserFactory(DjangoModelFactory):
    class Meta:
        model = User

    phone = factory.Sequence(lambda n: '09%09d' % n)
    email = factory.Sequence(lambda n: '%s%d@gmail.com' %(faker.first_name(), n))
    password = factory.PostGenerationMethodCall('set_password', faker.password())
    
    @classmethod
    def _setup_next_sequence(cls):
        try:
            user = User.objects.latest("phone")
            return int(user.phone[2:]) + 1
        except User.DoesNotExist:
            return 1
   
    
@factory.django.mute_signals(signals.post_save)
class CustomerFactory(DjangoModelFactory):
    class Meta:
        model = models.Customer
    
    user = factory.SubFactory(CustomUserFactory)
    first_name = factory.LazyAttribute(lambda o: o.user.email.split('@')[0].strip(string.digits))
    last_name = factory.Faker("last_name")
    birth_date = factory.LazyFunction(lambda: faker.date_time_ad(start_datetime=datetime(1980, 1, 1), end_datetime=datetime(2014, 1, 1)))
    gender = factory.LazyFunction(lambda: random.choice([models.Customer.PERSON_GENDER_MALE, models.Customer.PERSON_GENDER_FEMALE]))
    wallet_amount = factory.LazyFunction(lambda: random.randint(100, 99999900) * 10)


@factory.django.mute_signals(signals.post_save, signals.pre_save)
class SellerFactory(DjangoModelFactory):
    class Meta:
        model = models.Seller

    user = factory.SubFactory(CustomUserFactory)
    first_name = factory.LazyAttribute(lambda o: o.user.email.split('@')[0].strip(string.digits))
    company_name = factory.LazyFunction(lambda: faker.sentence(nb_words=3, variable_nb_words=True)[:-1])
    last_name = factory.Faker("last_name")
    birth_date = factory.LazyFunction(lambda: faker.date_time_ad(start_datetime=datetime(1980, 1, 1), end_datetime=datetime(2014, 1, 1)))
    gender = factory.LazyFunction(lambda: random.choice([models.Customer.PERSON_GENDER_MALE, models.Customer.PERSON_GENDER_FEMALE]))
    national_code = factory.Sequence(lambda n: "1%09d" % n)
    
    @classmethod
    def _setup_next_sequence(cls):
        try:
            seller = models.Seller.objects.latest("id")
            return int(seller.national_code) + 1
        except models.Seller.DoesNotExist:
            return 0


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = models.Category
    
    title = factory.LazyFunction(lambda: faker.sentence(nb_words=3, variable_nb_words=True)[:-1])

class ProductFactory(DjangoModelFactory):
    class Meta:
        model = models.Product
    
    title = factory.LazyFunction(lambda: ' '.join([x.capitalize() for x in faker.words(4)]))
    slug = factory.LazyAttribute(lambda obj: '-'.join(obj.title.split(' ')).lower())
    description = factory.Faker(
        'paragraph',
        nb_sentences=5,
        variable_nb_sentences=True
    )
    price = factory.LazyFunction(lambda: random.randint(100, 99999900) * 10)
    inventory = factory.LazyFunction(lambda: random.randint(1, 100))


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = models.Comment
    
    title = factory.Faker(
        'sentence',
        nb_words=5,
        variable_nb_words=True
    )
    body = factory.Faker(
        'paragraph',
        nb_sentences=3,
        variable_nb_sentences=True
    )
    status = factory.LazyFunction(lambda: random.choice([models.Comment.COMMENT_STATUS_WAITING, models.Comment.COMMENT_STATUS_APPROVED, models.Comment.COMMENT_STATUS_NOT_APPROVED]))
    rating = factory.LazyFunction(
        lambda: random.choice([models.Comment.COMMENT_RATING_VERY_BAD, models.Comment.COMMENT_RATING_BAD, models.Comment.COMMENT_RATING_NORMAL, 
                               models.Comment.COMMENT_RATING_GOOD, models.Comment.COMMENT_RATING_EXCELLENT]))


class CartFactory(DjangoModelFactory):
    class Meta:
        model = models.Cart


class CartItemFactory(DjangoModelFactory):
    class Meta:
        model = models.CartItem
    

class OrderFactory(DjangoModelFactory):
    class Meta:
        model = models.Order
    
    status = factory.LazyFunction(lambda: random.choice([models.Order.ORDER_STATUS_CANCELED, models.Order.ORDER_STATUS_PAID]))
    delivery_date = factory.LazyAttribute(lambda obj: obj.created_datetime.date() + timedelta(days=random.choice([3, 4, 5])))


class OrderItemFactory(DjangoModelFactory):
    class Meta:
        model = models.OrderItem
    
    quantity = factory.LazyFunction(lambda: random.randint(1, 20))
