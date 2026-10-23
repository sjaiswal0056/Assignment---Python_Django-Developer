from decimal import Decimal
from django.core.management.base import BaseCommand
from boxes.models import Box
from products.models import Product
from orders.models import Order, OrderItem
from recommendations.services.box_selector import BoxSelector
from recommendations.models import BoxRecommendation


class Command(BaseCommand):
    help = "Seeds database with realistic ecommerce boxes, products, and sample orders."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding warehouse shipping boxes..."))

        boxes_data = [
            {
                'code': 'BOX-XS',
                'name': 'Extra Small Padded Mailer',
                'length': Decimal('15.00'),
                'width': Decimal('10.00'),
                'height': Decimal('5.00'),
                'max_weight': Decimal('1.00'),
                'cost': Decimal('0.75'),
                'empty_weight': Decimal('0.05'),
            },
            {
                'code': 'BOX-FLAT',
                'name': 'Slim Book & Document Box',
                'length': Decimal('35.00'),
                'width': Decimal('26.00'),
                'height': Decimal('6.00'),
                'max_weight': Decimal('3.00'),
                'cost': Decimal('1.10'),
                'empty_weight': Decimal('0.10'),
            },
            {
                'code': 'BOX-S',
                'name': 'Small Standard Box',
                'length': Decimal('25.00'),
                'width': Decimal('20.00'),
                'height': Decimal('12.00'),
                'max_weight': Decimal('4.00'),
                'cost': Decimal('1.40'),
                'empty_weight': Decimal('0.15'),
            },
            {
                'code': 'BOX-M',
                'name': 'Medium Parcel Box',
                'length': Decimal('35.00'),
                'width': Decimal('28.00'),
                'height': Decimal('18.00'),
                'max_weight': Decimal('8.00'),
                'cost': Decimal('2.60'),
                'empty_weight': Decimal('0.25'),
            },
            {
                'code': 'BOX-LONG',
                'name': 'Long Cylindrical / Tube Box',
                'length': Decimal('80.00'),
                'width': Decimal('15.00'),
                'height': Decimal('15.00'),
                'max_weight': Decimal('6.00'),
                'cost': Decimal('3.20'),
                'empty_weight': Decimal('0.30'),
            },
            {
                'code': 'BOX-L',
                'name': 'Large Storage Box',
                'length': Decimal('48.00'),
                'width': Decimal('36.00'),
                'height': Decimal('25.00'),
                'max_weight': Decimal('15.00'),
                'cost': Decimal('4.50'),
                'empty_weight': Decimal('0.40'),
            },
            {
                'code': 'BOX-XL',
                'name': 'Extra Large Heavy Duty Crate',
                'length': Decimal('60.00'),
                'width': Decimal('45.00'),
                'height': Decimal('35.00'),
                'max_weight': Decimal('25.00'),
                'cost': Decimal('7.80'),
                'empty_weight': Decimal('0.65'),
            },
        ]

        created_boxes = {}
        for b in boxes_data:
            box, created = Box.objects.update_or_create(
                code=b['code'],
                defaults=b
            )
            created_boxes[b['code']] = box
            status_text = "Created" if created else "Updated"
            self.stdout.write(f"  [{status_text}] {box.name} ({box.code})")

        self.stdout.write(self.style.NOTICE("\nSeeding ecommerce products..."))

        products_data = [
            {
                'sku': 'SKU-BOOK-01',
                'name': 'Python Programming Handbook',
                'category': 'Books',
                'length': Decimal('24.00'),
                'width': Decimal('17.00'),
                'height': Decimal('3.50'),
                'weight': Decimal('0.85'),
            },
            {
                'sku': 'SKU-MUG-01',
                'name': 'Ceramic Coffee Mug',
                'category': 'Kitchenware',
                'length': Decimal('12.00'),
                'width': Decimal('10.00'),
                'height': Decimal('11.00'),
                'weight': Decimal('0.40'),
                'is_fragile': True,
            },
            {
                'sku': 'SKU-HEADPHONE-01',
                'name': 'Studio Wireless Headphones',
                'category': 'Electronics',
                'length': Decimal('20.00'),
                'width': Decimal('18.00'),
                'height': Decimal('8.00'),
                'weight': Decimal('0.35'),
            },
            {
                'sku': 'SKU-LAPTOP-01',
                'name': 'Ultrabook 15-inch Laptop',
                'category': 'Electronics',
                'length': Decimal('36.00'),
                'width': Decimal('25.00'),
                'height': Decimal('4.00'),
                'weight': Decimal('2.10'),
                'is_fragile': True,
            },
            {
                'sku': 'SKU-SHOES-01',
                'name': 'Air Cushion Running Shoes',
                'category': 'Footwear',
                'length': Decimal('32.00'),
                'width': Decimal('21.00'),
                'height': Decimal('12.00'),
                'weight': Decimal('1.10'),
            },
            {
                'sku': 'SKU-KEYBOARD-01',
                'name': 'RGB Mechanical Gaming Keyboard',
                'category': 'Electronics',
                'length': Decimal('44.00'),
                'width': Decimal('14.00'),
                'height': Decimal('4.50'),
                'weight': Decimal('1.15'),
            },
            {
                'sku': 'SKU-KETTLE-01',
                'name': 'Electric Stainless Steel Kettle',
                'category': 'Home Appliances',
                'length': Decimal('22.00'),
                'width': Decimal('19.00'),
                'height': Decimal('24.00'),
                'weight': Decimal('1.30'),
            },
            {
                'sku': 'SKU-POSTER-01',
                'name': 'Framed Architectural Art Print',
                'category': 'Art',
                'length': Decimal('75.00'),
                'width': Decimal('10.00'),
                'height': Decimal('10.00'),
                'weight': Decimal('0.45'),
            },
            {
                'sku': 'SKU-DUMBBELL-01',
                'name': 'Cast Iron Dumbbell 10kg',
                'category': 'Fitness',
                'length': Decimal('25.00'),
                'width': Decimal('12.00'),
                'height': Decimal('12.00'),
                'weight': Decimal('10.00'),
            },
            {
                'sku': 'SKU-OVERSIZE-01',
                'name': 'Carbon Fiber Kayak Paddle',
                'category': 'Outdoors',
                'length': Decimal('125.00'),
                'width': Decimal('22.00'),
                'height': Decimal('8.00'),
                'weight': Decimal('1.80'),
            },
        ]

        created_products = {}
        for p in products_data:
            prod, created = Product.objects.update_or_create(
                sku=p['sku'],
                defaults=p
            )
            created_products[p['sku']] = prod
            status_text = "Created" if created else "Updated"
            self.stdout.write(f"  [{status_text}] {prod.name} ({prod.sku})")

        self.stdout.write(self.style.NOTICE("\nSeeding realistic test orders..."))

        sample_orders = [
            {
                'order_number': 'ORD-101',
                'customer_name': 'Alice Johnson',
                'customer_email': 'alice@example.com',
                'shipping_address': '742 Evergreen Terrace, Springfield',
                'items': [
                    ('SKU-BOOK-01', 1),
                ],
            },
            {
                'order_number': 'ORD-102',
                'customer_name': 'Bob Smith',
                'customer_email': 'bob@example.com',
                'shipping_address': '221B Baker Street, London',
                'items': [
                    ('SKU-MUG-01', 2),
                    ('SKU-HEADPHONE-01', 1),
                ],
            },
            {
                'order_number': 'ORD-103',
                'customer_name': 'Charlie Brown',
                'customer_email': 'charlie@example.com',
                'shipping_address': '10 Downing St, Westminster',
                'items': [
                    ('SKU-SHOES-01', 1),
                    ('SKU-KEYBOARD-01', 1),
                    ('SKU-BOOK-01', 1),
                ],
            },
            {
                'order_number': 'ORD-104',
                'customer_name': 'Diana Prince',
                'customer_email': 'diana@example.com',
                'shipping_address': '432 Park Ave, New York, NY',
                'items': [
                    ('SKU-POSTER-01', 1),
                ],
            },
            {
                'order_number': 'ORD-105',
                'customer_name': 'Evan Wright',
                'customer_email': 'evan@example.com',
                'shipping_address': '1600 Amphitheatre Pkwy, Mountain View, CA',
                'items': [
                    ('SKU-DUMBBELL-01', 2),
                    ('SKU-SHOES-01', 1),
                ],
            },
            {
                'order_number': 'ORD-106',
                'customer_name': 'Fiona Gallagher',
                'customer_email': 'fiona@example.com',
                'shipping_address': '21 Jump Street, Chicago, IL',
                'items': [
                    ('SKU-OVERSIZE-01', 1),
                ],
            },
        ]

        for ord_data in sample_orders:
            order, created = Order.objects.update_or_create(
                order_number=ord_data['order_number'],
                defaults={
                    'customer_name': ord_data['customer_name'],
                    'customer_email': ord_data['customer_email'],
                    'shipping_address': ord_data['shipping_address'],
                }
            )

            # Clear and rebuild order items
            order.items.all().delete()
            for sku, qty in ord_data['items']:
                OrderItem.objects.create(
                    order=order,
                    product=created_products[sku],
                    quantity=qty
                )

            # Run box recommendation via single source of truth
            rec_result = BoxSelector.recommend_for_order(order)

            status_str = rec_result['status']
            box_code = rec_result['selected_box']['code'] if rec_result.get('selected_box') else 'N/A'
            cost_val = float(rec_result['total_cost']) if rec_result.get('total_cost') else 0.0
            self.stdout.write(f"  Order {order.order_number}: [{status_str}] -> Box {box_code} (${cost_val:.2f})")

        self.stdout.write(self.style.SUCCESS("\nSuccessfully seeded warehouse data and ran recommendations!"))
