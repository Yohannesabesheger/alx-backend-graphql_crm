import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from decimal import Decimal
import re

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer

class ProductType(DjangoObjectType):
    class Meta:
        model = Product

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        if Customer.objects.filter(email=email).exists():
            raise Exception("Email already exists")
        if phone and not re.match(r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$', phone):
            raise Exception("Invalid phone format")
        customer = Customer(name=name, email=email, phone=phone)
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created successfully")
class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(graphene.JSONString, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        valid_customers = []
        errors = []

        for index, entry in enumerate(input):
            try:
                name = entry["name"]
                email = entry["email"]
                phone = entry.get("phone", None)

                if Customer.objects.filter(email=email).exists():
                    raise Exception(f"Row {index+1}: Email '{email}' already exists")
                if phone and not re.match(r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$', phone):
                    raise Exception(f"Row {index+1}: Invalid phone format")

                customer = Customer(name=name, email=email, phone=phone)
                customer.save()
                valid_customers.append(customer)

            except Exception as e:
                errors.append(str(e))

        return BulkCreateCustomers(customers=valid_customers, errors=errors)
class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids):
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID")

        if not product_ids:
            raise Exception("At least one product must be selected")

        products = []
        total = Decimal('0.00')

        for pid in product_ids:
            try:
                product = Product.objects.get(id=pid)
                products.append(product)
                total += product.price
            except Product.DoesNotExist:
                raise Exception(f"Invalid product ID: {pid}")

        order = Order(customer=customer, total_amount=total)
        order.save()
        order.products.set(products)
        return CreateOrder(order=order)
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(self, info):
        return Customer.objects.all()

    def resolve_products(self, info):
        return Product.objects.all()

    def resolve_orders(self, info):
        return Order.objects.all()
