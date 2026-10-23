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
        """
        order = self.get_object()
        items = BoxSelector.items_from_order(order)
        rec_result = BoxSelector.select_box(items)

        # Update or create recommendation record
        recommendation, _ = BoxRecommendation.objects.update_or_create(
            order=order,
            defaults={
                'status': rec_result['status'],
                'selected_box': rec_result['selected_box'],
                'total_cost': Decimal(str(rec_result['total_cost'])),
                'total_weight': Decimal(str(rec_result['total_weight'])),
                'total_volume': rec_result['total_volume'],
                'volume_utilization': rec_result['volume_utilization'],
                'weight_utilization': rec_result['weight_utilization'],
                'boxes_used': rec_result['boxes_used'],
                'packing_layout': rec_result['packing_layout'],
                'audit_trail': rec_result['audit_trail'],
                'explanation': rec_result['explanation'],
            }
        )

        if rec_result['status'] == 'OPTIMAL':
            order.status = Order.Status.RECOMMENDED
            order.save(update_fields=['status'])

        return Response(
            BoxRecommendationSerializer(recommendation).data,
            status=status.HTTP_200_OK
        )
