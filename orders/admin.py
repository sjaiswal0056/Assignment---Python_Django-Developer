from decimal import Decimal
from django.contrib import admin, messages
from orders.models import Order, OrderItem
from recommendations.services.box_selector import BoxSelector
from recommendations.models import BoxRecommendation


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ('product', 'quantity', 'item_weight_display', 'item_volume_display')
    readonly_fields = ('item_weight_display', 'item_volume_display')

    def item_weight_display(self, obj):
        return f"{obj.total_weight:.2f} kg" if obj.pk else "-"
    item_weight_display.short_description = "Subtotal Weight"

    def item_volume_display(self, obj):
        return f"{obj.total_volume:.0f} cm³" if obj.pk else "-"
    item_volume_display.short_description = "Subtotal Volume"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'status', 'total_quantity', 'total_weight_display', 'total_volume_display', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_email')
    inlines = [OrderItemInline]
    actions = ['run_box_recommendation']

    @admin.display(description="Total Weight")
    def total_weight_display(self, obj):
        return f"{obj.total_weight:.2f} kg"

    @admin.display(description="Total Volume")
    def total_volume_display(self, obj):
        return f"{obj.total_volume / 1000.0:.2f} L"

    @admin.action(description="Run Box Recommendation for Selected Orders")
    def run_box_recommendation(self, request, queryset):
        count = 0
        for order in queryset:
            BoxSelector.recommend_for_order(order)
            count += 1
        self.message_user(request, f"Generated box recommendations for {count} order(s).", messages.SUCCESS)
