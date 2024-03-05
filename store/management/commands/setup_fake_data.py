from django.core.management import BaseCommand
from django.db import transaction

import random
from faker import Faker
from datetime import datetime, timedelta
from datetime import timezone

from store.models import Address, Customer, Category, Product, Comment, Seller, Cart, CartItem, Order, OrderItem
from store.factories import (
    AddressFactory,
    CustomerFactory,
    SellerFactory,
    CategoryFactory,
    ProductFactory,
    CommentFactory,
    CartFactory,
    CartItemFactory,
    OrderFactory,
    OrderItemFactory
)

faker = Faker()

list_of_models = [Address, Customer, Seller, Category, Product, Comment, Cart, CartItem, Order, OrderItem]

NUM_CUSTOMERS = 40
NUM_SELLERS = 10
NUM_CATEGORIES = 50
NUM_PRODUCTS = 1000
NUM_CARTS = 100
NUM_ORDERS = 30


class Command(BaseCommand):
    help = "Generate fake data"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Deleting old data...")
        
        models = list_of_models
        for model in models:
            model.objects.all().delete()
        
        self.stdout.write("Creating new data...\n")

        # categories data
        print(f"Adding {NUM_CATEGORIES} categories...", end='')
        all_categories = [CategoryFactory() for _ in range(NUM_CATEGORIES)]
        print("DONE")

        # customers data
        print(f"Adding {NUM_CUSTOMERS} customers...", end='')
        all_customers = list([CustomerFactory() if random.random() > 0.3 else CustomerFactory(birth_date=None) for _ in range(NUM_CUSTOMERS)])
        print("DONE")

        # sellers data
        print(f"Adding {NUM_SELLERS} sellers...", end='')
        all_sellers = list()
        for _ in range(NUM_SELLERS):
            seller = SellerFactory() if random.random() > 0.3 else SellerFactory(birth_date=None)
            customer = CustomerFactory(
                user=seller.user,
                first_name=seller.first_name,
                last_name=seller.last_name,
                gender=seller.gender,
                birth_date=seller.birth_date
            )
            seller.status = Seller.SELLER_STATUS_ACCEPTED
            seller.save()
            
            all_customers.append(customer)
            all_sellers.append(seller)

        print("DONE")

        # addresses data
        print(f"Adding addresses...", end='')
        all_addresses = list()
        all_person = all_customers + all_sellers

        for person in all_person:
            for _ in range(random.randint(0, 3)):
                address = AddressFactory(
                    content_object=person
                )
                all_addresses.append(address)

        print("DONE")

        # products data
        print(f"Adding {NUM_PRODUCTS} products...", end='')
        all_products = list()

        for _ in range(NUM_PRODUCTS):
            product = ProductFactory(
                category_id=random.choice(all_categories).id, 
                seller_id=random.choice(all_sellers).id
            )
            product.created_datetime = datetime(year=random.randrange(2019, 2023), month=random.randint(1,12),day=random.randint(1,28), tzinfo=timezone.utc)
            product.modified_datetime = product.created_datetime + timedelta(hours=random.randint(1, 500))
            product.save()
            all_products.append(product)

        print("DONE")

        # comments data
        print(f"Adding comments...", end='')
        for product in all_products:
            for _ in range(random.randint(0, 5)):
                comment = CommentFactory(
                    content_object = random.choice(all_customers),
                    product_id = product.id
                )
                comment.created_datetime = datetime(year=random.randrange(2019, 2023), month=random.randint(1,12),day=random.randint(1,28), tzinfo=timezone.utc)
                comment.modified_datetime = comment.created_datetime + timedelta(hours=random.randint(1, 500))
                comment.save()
        
        print("DONE")

        # carts data
        print(f"Adding {NUM_CARTS} carts...", end='')
        all_carts = list()
        for _ in range(NUM_CARTS):
            cart = CartFactory()
            cart.created_datetime = datetime(year=random.randrange(2019, 2023), month=random.randint(1,12), day=random.randint(1,28), tzinfo=timezone.utc)
            cart.modified_datetime = cart.created_datetime + timedelta(hours=random.randint(1, 500))
            cart.save()
            all_carts.append(cart)
        
        print("DONE")

        # cart items data
        print(f"Adding cart items...", end='')
        for cart in all_carts:
            products = random.sample(all_products, random.randint(1, 10))
            for product in products:
                CartItemFactory(
                    cart_id=cart.id,
                    product_id = product.id
                )

        print("DONE")

        # orders data
        print(f"Adding {NUM_ORDERS} orders...", end='')
        all_orders = list()

        for _ in range(NUM_ORDERS):
            order = OrderFactory(
                customer_id=random.choice(all_customers).id
            )
            order.created_datetime = datetime(year=random.randrange(2019, 2023), month=random.randint(1,12), day=random.randint(1,28), tzinfo=timezone.utc)
            order.modified_datetime = order.created_datetime + timedelta(hours=random.randint(1, 500))
            order.save()
            all_orders.append(order)
        
        print("DONE")

        # order items data
        print(f"Adding order items...", end='')
        for order in all_orders:
            products = random.sample(all_products, random.randint(1, 10))
            for product in products:
                OrderItemFactory(
                    order_id=order.id,
                    product_id=product.id,
                    price=product.price,
                )
        
        print("DONE")
