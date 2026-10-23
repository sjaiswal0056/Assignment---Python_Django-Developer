from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, views, status, filters
from rest_framework.response import Response

from recommendations.models import BoxRecommendation
from recommendations.serializers import (
    BoxRecommendationSerializer,
    RecommendationRequestSerializer,
)
from recommendations.services.box_selector import BoxSelector
from recommendations.services.packing_engine import PackingEngine
from orders.models import Order
from boxes.models import Box
from products.models import Product


# --- API ViewSets and Endpoints ---

class BoxRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing historical box recommendations.
    """
    queryset = BoxRecommendation.objects.select_related('order', 'selected_box').all()
    serializer_class = BoxRecommendationSerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']


class RecommendBoxAPIView(views.APIView):
    """
    POST /api/recommend/
    Recommends the optimal box for an order or custom list of items.
    """
    def post(self, request, *args, **kwargs):
        serializer = RecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data.get('order_id'):
            order = get_object_or_404(Order, id=data['order_id'])
            items = BoxSelector.items_from_order(order)
            rec_result = BoxSelector.select_box(items)

            # Persist recommendation
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

            return Response(BoxRecommendationSerializer(recommendation).data, status=status.HTTP_200_OK)

        elif data.get('items'):
            items = BoxSelector.items_from_raw_data(data['items'])
            rec_result = BoxSelector.select_box(items)

            # Ad-hoc recommendation
            response_payload = {
                'status': rec_result['status'],
                'selected_box': (
                    {
                        'id': rec_result['selected_box'].id,
                        'code': rec_result['selected_box'].code,
                        'name': rec_result['selected_box'].name,
                        'dimensions': rec_result['selected_box'].dimensions_display,
                        'cost': float(rec_result['selected_box'].cost),
                        'max_weight': float(rec_result['selected_box'].max_weight),
                    }
                    if rec_result['selected_box']
                    else None
                ),
                'total_cost': rec_result['total_cost'],
                'total_weight': rec_result['total_weight'],
                'total_volume': rec_result['total_volume'],
                'volume_utilization': round(rec_result['volume_utilization'], 2),
                'weight_utilization': round(rec_result['weight_utilization'], 2),
                'boxes_used': rec_result['boxes_used'],
                'packing_layout': rec_result['packing_layout'],
                'audit_trail': rec_result['audit_trail'],
                'explanation': rec_result['explanation'],
            }
            return Response(response_payload, status=status.HTTP_200_OK)


class SimulatePackingAPIView(views.APIView):
    """
    POST /api/simulate/
    Simulates packing given items into a specific box.
    Returns 3D spatial layout and collision verification.
    """
    def post(self, request, *args, **kwargs):
        box_id = request.data.get('box_id')
        items_data = request.data.get('items', [])

        if not box_id or not items_data:
            return Response(
                {'error': "Both 'box_id' and 'items' list are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        box = get_object_or_404(Box, id=box_id)
        items = BoxSelector.items_from_raw_data(items_data)

        result = PackingEngine.pack(
            box_length=float(box.length),
            box_width=float(box.width),
            box_height=float(box.height),
            box_max_weight=float(box.max_weight),
            box_cost=float(box.cost),
            box_name=box.name,
            box_code=box.code,
            items=items,
        )

        return Response(result.to_dict(), status=status.HTTP_200_OK)


# --- Web UI Views ---

def dashboard_view(request):
    """Warehouse operations main dashboard."""
    boxes_count = Box.objects.filter(is_active=True).count()
    products_count = Product.objects.count()
    orders = Order.objects.prefetch_related('items__product').all()[:10]
    total_orders = Order.objects.count()
    recommendations = BoxRecommendation.objects.select_related('order', 'selected_box')[:6]

    context = {
        'boxes_count': boxes_count,
        'products_count': products_count,
        'total_orders': total_orders,
        'orders': orders,
        'recommendations': recommendations,
    }
    return render(request, 'dashboard.html', context)


def recommender_view(request):
    """Interactive warehouse box recommendation & 3D visualizer tool."""
    products = Product.objects.all().order_by('name')
    boxes = Box.objects.filter(is_active=True).order_by('cost')
    orders = Order.objects.all().order_by('-created_at')

    context = {
        'products': products,
        'boxes': boxes,
        'orders': orders,
    }
    return render(request, 'recommender.html', context)


def orders_list_view(request):
    """Orders management view."""
    orders = Order.objects.prefetch_related('items__product', 'recommendations__selected_box').all()
    context = {'orders': orders}
    return render(request, 'orders.html', context)


def boxes_list_view(request):
    """Warehouse box inventory catalog view."""
    boxes = Box.objects.all().order_by('cost')
    context = {'boxes': boxes}
    return render(request, 'boxes.html', context)
