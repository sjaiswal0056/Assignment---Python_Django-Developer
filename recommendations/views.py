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
            items = None
            if data.get('items'):
                items = BoxSelector.items_from_raw_data(data['items'])
            res_data = BoxSelector.recommend_for_order(order, items=items)
            return Response(res_data, status=status.HTTP_200_OK)

        elif data.get('items'):
            items = BoxSelector.items_from_raw_data(data['items'])
            rec_result = BoxSelector.select_box(items)

            # Ad-hoc / Standalone recommendation (does not touch Order or DB)
            response_payload = {
                'status': rec_result['status'],
                'order_id': None,
                'order_number': None,
                'is_standalone': True,
                'selected_box': (
                    {
                        'id': rec_result['selected_box'].id,
                        'code': rec_result['selected_box'].code,
                        'name': rec_result['selected_box'].name,
                        'dimensions': rec_result['selected_box'].dimensions_display,
                        'cost': float(rec_result['selected_box'].cost),
                        'max_weight': float(rec_result['selected_box'].max_weight),
                    }
                    if rec_result.get('selected_box')
                    else None
                ),
                'total_cost': rec_result.get('total_cost', 0.0),
                'packaging_cost': rec_result.get('total_cost', 0.0),
                'total_weight': rec_result.get('total_weight', 0.0),
                'total_volume': rec_result.get('total_volume', 0.0),
                'volume_utilization': round(rec_result.get('volume_utilization', 0.0), 2),
                'weight_utilization': round(rec_result.get('weight_utilization', 0.0), 2),
                'boxes_used': rec_result.get('boxes_used', []),
                'packing_layout': rec_result.get('packing_layout', []),
                'audit_trail': rec_result.get('audit_trail', []),
                'explanation': rec_result.get('explanation', ''),
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
