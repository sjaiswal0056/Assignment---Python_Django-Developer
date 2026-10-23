from django.contrib import admin
from products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'dimensions_display', 'weight', 'volume_liters_display', 'is_fragile')
    list_filter = ('category', 'is_fragile')
    search_fields = ('name', 'sku')
    ordering = ('name',)
    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        return ('created_at', 'updated_at', 'volume', 'volume_liters')

    @admin.display(description="Volume (L)")
    def volume_liters_display(self, obj):
        return f"{obj.volume_liters:.2f} L" if obj else "-"
