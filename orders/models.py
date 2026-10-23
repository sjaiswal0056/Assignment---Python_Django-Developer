from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from products.models import Product


class Order(models.Model):
    """
    Customer order placed on the ecommerce platform.
    Contains one or more order items to be packaged by the warehouse.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Box Recommendation'
        RECOMMENDED = 'RECOMMENDED', 'Box Recommended'
        PACKED = 'PACKED', 'Packed'
        SHIPPED = 'SHIPPED', 'Shipped'

    order_number = models.CharField(max_length=50, unique=True, help_text="Unique Order identifier (e.g. ORD-1001)")
    customer_name = models.CharField(max_length=200, help_text="Customer full name")
    customer_email = models.EmailField(blank=True, default="", help_text="Customer email address")
    shipping_address = models.TextField(blank=True, default="", help_text="Destination address")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"{self.order_number} - {self.customer_name} ({self.get_status_display()})"

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
