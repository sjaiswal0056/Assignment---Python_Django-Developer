from django.contrib import admin
from recommendations.models import BoxRecommendation


@admin.register(BoxRecommendation)
class BoxRecommendationAdmin(admin.ModelAdmin):
    list_display = (
        'order',
        'status',
        'selected_box',
        'total_cost',
        'total_weight',
        'volume_utilization_display',
        'weight_utilization_display',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_number', 'selected_box__name', 'selected_box__code')
    readonly_fields = (
        'created_at',
        'volume_utilization_display',
        'weight_utilization_display',
        'boxes_used',
        'packing_layout',
        'audit_trail',
        'explanation',
    )

    @admin.display(description="Vol. Util.")
    def volume_utilization_display(self, obj):
        return f"{obj.volume_utilization:.1f}%"

    @admin.display(description="Weight Util.")
    def weight_utilization_display(self, obj):
        return f"{obj.weight_utilization:.1f}%"
