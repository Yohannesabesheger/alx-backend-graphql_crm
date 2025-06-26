from crm.models import Customer, Product
Customer.objects.create(name="John Doe", email="john@example.com", phone="+1234567890")
Product.objects.create(name="Keyboard", price=99.99, stock=5)
Product.objects.create(name="Mouse", price=49.99, stock=10)