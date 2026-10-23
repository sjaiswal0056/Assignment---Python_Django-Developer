from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models


class Box(models.Model):
    """
    Shipping box packaging available in the warehouse.
    Stores internal dimensions, maximum weight capacity, and unit cost.
    """
    code = models.CharField(max_length=50, unique=True, help_text="Unique SKU/Code for the box (e.g., BOX-S, BOX-M)")
    name = models.CharField(max_length=150, help_text="Descriptive name (e.g., 'Small Shipping Box')")
    length = models.DecimalField(max_digits=8, decimal_places=2, help_text="Internal length in cm")
    width = models.DecimalField(max_digits=8, decimal_places=2, help_text="Internal width in cm")
    height = models.DecimalField(max_digits=8, decimal_places=2, help_text="Internal height in cm")
    max_weight = models.DecimalField(max_digits=8, decimal_places=2, help_text="Maximum weight capacity in kg")
    empty_weight = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), help_text="Tare weight of the box itself in kg")
    cost = models.DecimalField(max_digits=8, decimal_places=2, help_text="Cost per box unit")
    is_active = models.BooleanField(default=True, help_text="Whether this box is currently available for packaging")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['cost', 'length', 'width', 'height']
        verbose_name = "Shipping Box"
        verbose_name_plural = "Shipping Boxes"

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.dimensions_display} | Max {self.max_weight}kg | ${self.cost}"

    def clean(self):
        super().clean()
        if self.length is not None and self.length <= 0:
            raise ValidationError({'length': 'Length must be greater than zero.'})
        if self.width is not None and self.width <= 0:
            raise ValidationError({'width': 'Width must be greater than zero.'})
        if self.height is not None and self.height <= 0:
            raise ValidationError({'height': 'Height must be greater than zero.'})
        if self.max_weight is not None and self.max_weight <= 0:
            raise ValidationError({'max_weight': 'Max weight must be greater than zero.'})
        if self.cost is not None and self.cost < 0:
            raise ValidationError({'cost': 'Cost cannot be negative.'})

    @property
    def volume(self) -> float:
        """Internal volume in cubic centimeters (cm³)."""
        if self.length is None or self.width is None or self.height is None:
            return 0.0
        return float(self.length * self.width * self.height)

    @property
    def volume_liters(self) -> float:
        """Internal volume in liters."""
        return self.volume / 1000.0

    @property
    def dimensions_display(self) -> str:
        """Formatted string of dimensions."""
        if self.length is None or self.width is None or self.height is None:
            return "-"
        return f"{self.length} x {self.width} x {self.height} cm"

    def can_fit_single_item(self, item_length: float, item_width: float, item_height: float) -> bool:
        """
        Check if a single item's dimensions can physically fit inside this box,
        considering all 6 possible 3D orthogonal orientations.
        """
        if self.length is None or self.width is None or self.height is None:
            return False
        item_dims = sorted([float(item_length), float(item_width), float(item_height)])
        box_dims = sorted([float(self.length), float(self.width), float(self.height)])
        return (
            item_dims[0] <= box_dims[0] and
            item_dims[1] <= box_dims[1] and
            item_dims[2] <= box_dims[2]
        )
