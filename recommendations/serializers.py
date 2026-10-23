from rest_framework import serializers
from recommendations.models import BoxRecommendation
from boxes.serializers import BoxSerializer


class BoxRecommendationSerializer(serializers.ModelSerializer):
    selected_box_details = BoxSerializer(source='selected_box', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model = BoxRecommendation
        fields = [
            'id',
            'order',
            'order_number',
            'status',
            'selected_box',
            'selected_box_details',
            'total_cost',
            'total_weight',
            'total_volume',
            'volume_utilization',
            'weight_utilization',
            'boxes_used',
            'packing_layout',
            'audit_trail',
            'explanation',
            'created_at',
        ]


class ItemInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, default="Item")
    sku = serializers.CharField(max_length=50, default="SKU-GEN")
    length = serializers.FloatField(min_value=0.01, help_text="Length in cm")
    width = serializers.FloatField(min_value=0.01, help_text="Width in cm")
    height = serializers.FloatField(min_value=0.01, help_text="Height in cm")
    weight = serializers.FloatField(min_value=0.01, help_text="Weight in kg")
    quantity = serializers.IntegerField(default=1, min_value=1, help_text="Number of units")


class RecommendationRequestSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=False, help_text="Optional ID of existing Order")
    items = ItemInputSerializer(many=True, required=False, help_text="List of custom items to pack")

    def validate(self, attrs):
        if not attrs.get('order_id') and not attrs.get('items'):
            raise serializers.ValidationError("Either 'order_id' or 'items' list must be provided.")
        return attrs
