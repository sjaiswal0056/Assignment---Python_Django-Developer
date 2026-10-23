from rest_framework import serializers
from boxes.models import Box


class BoxSerializer(serializers.ModelSerializer):
    volume = serializers.FloatField(read_only=True)
    volume_liters = serializers.FloatField(read_only=True)
    dimensions_display = serializers.CharField(read_only=True)

    class Meta:
        model = Box
        fields = [
            'id',
            'code',
            'name',
            'length',
            'width',
            'height',
            'max_weight',
            'empty_weight',
            'cost',
            'is_active',
            'volume',
            'volume_liters',
            'dimensions_display',
            'created_at',
            'updated_at',
        ]
