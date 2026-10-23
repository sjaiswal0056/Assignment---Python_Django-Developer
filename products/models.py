from django.core.exceptions import ValidationError
from django.db import models


class Product(models.Model):
    """
    Catalog product sold on the ecommerce platform.
    Stores external package dimensions and unit weight.
    """
    sku = models.CharField(max_length=50, unique=True, help_text="Stock Keeping Unit (unique product code)")
    name = models.CharField(max_length=200, help_text="Product title")
    description = models.TextField(blank=True, default="", help_text="Product description")
    category = models.CharField(max_length=100, blank=True, default="General", help_text="Product category")
    length = models.DecimalField(max_digits=8, decimal_places=2, help_text="Product length in cm")
    width = models.DecimalField(max_digits=8, decimal_places=2, help_text="Product width in cm")
    height = models.DecimalField(max_digits=8, decimal_places=2, help_text="Product height in cm")
    weight = models.DecimalField(max_digits=8, decimal_places=2, help_text="Product weight in kg")
    is_fragile = models.BooleanField(default=False, help_text="Fragile item requiring careful handling")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name', 'sku']
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return f"{self.name} ({self.sku}) - {self.dimensions_display} | {self.weight}kg"

    def clean(self):
        super().clean()
        if self.length is not None and self.length <= 0:
            raise ValidationError({'length': 'Length must be greater than zero.'})
        if self.width is not None and self.width <= 0:
            raise ValidationError({'width': 'Width must be greater than zero.'})
        if self.height is not None and self.height <= 0:
            raise ValidationError({'height': 'Height must be greater than zero.'})
        if self.weight is not None and self.weight <= 0:
            raise ValidationError({'weight': 'Weight must be greater than zero.'})

    @property
    def volume(self) -> float:
        """Volume in cubic centimeters (cm³)."""
        if self.length is None or self.width is None or self.height is None:
            return 0.0
        return float(self.length * self.width * self.height)

    @property
    def volume_liters(self) -> float:
        """Volume in liters."""
        return self.volume / 1000.0

    @property
    def dimensions_display(self) -> str:
        """Formatted string of dimensions."""
        if self.length is None or self.width is None or self.height is None:
            return "-"
        return f"{self.length} x {self.width} x {self.height} cm"

    @property
    def sorted_dimensions(self) -> list[float]:
        """Dimensions sorted in ascending order for rotational orientation comparison."""
        if self.length is None or self.width is None or self.height is None:
            return [0.0, 0.0, 0.0]
        return sorted([float(self.length), float(self.width), float(self.height)])
