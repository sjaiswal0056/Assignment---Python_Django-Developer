"""
Automated Integration Tests for the End-to-End Box Recommendation Workflow.
Verifies all 12 scenarios required for the AI-Assisted Box Selection System.
"""

from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from boxes.models import Box
from products.models import Product
from orders.models import Order, OrderItem
from recommendations.models import BoxRecommendation
from recommendations.services.box_selector import BoxSelector


class RecommendationWorkflowIntegrationTests(APITestCase):
    """
    Complete workflow integration test suite covering Scenarios 1 through 12.
    """

    def setUp(self):
        # 1. Standard active warehouse boxes
        self.box_small = Box.objects.create(
            code="BOX-S",
            name="Small Parcel Box",
            length=Decimal("20.00"),
            width=Decimal("15.00"),
            height=Decimal("10.00"),
            max_weight=Decimal("3.00"),
            cost=Decimal("1.50"),
            is_active=True,
        )
        self.box_medium = Box.objects.create(
            code="BOX-M",
            name="Medium Parcel Box",
            length=Decimal("35.00"),
            width=Decimal("25.00"),
            height=Decimal("20.00"),
            max_weight=Decimal("8.00"),
            cost=Decimal("2.80"),
            is_active=True,
        )
        self.box_large = Box.objects.create(
            code="BOX-L",
            name="Large Freight Box",
            length=Decimal("50.00"),
            width=Decimal("40.00"),
            height=Decimal("30.00"),
            max_weight=Decimal("20.00"),
            cost=Decimal("5.00"),
            is_active=True,
        )

        # 2. Standard products
        self.prod_small = Product.objects.create(
            sku="PROD-SM",
            name="Compact Speaker",
            length=Decimal("12.00"),
            width=Decimal("8.00"),
            height=Decimal("6.00"),
            weight=Decimal("0.50"),
        )
        self.prod_medium = Product.objects.create(
            sku="PROD-MD",
            name="Office Desk Lamp",
            length=Decimal("28.00"),
            width=Decimal("18.00"),
            height=Decimal("14.00"),
            weight=Decimal("2.50"),
        )

        # 3. Standard test orders
        self.order_1 = Order.objects.create(
            order_number="ORD-WF-001",
            customer_name="Alice Walker",
            customer_email="alice@example.com",
            shipping_address="123 Tech Way, Silicon Valley, CA",
        )
        OrderItem.objects.create(order=self.order_1, product=self.prod_small, quantity=1)

        self.order_2 = Order.objects.create(
            order_number="ORD-WF-002",
            customer_name="Bob Martinez",
            customer_email="bob@example.com",
            shipping_address="456 Commerce Blvd, Austin, TX",
        )
        OrderItem.objects.create(order=self.order_2, product=self.prod_medium, quantity=1)

    # -------------------------------------------------------------------------
    # Scenario 1: A calculated recommendation appears in the fulfillment queue.
    # -------------------------------------------------------------------------
    def test_scenario_1_calculated_recommendation_appears_in_fulfillment_queue(self):
        """
        Scenario 1: When a recommendation is calculated for an order, it is
        persisted and correctly retrieved as the order's active recommendation.
        """
        # Initially pending
        self.assertEqual(self.order_1.status, Order.Status.PENDING)
        self.assertIsNone(self.order_1.current_recommendation)

        # Run recommendation
        result = BoxSelector.recommend_for_order(self.order_1)

        self.order_1.refresh_from_db()
        self.assertEqual(self.order_1.status, Order.Status.RECOMMENDED)
        rec = self.order_1.current_recommendation
        self.assertIsNotNone(rec)
        self.assertEqual(rec.status, BoxRecommendation.RecommendationStatus.OPTIMAL)
        self.assertEqual(rec.selected_box, self.box_small)
        self.assertEqual(rec.total_cost, Decimal("1.50"))
        self.assertFalse(rec.is_stale)

    # -------------------------------------------------------------------------
    # Scenario 2: Packaging cost is updated after recalculation.
    # -------------------------------------------------------------------------
    def test_scenario_2_packaging_cost_updated_after_recalculation(self):
        """
        Scenario 2: Packaging cost starts empty/pending, and is correctly updated
        when recalculating an order via API.
        """
        self.assertIsNone(self.order_2.packaging_cost)

        url = reverse('order-recommend', args=[self.order_2.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['packaging_cost'], 2.80)
        self.order_2.refresh_from_db()
        self.assertEqual(self.order_2.packaging_cost, Decimal("2.80"))

    # -------------------------------------------------------------------------
    # Scenario 3: An oversized shipment correctly displays as Oversized / Special Freight.
    # -------------------------------------------------------------------------
    def test_scenario_3_oversized_shipment_displays_oversized_special_freight(self):
        """
        Scenario 3: An item whose dimensions exceed all boxes in the catalog is
        classified as OVERSIZED / Special Freight and not assigned an invalid box.
        """
        oversized_prod = Product.objects.create(
            sku="PROD-OVERSIZED",
            name="Kayak Paddle",
            length=Decimal("180.00"),  # Exceeds max box length (50cm)
            width=Decimal("15.00"),
            height=Decimal("10.00"),
            weight=Decimal("2.00"),
        )
        order_oversized = Order.objects.create(
            order_number="ORD-OVERSIZED-1",
            customer_name="Paddle Explorer",
        )
        OrderItem.objects.create(order=order_oversized, product=oversized_prod, quantity=1)

        result = BoxSelector.recommend_for_order(order_oversized)

        order_oversized.refresh_from_db()
        self.assertEqual(order_oversized.status, Order.Status.OVERSIZED)
        self.assertEqual(order_oversized.get_status_display(), "Oversized / Special Freight")
        self.assertEqual(result['status'], "OVERSIZED")
        self.assertIsNone(result['selected_box'])

        rec = order_oversized.current_recommendation
        self.assertIsNotNone(rec)
        self.assertEqual(rec.status, BoxRecommendation.RecommendationStatus.OVERSIZED)
        self.assertIsNone(rec.selected_box)

    # -------------------------------------------------------------------------
    # Scenario 4: A shipment exceeding weight limits is flagged with weight status (not Oversized).
    # -------------------------------------------------------------------------
    def test_scenario_4_weight_limit_exceeded_not_marked_as_oversized(self):
        """
        Scenario 4: An item that fits dimensionally but exceeds weight limits
        is flagged as WEIGHT_EXCEEDED and NEVER mislabeled as OVERSIZED.
        """
        heavy_prod = Product.objects.create(
            sku="PROD-HEAVY-ANVIL",
            name="Cast Iron Anvil",
            length=Decimal("25.00"),  # Fits inside Large Box (50x40x30)
            width=Decimal("20.00"),
            height=Decimal("15.00"),
            weight=Decimal("45.00"),  # Exceeds Large Box max weight (20kg)
        )
        order_heavy = Order.objects.create(
            order_number="ORD-HEAVY-1",
            customer_name="Heavy Metal Works",
        )
        OrderItem.objects.create(order=order_heavy, product=heavy_prod, quantity=1)

        result = BoxSelector.recommend_for_order(order_heavy)

        order_heavy.refresh_from_db()
        self.assertEqual(order_heavy.status, Order.Status.WEIGHT_EXCEEDED)
        self.assertEqual(order_heavy.get_status_display(), "Weight Limit Exceeded")
        self.assertNotEqual(order_heavy.status, Order.Status.OVERSIZED)
        self.assertEqual(result['status'], "WEIGHT_EXCEEDED")

        rec = order_heavy.current_recommendation
        self.assertIsNotNone(rec)
        self.assertEqual(rec.status, BoxRecommendation.RecommendationStatus.WEIGHT_EXCEEDED)
        self.assertNotEqual(rec.status, BoxRecommendation.RecommendationStatus.OVERSIZED)

    # -------------------------------------------------------------------------
    # Scenario 5: A recommendation is associated with the correct order and not another order.
    # -------------------------------------------------------------------------
    def test_scenario_5_recommendation_associated_with_correct_order(self):
        """
        Scenario 5: Calculating for Order 1 persists a recommendation for Order 1
        only, and does not alter Order 2.
        """
        result = BoxSelector.recommend_for_order(self.order_1)

        self.order_1.refresh_from_db()
        self.order_2.refresh_from_db()

        self.assertEqual(self.order_1.status, Order.Status.RECOMMENDED)
        self.assertEqual(self.order_2.status, Order.Status.PENDING)
        self.assertIsNotNone(self.order_1.current_recommendation)
        self.assertIsNone(self.order_2.current_recommendation)

        # Recommendation points to order_1 only
        rec = BoxRecommendation.objects.get(id=result['id'])
        self.assertEqual(rec.order, self.order_1)

    # -------------------------------------------------------------------------
    # Scenario 6: Standalone simulator calculations do not overwrite or modify orders.
    # -------------------------------------------------------------------------
    def test_scenario_6_standalone_simulator_does_not_modify_unrelated_orders(self):
        """
        Scenario 6: Using the simulator in standalone mode (no order_id) calculates
        ephemerally without mutating any existing database orders.
        """
        url = reverse('api-recommend')
        payload = {
            'items': [
                {
                    'name': 'Standalone Test Widget',
                    'sku': 'STANDALONE-SKU',
                    'length': 15.0,
                    'width': 10.0,
                    'height': 5.0,
                    'weight': 0.8,
                    'quantity': 1,
                }
            ]
        }

        rec_count_before = BoxRecommendation.objects.count()
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('is_standalone'))
        self.assertIsNone(response.data.get('order_id'))
        self.assertEqual(response.data['status'], 'OPTIMAL')

        # No recommendations created in DB
        self.assertEqual(BoxRecommendation.objects.count(), rec_count_before)

        # Existing orders untouched
        self.order_1.refresh_from_db()
        self.order_2.refresh_from_db()
        self.assertEqual(self.order_1.status, Order.Status.PENDING)
        self.assertEqual(self.order_2.status, Order.Status.PENDING)

    # -------------------------------------------------------------------------
    # Scenario 7: A failed calculation is not marked as Recommended.
    # -------------------------------------------------------------------------
    def test_scenario_7_failed_calculation_not_marked_as_recommended(self):
        """
        Scenario 7: When an order cannot be accommodated or calculation encounters
        an unresolvable constraint, order status must NOT be set to RECOMMENDED.
        """
        huge_item = Product.objects.create(
            sku="PROD-HUGE",
            name="Massive Sculpture",
            length=Decimal("300.00"),
            width=Decimal("200.00"),
            height=Decimal("100.00"),
            weight=Decimal("80.00"),
        )
        order_fail = Order.objects.create(
            order_number="ORD-FAIL-01",
            customer_name="Art Museum",
        )
        OrderItem.objects.create(order=order_fail, product=huge_item, quantity=1)

        result = BoxSelector.recommend_for_order(order_fail)
        order_fail.refresh_from_db()

        self.assertNotEqual(order_fail.status, Order.Status.RECOMMENDED)
        self.assertIn(order_fail.status, [Order.Status.OVERSIZED, Order.Status.WEIGHT_EXCEEDED, Order.Status.ERROR])

    # -------------------------------------------------------------------------
    # Scenario 8: Recalculating one order leaves other orders unchanged.
    # -------------------------------------------------------------------------
    def test_scenario_8_recalculating_one_order_leaves_other_orders_unchanged(self):
        """
        Scenario 8: Recalculating Order 1 does not alter Order 2's recommendation,
        status, or packaging cost.
        """
        # Recommend both initially
        BoxSelector.recommend_for_order(self.order_1)
        BoxSelector.recommend_for_order(self.order_2)

        self.order_2.refresh_from_db()
        order_2_rec = self.order_2.current_recommendation
        order_2_rec_id = order_2_rec.id
        order_2_cost = order_2_rec.total_cost

        # Recalculate Order 1
        url = reverse('order-recommend', args=[self.order_1.id])
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Verify Order 2 is completely unchanged
        self.order_2.refresh_from_db()
        self.assertEqual(self.order_2.current_recommendation.id, order_2_rec_id)
        self.assertEqual(self.order_2.current_recommendation.total_cost, order_2_cost)
        self.assertEqual(self.order_2.status, Order.Status.RECOMMENDED)

    # -------------------------------------------------------------------------
    # Scenario 9: The queue displays the latest saved recommendation.
    # -------------------------------------------------------------------------
    def test_scenario_9_queue_displays_latest_saved_recommendation(self):
        """
        Scenario 9: If multiple recommendations exist historically for an order,
        the active/current recommendation returned is the latest valid one.
        """
        # Run initial recommendation
        BoxSelector.recommend_for_order(self.order_1)
        first_rec = self.order_1.current_recommendation

        # Re-run recommendation
        BoxSelector.recommend_for_order(self.order_1)
        self.order_1.refresh_from_db()
        latest_rec = self.order_1.current_recommendation

        # Verify latest is different instance and active, older is marked stale
        self.assertNotEqual(first_rec.id, latest_rec.id)
        first_rec.refresh_from_db()
        self.assertTrue(first_rec.is_stale)
        self.assertFalse(latest_rec.is_stale)

    # -------------------------------------------------------------------------
    # Scenario 10: Shipment modifications invalidate outdated recommendations.
    # -------------------------------------------------------------------------
    def test_scenario_10_shipment_modifications_invalidate_outdated_recommendations(self):
        """
        Scenario 10: Modifying order items, quantities, or product dimensions
        invalidates current recommendation (is_stale=True) and reverts status to PENDING.
        """
        BoxSelector.recommend_for_order(self.order_1)
        self.order_1.refresh_from_db()
        self.assertEqual(self.order_1.status, Order.Status.RECOMMENDED)
        self.assertFalse(self.order_1.is_recommendation_stale)
        self.assertIsNotNone(self.order_1.current_recommendation)

        # Modify item quantity (shipment changes)
        order_item = self.order_1.items.first()
        order_item.quantity = 5
        order_item.save()

        self.order_1.refresh_from_db()
        # Outdated recommendation is invalidated
        self.assertTrue(self.order_1.is_recommendation_stale)
        self.assertEqual(self.order_1.status, Order.Status.PENDING)
        self.assertIsNone(self.order_1.current_recommendation)
        self.assertIsNone(self.order_1.packaging_cost)

        # Recalculate with updated shipment
        res = BoxSelector.recommend_for_order(self.order_1)
        self.order_1.refresh_from_db()
        self.assertFalse(self.order_1.is_recommendation_stale)
        self.assertEqual(self.order_1.status, Order.Status.RECOMMENDED)
        self.assertIsNotNone(self.order_1.current_recommendation)

    # -------------------------------------------------------------------------
    # Scenario 11: Audit logs reflect the actual recommendation decision.
    # -------------------------------------------------------------------------
    def test_scenario_11_audit_logs_reflect_actual_recommendation_decision(self):
        """
        Scenario 11: Audit log accurately records candidate box evaluations,
        rejection reasons (physical constraints), and the accepted box rationale.
        """
        result = BoxSelector.recommend_for_order(self.order_2)
        rec = self.order_2.current_recommendation

        self.assertIsNotNone(rec.audit_trail)
        self.assertGreaterEqual(len(rec.audit_trail), 2)

        # BOX-S must be rejected because PROD-MD (28x18x14cm) exceeds BOX-S (20x15x10cm)
        box_s_audit = next((b for b in rec.audit_trail if b.get('box_code') == 'BOX-S'), None)
        self.assertIsNotNone(box_s_audit)
        self.assertEqual(box_s_audit['status'], 'REJECTED')

        # BOX-M must be accepted
        box_m_audit = next((b for b in rec.audit_trail if b.get('box_code') == 'BOX-M'), None)
        self.assertIsNotNone(box_m_audit)
        self.assertEqual(box_m_audit['status'], 'ACCEPTED')

        # Explanation contains rationale
        self.assertIn("Medium Parcel Box", rec.explanation)

    # -------------------------------------------------------------------------
    # Scenario 12: API response provides all required fields for frontend queue update.
    # -------------------------------------------------------------------------
    def test_scenario_12_api_response_provides_all_required_fields_for_frontend(self):
        """
        Scenario 12: The API response provides all required fields for immediate
        asynchronous frontend row update without needing a full-page reload.
        """
        url = reverse('order-recommend', args=[self.order_1.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        required_fields = [
            'order_id',
            'order_number',
            'customer_name',
            'status',
            'status_display',
            'packaging_cost',
            'total_cost',
            'total_weight',
            'selected_box',
            'recommended_box',
            'boxes_used',
            'packing_layout',
            'audit_trail',
            'explanation',
            'is_standalone',
        ]
        for field in required_fields:
            self.assertIn(field, data, f"Missing required field '{field}' in API response")

        self.assertEqual(data['order_id'], self.order_1.id)
        self.assertEqual(data['order_number'], self.order_1.order_number)
        self.assertEqual(data['status'], 'OPTIMAL')
        self.assertEqual(data['is_standalone'], False)
        self.assertEqual(data['packaging_cost'], 1.50)
        self.assertEqual(data['recommended_box']['code'], 'BOX-S')
