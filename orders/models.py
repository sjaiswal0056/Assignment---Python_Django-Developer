import hashlib
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from products.models import Product


class Order(models.Model):
    """
    Customer order placed on the ecommerce platform.
    Contains one or more order items to be packaged by the warehouse.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Box Recommendation'
        RECOMMENDED = 'RECOMMENDED', 'Box Recommended'
        SPLIT_REQUIRED = 'SPLIT_REQUIRED', 'Split Required (Multi-Box)'
        OVERSIZED = 'OVERSIZED', 'Oversized / Special Freight'
        WEIGHT_EXCEEDED = 'WEIGHT_EXCEEDED', 'Weight Limit Exceeded'
        ERROR = 'ERROR', 'Calculation Error'
        PACKED = 'PACKED', 'Packed'
        SHIPPED = 'SHIPPED', 'Shipped'

    order_number = models.CharField(max_length=50, unique=True, help_text="Unique Order identifier (e.g. ORD-1001)")
    customer_name = models.CharField(max_length=200, help_text="Customer full name")
    customer_email = models.EmailField(blank=True, default="", help_text="Customer email address")
    shipping_address = models.TextField(blank=True, default="", help_text="Destination address")
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"{self.order_number} - {self.customer_name} ({self.get_status_display()})"

    def get_shipment_fingerprint(self) -> str:
        """
        Generate a deterministic SHA256 hash of all items in this order
        including product IDs, quantities, dimensions, and weights.
        Used to detect shipment modifications and invalidate stale recommendations.
        """
        if not self.pk:
            return ""
        items_data = []
        for item in self.items.select_related('product').order_by('product__sku'):
            p = item.product
            items_data.append(
                f"{p.id}:{p.sku}:{item.quantity}:{float(p.length)}x{float(p.width)}x{float(p.height)}:{float(p.weight)}"
            )
        raw_str = "|".join(items_data)
        return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

    @property
    def current_recommendation(self):
        """
        Returns the latest valid, non-stale recommendation that matches
        the order's exact current shipment configuration.
        """
        if not self.pk:
            return None
        rec = self.recommendations.filter(is_stale=False).first()
        if not rec:
            return None
        current_fp = self.get_shipment_fingerprint()
        if rec.shipment_fingerprint and rec.shipment_fingerprint != current_fp:
            return None
        return rec

    @property
    def is_recommendation_stale(self) -> bool:
        """Returns True if order items have changed since recommendation was computed."""
        if not self.pk:
            return False
        rec = self.recommendations.first()
        if not rec:
            return False
        if rec.is_stale:
            return True
        current_fp = self.get_shipment_fingerprint()
        return bool(rec.shipment_fingerprint and rec.shipment_fingerprint != current_fp)

    @property
    def packaging_cost(self):
        """
        Packaging cost of the current active recommendation.
        Returns None if pending, stale, oversized, overweight, or failed.
        """
        if self.is_recommendation_stale:
            return None
        rec = self.current_recommendation
        if not rec:
            return None
        if rec.status in ['OVERSIZED', 'WEIGHT_EXCEEDED', 'ERROR', 'NO_FIT']:
            return None
        return rec.total_cost if rec.total_cost > Decimal('0.00') else None

    @property
    def total_weight(self) -> Decimal:
        """Total weight of all products in this order in kg."""
        if not self.pk:
            return Decimal('0.00')
        return sum((item.product.weight * item.quantity for item in self.items.select_related('product')), Decimal('0.00'))

    @property
    def total_volume(self) -> float:
        """Total volume of all products in this order in cm³."""
        if not self.pk:
            return 0.0
        return sum((item.product.volume * item.quantity for item in self.items.select_related('product')), 0.0)

    @property
    def total_quantity(self) -> int:
        """Total number of individual item units in this order."""
        if not self.pk:
            return 0
        return sum((item.quantity for item in self.items.all()), 0)


class OrderItem(models.Model):
    """
    Individual item and quantity within an order.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1, help_text="Quantity of this product")

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        unique_together = ('order', 'product')

    def __str__(self):
        return f"{self.quantity}x {self.product.name} ({self.product.sku})"

    def clean(self):
        super().clean()
        if self.quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be at least 1.'})

    @property
    def total_weight(self) -> Decimal:
        if not hasattr(self, 'product') or self.product is None or self.quantity is None or getattr(self.product, 'weight', None) is None:
            return Decimal('0.00')
        return self.product.weight * self.quantity

    @property
    def total_volume(self) -> float:
        if not hasattr(self, 'product') or self.product is None or self.quantity is None:
            return 0.0
        return self.product.volume * self.quantity


# --- Signals to invalidate stale recommendations on item/product edits ---

@receiver([post_save, post_delete], sender=OrderItem)
def invalidate_order_recommendations_on_item_change(sender, instance, **kwargs):
    """
    When an order's items change, invalidate existing recommendations
    and reset the order's status to PENDING.
    """
    if instance.order_id:
        from recommendations.models import BoxRecommendation
        BoxRecommendation.objects.filter(order_id=instance.order_id, is_stale=False).update(is_stale=True)
        Order.objects.filter(id=instance.order_id).exclude(
            status__in=[Order.Status.PACKED, Order.Status.SHIPPED]
        ).update(status=Order.Status.PENDING)


@receiver(post_save, sender=Product)
def invalidate_order_recommendations_on_product_change(sender, instance, **kwargs):
    """
    When a product's dimensions or weight change, invalidate recommendations
    for all pending/recommended orders containing that product.
    """
    from recommendations.models import BoxRecommendation
    order_ids = list(OrderItem.objects.filter(product=instance).values_list('order_id', flat=True).distinct())
    if order_ids:
        BoxRecommendation.objects.filter(order_id__in=order_ids, is_stale=False).update(is_stale=True)
        Order.objects.filter(id__in=order_ids).exclude(
            status__in=[Order.Status.PACKED, Order.Status.SHIPPED]
        ).update(status=Order.Status.PENDING)
