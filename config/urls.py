"""
URL configuration for Box Selection System.
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from boxes.views import BoxViewSet
from products.views import ProductViewSet
from orders.views import OrderViewSet
from recommendations.views import (
    BoxRecommendationViewSet,
    RecommendBoxAPIView,
    SimulatePackingAPIView,
    dashboard_view,
    recommender_view,
    orders_list_view,
    boxes_list_view,
)

# API Router
router = DefaultRouter()
router.register(r'boxes', BoxViewSet, basename='box')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'recommendations', BoxRecommendationViewSet, basename='recommendation')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Web UI Views
    path('', dashboard_view, name='dashboard'),
    path('recommender/', recommender_view, name='recommender'),
    path('orders/', orders_list_view, name='orders-list'),
    path('boxes/', boxes_list_view, name='boxes-list'),

    # REST API endpoints
    path('api/', include(router.urls)),
    path('api/recommend/', RecommendBoxAPIView.as_view(), name='api-recommend'),
    path('api/simulate/', SimulatePackingAPIView.as_view(), name='api-simulate'),
]
