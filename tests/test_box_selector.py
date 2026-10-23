from decimal import Decimal
from django.test import TestCase
from boxes.models import Box
from products.models import Product
from orders.models import Order, OrderItem
from recommendations.services.box_selector import BoxSelector
from recommendations.services.packing_engine import ItemToPack


class BoxSelectorTests(TestCase):
    """
    Tests for the BoxSelector orchestration service.
    """

    def setUp(self):
        # Create standard test box hierarchy
        self.box_small = Box.objects.create(
            code="TEST-S",
            name="Small Box",
            length=Decimal("20.00"),
            width=Decimal("15.00"),
            height=Decimal("10.00"),
            max_weight=Decimal("3.00"),
            cost=Decimal("1.50"),
            is_active=True,
        )
        self.box_medium = Box.objects.create(
            code="TEST-M",
            name="Medium Box",
            length=Decimal("35.00"),
            width=Decimal("25.00"),
            height=Decimal("20.00"),
            max_weight=Decimal("8.00"),
            cost=Decimal("3.00"),
            is_active=True,
        )
        self.box_large = Box.objects.create(
            code="TEST-L",
            name="Large Box",
            length=Decimal("50.00"),
            width=Decimal("40.00"),
            height=Decimal("30.00"),
            max_weight=Decimal("20.00"),
            cost=Decimal("5.50"),
            is_active=True,
        )

    def test_cheapest_fitting_box_selected(self):
        # Item: 15 x 10 x 5 cm, 1.0 kg -> Fits in Small, Medium, and Large.
        # Should pick TEST-S because it is the cheapest ($1.50).
        item = ItemToPack(
            id="1", name="Small Book", sku="SKU-BK",
            length=15.0, width=10.0, height=5.0, weight=1.0
        )
        result = BoxSelector.select_box([item])
        self.assertEqual(result['status'], 'OPTIMAL')
        self.assertEqual(result['selected_box'].code, 'TEST-S')
        self.assertEqual(result['total_cost'], 1.50)

    def test_cheaper_box_rejected_for_weight(self):
        # Item: 15 x 10 x 5 cm (physically fits in Small Box), but weighs 5.0 kg!
        # Small Box max weight is 3.0 kg, Medium Box max weight is 8.0 kg.
        # Must skip Small Box and select Medium Box ($3.00).
        heavy_item = ItemToPack(
            id="1", name="Heavy Lead Piece", sku="SKU-LEAD",
            length=15.0, width=10.0, height=5.0, weight=5.0
        )
        result = BoxSelector.select_box([heavy_item])
        self.assertEqual(result['status'], 'OPTIMAL')
        self.assertEqual(result['selected_box'].code, 'TEST-M')
        self.assertEqual(result['total_cost'], 3.00)

        # Audit trail must show TEST-S rejected due to weight
        small_audit = next(b for b in result['audit_trail'] if b['box_code'] == 'TEST-S')
        self.assertEqual(small_audit['status'], 'REJECTED')
        self.assertIn("Exceeds max weight capacity", small_audit['reason'])

    def test_cheaper_box_rejected_for_dimensions(self):
        # Item: 28 x 10 x 5 cm, 1.0 kg (fits in Medium Box, but too long for Small Box 20x15x10).
        # Must skip Small Box and select Medium Box.
        long_item = ItemToPack(
            id="1", name="Long Ruler Box", sku="SKU-RULER",
            length=28.0, width=10.0, height=5.0, weight=1.0
        )
        result = BoxSelector.select_box([long_item])
        self.assertEqual(result['status'], 'OPTIMAL')
        self.assertEqual(result['selected_box'].code, 'TEST-M')

    def test_oversized_item_returns_no_fit(self):
        # Item: 100 x 20 x 20 cm, exceeds all boxes in catalog
        huge_item = ItemToPack(
            id="1", name="Giant Poster", sku="SKU-GIANT",
            length=100.0, width=20.0, height=20.0, weight=2.0
        )
        result = BoxSelector.select_box([huge_item])
        self.assertEqual(result['status'], 'NO_FIT')
        self.assertIsNone(result['selected_box'])
        self.assertIn("ALERT: No Suitable Standard Box Found", result['explanation'])

    def test_multi_box_split_when_single_box_exceeded(self):
        # Create items that individually fit in Medium Box, but together exceed Large Box (20kg max)
        # 3 items of 8kg each = 24kg total!
        items = [
            ItemToPack(id="1", name="Kettlebell 1", sku="KB1", length=20.0, width=15.0, height=15.0, weight=8.0),
            ItemToPack(id="2", name="Kettlebell 2", sku="KB2", length=20.0, width=15.0, height=15.0, weight=8.0),
            ItemToPack(id="3", name="Kettlebell 3", sku="KB3", length=20.0, width=15.0, height=15.0, weight=8.0),
        ]
        result = BoxSelector.select_box(items)
        self.assertEqual(result['status'], 'SPLIT_REQUIRED')
        self.assertGreaterEqual(len(result['boxes_used']), 2)
        self.assertIn("Multi-Box Split Required", result['explanation'])

    def test_order_conversion_and_recommendation(self):
        product = Product.objects.create(
            sku="SKU-T1",
            name="Test Headphones",
            length=Decimal("18.00"),
            width=Decimal("14.00"),
            height=Decimal("8.00"),
            weight=Decimal("0.50"),
        )
        order = Order.objects.create(
            order_number="ORD-TEST-99",
            customer_name="Test User",
            customer_email="test@user.com",
        )
        OrderItem.objects.create(order=order, product=product, quantity=2)

        items = BoxSelector.items_from_order(order)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].sku, "SKU-T1")
        self.assertEqual(items[1].sku, "SKU-T1")

        # For quantity=2, total volume is 4,032 cm3 which exceeds Small Box (3,000 cm3).
        # BoxSelector correctly upgrades recommendation to Medium Box (TEST-M)!
        result_2 = BoxSelector.select_box(items)
        self.assertEqual(result_2['status'], 'OPTIMAL')
        self.assertEqual(result_2['selected_box'].code, 'TEST-M')

        # Now test single unit (quantity=1) which cleanly fits in Small Box (TEST-S)
        order_single = Order.objects.create(
            order_number="ORD-TEST-SINGLE",
            customer_name="Single Item User",
        )
        OrderItem.objects.create(order=order_single, product=product, quantity=1)
        items_single = BoxSelector.items_from_order(order_single)
        result_1 = BoxSelector.select_box(items_single)
        self.assertEqual(result_1['status'], 'OPTIMAL')
        self.assertEqual(result_1['selected_box'].code, 'TEST-S')
