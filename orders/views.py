from decimal import Decimal
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from orders.models import Order
from orders.serializers import OrderSerializer
from recommendations.services.box_selector import BoxSelector
from recommendations.models import BoxRecommendation
from recommendations.serializers import BoxRecommendationSerializer


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing orders.
    Includes custom action `/api/orders/{id}/recommend/` to run box selection.
    """
    queryset = Order.objects.prefetch_related('items__product').all()
    serializer_class = OrderSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_number', 'customer_name', 'customer_email']
    ordering_fields = ['created_at', 'order_number']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'], url_path='recommend')
    def recommend(self, request, pk=None):
        """
        Trigger box recommendation algorithm for this specific order.
        Persists the result in BoxRecommendation and updates order status.
        Uses BoxSelector.recommend_for_order as the single source of truth.
        """
        order = self.get_object()
        res_data = BoxSelector.recommend_for_order(order)
        return Response(res_data, status=status.HTTP_200_OK)
