from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from boxes.models import Box
from products.models import Product
from orders.models import Order, OrderItem


class ModelValidationTests(TestCase):
    """
    Tests for Model clean validations and helper properties.
    """

    def test_box_validation_rejects_negative_or_zero_dimensions(self):
        b1 = Box(
            code="INVALID-1",
            name="Zero Length Box",
            length=Decimal("0.00"),
            width=Decimal("10.00"),
            height=Decimal("10.00"),
            max_weight=Decimal("5.00"),
            cost=Decimal("1.00"),
        )
        with self.assertRaises(ValidationError):
            b1.full_clean()

    def test_box_validation_rejects_negative_cost(self):
        b2 = Box(
            code="INVALID-2",
            name="Negative Cost Box",
            length=Decimal("10.00"),
            width=Decimal("10.00"),
            height=Decimal("10.00"),
            max_weight=Decimal("5.00"),
            cost=Decimal("-1.00"),
        )
        with self.assertRaises(ValidationError):
            b2.full_clean()

    def test_box_volume_calculation(self):
        box = Box(
            code="VOL-TEST",
            name="Volume Box",
            length=Decimal("20.00"),
            width=Decimal("15.00"),
            height=Decimal("10.00"),
            max_weight=Decimal("5.00"),
            cost=Decimal("2.00"),
        )
        self.assertEqual(box.volume, 3000.0)
        self.assertEqual(box.volume_liters, 3.0)

    def test_product_validation_rejects_negative_weight(self):
        prod = Product(
            sku="INVALID-SKU",
            name="Anti-gravity Widget",
            length=Decimal("10.00"),
            width=Decimal("10.00"),
            height=Decimal("10.00"),
            weight=Decimal("-0.50"),
        )
        with self.assertRaises(ValidationError):
            prod.full_clean()

    def test_order_aggregations(self):
        p1 = Product.objects.create(
            sku="SKU-A",
            name="Item A",
            length=Decimal("10.00"),
            width=Decimal("10.00"),
            height=Decimal("10.00"),
            weight=Decimal("1.50"),
        )
        p2 = Product.objects.create(
            sku="SKU-B",
            name="Item B",
            length=Decimal("20.00"),
            width=Decimal("10.00"),
            height=Decimal("5.00"),
            weight=Decimal("2.00"),
        )
        order = Order.objects.create(
            order_number="ORD-AGG-1",
            customer_name="John Doe",
        )
        OrderItem.objects.create(order=order, product=p1, quantity=2) # 2 * 1.5 = 3.0 kg, 2 * 1000 = 2000 cm3
        OrderItem.objects.create(order=order, product=p2, quantity=1) # 1 * 2.0 = 2.0 kg, 1 * 1000 = 1000 cm3

        self.assertEqual(order.total_quantity, 3)
        self.assertEqual(order.total_weight, Decimal("5.00"))
        self.assertEqual(order.total_volume, 3000.0)
