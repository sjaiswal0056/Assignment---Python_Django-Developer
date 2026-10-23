from rest_framework import viewsets, filters
from products.models import Product
from products.serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing ecommerce products.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'sku', 'category']
    ordering_fields = ['name', 'sku', 'weight', 'length']
    ordering = ['name']
