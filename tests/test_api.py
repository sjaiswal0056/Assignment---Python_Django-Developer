from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from boxes.models import Box
from products.models import Product
from orders.models import Order, OrderItem
from recommendations.models import BoxRecommendation


class BoxSelectionAPITests(APITestCase):
    """
    Integration tests for Box Selection System REST APIs.
    """

    def setUp(self):
        self.box_s = Box.objects.create(
            code="API-BOX-S",
            name="Small Box",
            length=Decimal("25.00"),
            width=Decimal("20.00"),
            height=Decimal("12.00"),
            max_weight=Decimal("4.00"),
            cost=Decimal("1.40"),
            is_active=True,
        )
        self.box_m = Box.objects.create(
            code="API-BOX-M",
            name="Medium Box",
            length=Decimal("35.00"),
            width=Decimal("28.00"),
            height=Decimal("18.00"),
            max_weight=Decimal("8.00"),
            cost=Decimal("2.60"),
            is_active=True,
        )
        self.product = Product.objects.create(
            sku="SKU-API-1",
            name="Wireless Mouse",
            length=Decimal("12.00"),
            width=Decimal("8.00"),
            height=Decimal("5.00"),
            weight=Decimal("0.25"),
        )
        self.order = Order.objects.create(
            order_number="ORD-API-001",
            customer_name="API Tester",
            customer_email="api@test.com",
        )
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1)

    def test_list_boxes(self):
        url = reverse('box-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify pagination or list structure
        data = response.data['results'] if 'results' in response.data else response.data
        self.assertGreaterEqual(len(data), 2)

    def test_list_products(self):
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results'] if 'results' in response.data else response.data
        self.assertGreaterEqual(len(data), 1)

    def test_recommend_box_ad_hoc_items(self):
        url = reverse('api-recommend')
        payload = {
            'items': [
                {
                    'name': 'Wireless Mouse',
                    'sku': 'SKU-API-1',
                    'length': 12.0,
                    'width': 8.0,
                    'height': 5.0,
                    'weight': 0.25,
                    'quantity': 1,
                }
            ]
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'OPTIMAL')
        self.assertEqual(response.data['selected_box']['code'], 'API-BOX-S')
        self.assertEqual(response.data['total_cost'], 1.40)
        self.assertIn('packing_layout', response.data)
        self.assertIn('audit_trail', response.data)

    def test_recommend_box_for_order(self):
        url = reverse('api-recommend')
        payload = {'order_id': self.order.id}
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'OPTIMAL')
        self.assertEqual(response.data['order_number'], 'ORD-API-001')

        # Verify order status was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.RECOMMENDED)

        # Verify recommendation record was persisted
        self.assertTrue(BoxRecommendation.objects.filter(order=self.order).exists())

    def test_order_custom_action_recommend(self):
        url = reverse('order-recommend', args=[self.order.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'OPTIMAL')

    def test_simulate_packing_api(self):
        url = reverse('api-simulate')
        payload = {
            'box_id': self.box_s.id,
            'items': [
                {
                    'name': 'Small Cube',
                    'sku': 'CUBE',
                    'length': 10.0,
                    'width': 10.0,
                    'height': 10.0,
                    'weight': 1.0,
                    'quantity': 1,
                }
            ]
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['packed_items']), 1)

    def test_recommend_validation_error_on_empty_payload(self):
        url = reverse('api-recommend')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
