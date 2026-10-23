from rest_framework import serializers
from products.models import Product


class ProductSerializer(serializers.ModelSerializer):
    volume = serializers.FloatField(read_only=True)
    volume_liters = serializers.FloatField(read_only=True)
    dimensions_display = serializers.CharField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'sku',
            'name',
            'description',
            'category',
            'length',
            'width',
            'height',
            'weight',
            'is_fragile',
            'volume',
            'volume_liters',
            'dimensions_display',
            'created_at',
            'updated_at',
        ]
