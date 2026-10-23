from django.contrib import admin
from boxes.models import Box


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'dimensions_display', 'max_weight', 'cost', 'volume_liters_display', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('cost',)
    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        return ('created_at', 'updated_at', 'volume', 'volume_liters')

    @admin.display(description="Volume (L)")
    def volume_liters_display(self, obj):
        return f"{obj.volume_liters:.2f} L" if obj else "-"
