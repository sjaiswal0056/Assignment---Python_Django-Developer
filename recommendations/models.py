from decimal import Decimal
from django.db import models
from boxes.models import Box
from orders.models import Order


class BoxRecommendation(models.Model):
    """
    Persisted result of a box recommendation algorithm run.
    Contains the recommended box(es), packing layout, cost, utilization,
    and a clear explanation for warehouse personnel.
    """
    class RecommendationStatus(models.TextChoices):
        OPTIMAL = 'OPTIMAL', 'Optimal Single Box Found'
        SPLIT_REQUIRED = 'SPLIT_REQUIRED', 'Split Required (Multi-Box)'
        NO_FIT = 'NO_FIT', 'No Suitable Box Available'
        OVERSIZED = 'OVERSIZED', 'Oversized / Special Freight'
        WEIGHT_EXCEEDED = 'WEIGHT_EXCEEDED', 'Weight Limit Exceeded'
        ERROR = 'ERROR', 'Calculation Error'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True, related_name='recommendations')
    status = models.CharField(max_length=30, choices=RecommendationStatus.choices, default=RecommendationStatus.OPTIMAL)
    selected_box = models.ForeignKey(Box, on_delete=models.SET_NULL, null=True, blank=True, related_name='selected_recommendations')
    
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Total packaging cost")
    total_weight = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), help_text="Total items weight in kg")
    total_volume = models.FloatField(default=0.0, help_text="Total items volume in cm³")
    
    volume_utilization = models.FloatField(default=0.0, help_text="Percentage of box volume utilized (0-100%)")
    weight_utilization = models.FloatField(default=0.0, help_text="Percentage of box weight capacity utilized (0-100%)")
    
    # Detailed packing results
    boxes_used = models.JSONField(default=list, help_text="List of box details used in this recommendation")
    packing_layout = models.JSONField(default=list, help_text="3D coordinates and placement of packed items")
    audit_trail = models.JSONField(default=list, help_text="List of candidate boxes evaluated and rejection reasons")
    explanation = models.TextField(help_text="Human-readable explanation of why this recommendation was chosen")

    shipment_fingerprint = models.CharField(max_length=64, blank=True, default="", help_text="SHA256 fingerprint of the order items when computed")
    is_stale = models.BooleanField(default=False, help_text="Whether this recommendation is invalidated by order item changes")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Box Recommendation"
        verbose_name_plural = "Box Recommendations"

    def __str__(self):
        target = self.order.order_number if self.order else "Ad-hoc Recommendation"
        box_name = self.selected_box.name if self.selected_box else f"{len(self.boxes_used)} Box(es)"
        return f"[{self.status}] {target} -> {box_name} (${self.total_cost})"
