from django.test import SimpleTestCase
from recommendations.services.packing_engine import PackingEngine, ItemToPack, PackedItem


class PackingEngineTests(SimpleTestCase):
    """
    Tests for the 3D Bin Packing Extreme Points engine.
    """

    def test_single_item_fits_exact_dimensions(self):
        item = ItemToPack(
            id="1", name="Cube", sku="SKU-CUBE",
            length=10.0, width=10.0, height=10.0, weight=1.0
        )
        res = PackingEngine.pack(
            box_length=10.0, box_width=10.0, box_height=10.0,
            box_max_weight=5.0, box_cost=1.0,
            box_name="Cube Box", box_code="BX-CUBE",
            items=[item]
        )
        self.assertTrue(res.success)
        self.assertEqual(len(res.packed_items), 1)
        self.assertAlmostEqual(res.volume_utilization_pct, 100.0, places=1)

    def test_item_fits_with_3d_rotation(self):
        # Item: 30 x 10 x 5. Box: 10 x 30 x 5.
        # Should fit by rotating length and width!
        item = ItemToPack(
            id="1", name="Rotated Item", sku="SKU-ROT",
            length=30.0, width=10.0, height=5.0, weight=1.0
        )
        res = PackingEngine.pack(
            box_length=10.0, box_width=30.0, box_height=5.0,
            box_max_weight=5.0, box_cost=1.5,
            box_name="Oriented Box", box_code="BX-ROT",
            items=[item]
        )
        self.assertTrue(res.success)
        self.assertEqual(len(res.packed_items), 1)

    def test_item_rejected_when_exceeding_weight_capacity(self):
        item = ItemToPack(
            id="1", name="Heavy Lead Block", sku="SKU-HEAVY",
            length=5.0, width=5.0, height=5.0, weight=10.0
        )
        res = PackingEngine.pack(
            box_length=20.0, box_width=20.0, box_height=20.0,
            box_max_weight=5.0, box_cost=1.0, # max weight is 5.0, item is 10.0
            box_name="Light Box", box_code="BX-LT",
            items=[item]
        )
        self.assertFalse(res.success)
        self.assertIn("Exceeds max weight capacity", res.rejection_reason)

    def test_item_rejected_when_exceeding_volume(self):
        item = ItemToPack(
            id="1", name="Big Foam Block", sku="SKU-FOAM",
            length=20.0, width=20.0, height=20.0, weight=0.5 # 8000 cm3
        )
        res = PackingEngine.pack(
            box_length=10.0, box_width=10.0, box_height=10.0, # 1000 cm3
            box_max_weight=10.0, box_cost=1.0,
            box_name="Small Box", box_code="BX-SM",
            items=[item]
        )
        self.assertFalse(res.success)
        self.assertIn("Exceeds internal volume", res.rejection_reason)

    def test_item_rejected_when_single_dimension_too_long(self):
        # 50cm rod in 20x20x20 box (volume of rod is tiny, but cannot fit physically)
        rod = ItemToPack(
            id="1", name="Long Curtain Rod", sku="SKU-ROD",
            length=50.0, width=2.0, height=2.0, weight=0.5
        )
        res = PackingEngine.pack(
            box_length=20.0, box_width=20.0, box_height=20.0,
            box_max_weight=10.0, box_cost=2.0,
            box_name="Square Box", box_code="BX-SQ",
            items=[rod]
        )
        self.assertFalse(res.success)
        self.assertIn("exceeds box dimensions", res.rejection_reason)

    def test_multi_item_packing_non_overlapping(self):
        # Pack 3 distinct items side-by-side
        items = [
            ItemToPack(id="1", name="Item A", sku="A", length=10.0, width=10.0, height=5.0, weight=1.0),
            ItemToPack(id="2", name="Item B", sku="B", length=10.0, width=10.0, height=5.0, weight=1.0),
            ItemToPack(id="3", name="Item C", sku="C", length=10.0, width=10.0, height=5.0, weight=1.0),
        ]
        # Box is 10 x 10 x 15 (can stack 3 items of height 5)
        res = PackingEngine.pack(
            box_length=10.0, box_width=10.0, box_height=15.0,
            box_max_weight=10.0, box_cost=2.0,
            box_name="Stack Box", box_code="BX-STK",
            items=items
        )
        self.assertTrue(res.success)
        self.assertEqual(len(res.packed_items), 3)

        # Verify no items overlap
        p1, p2, p3 = res.packed_items
        self.assertFalse(p1.overlaps_with(p2.x, p2.y, p2.z, p2.dx, p2.dy, p2.dz))
        self.assertFalse(p1.overlaps_with(p3.x, p3.y, p3.z, p3.dx, p3.dy, p3.dz))
        self.assertFalse(p2.overlaps_with(p3.x, p3.y, p3.z, p3.dx, p3.dy, p3.dz))

    def test_spatial_collision_failure(self):
        # Two bulky items whose combined volume is less than box volume,
        # but their dimensions prevent both from fitting simultaneously.
        # Box: 20 x 20 x 20 (8,000 cm3)
        # Item 1: 18 x 18 x 15 (4,860 cm3)
        # Item 2: 18 x 18 x 15 (4,860 cm3)
        # Total volume = 9,720 cm3 > 8,000 cm3 -> rejected by volume.
        # Now let's test where volume DOES fit, but shapes collide:
        # Box: 30 x 10 x 10 (3,000 cm3)
        # Item 1: 20 x 9 x 9 (1,620 cm3)
        # Item 2: 20 x 9 x 9 (1,620 cm3)
        # Total volume = 3,240 cm3 > 3000 cm3.
        # What about Box: 25 x 10 x 10 (2500 cm3)
        # Item 1: 20 x 8 x 8 (1280 cm3)
        # Item 2: 20 x 8 x 8 (1280 cm3)
        # Total volume = 2560 cm3 > 2500 cm3.
        # What about Box: 25 x 15 x 10 (3,750 cm3)
        # Item 1: 20 x 10 x 8 (1600 cm3)
        # Item 2: 20 x 10 x 8 (1600 cm3)
        # Total volume = 3200 cm3 < 3750 cm3 (volume passes!).
        # But along X: 20 + 20 = 40 > 25 (cannot place side by side along X).
        # Along Y: 10 + 10 = 20 > 15 (cannot place side by side along Y).
        # Along Z: 8 + 8 = 16 > 10 (cannot stack along Z).
        # So physically IMPOSSIBLE to pack both, even though volume is only 3200/3750 = 85.3%!
        item1 = ItemToPack(id="1", name="Block A", sku="A", length=20.0, width=10.0, height=8.0, weight=1.0)
        item2 = ItemToPack(id="2", name="Block B", sku="B", length=20.0, width=10.0, height=8.0, weight=1.0)
        res = PackingEngine.pack(
            box_length=25.0, box_width=15.0, box_height=10.0,
            box_max_weight=10.0, box_cost=3.0,
            box_name="Tricky Box", box_code="BX-TRICKY",
            items=[item1, item2]
        )
        self.assertFalse(res.success)
        self.assertIn("Spatial arrangement collision", res.rejection_reason)
