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
            items = BoxSelector.items_from_order(order)
            res = BoxSelector.select_box(items)
            BoxRecommendation.objects.update_or_create(
                order=order,
                defaults={
                    'status': res['status'],
                    'selected_box': res['selected_box'],
                    'total_cost': Decimal(str(res['total_cost'])),
                    'total_weight': Decimal(str(res['total_weight'])),
                    'total_volume': res['total_volume'],
                    'volume_utilization': res['volume_utilization'],
                    'weight_utilization': res['weight_utilization'],
                    'boxes_used': res['boxes_used'],
                    'packing_layout': res['packing_layout'],
                    'audit_trail': res['audit_trail'],
                    'explanation': res['explanation'],
                }
            )
            if res['status'] == 'OPTIMAL':
                order.status = Order.Status.RECOMMENDED
                order.save()
            count += 1
        self.message_user(request, f"Generated box recommendations for {count} order(s).", messages.SUCCESS)
