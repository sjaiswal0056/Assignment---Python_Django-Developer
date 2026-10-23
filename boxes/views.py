from rest_framework import viewsets, filters
from boxes.models import Box
from boxes.serializers import BoxSerializer


class BoxViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing shipping boxes in the warehouse.
    Supports filtering by active status, search by name/code, and ordering by cost/volume.
    """
    queryset = Box.objects.all()
    serializer_class = BoxSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['cost', 'length', 'width', 'height', 'max_weight']
    ordering = ['cost']
