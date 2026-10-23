from rest_framework import serializers
from orders.models import Order, OrderItem
from products.serializers import ProductSerializer
from products.models import Product


class OrderItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    total_weight = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    total_volume = serializers.FloatField(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_id',
            'product_details',
            'quantity',
            'total_weight',
            'total_volume',
        ]
        read_only_fields = ['product']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_weight = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    total_volume = serializers.FloatField(read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'customer_name',
            'customer_email',
            'shipping_address',
            'status',
            'notes',
            'items',
            'total_weight',
            'total_volume',
            'total_quantity',
            'created_at',
            'updated_at',
        ]
