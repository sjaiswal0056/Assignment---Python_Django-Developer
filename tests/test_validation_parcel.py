"""
Validation and constraint verification tests for the AI-Assisted Box Selection System.
Validates the user's test parcel (20 x 15 x 10 cm, 1.2 kg), checks all 6 item orientations,
verifies physical rejection of the Slim Book & Document Box, and ensures complete consistency
between evaluation constraints, audit trails, and 3D placement coordinates.
"""

from decimal import Decimal
from django.test import TestCase
from boxes.models import Box
from products.models import Product
from recommendations.services.box_selector import BoxSelector
from recommendations.services.packing_engine import PackingEngine, ItemToPack


class ParcelRecommendationValidationTests(TestCase):
    """
    Validation tests inspecting dimensional fit, rotation, weight limits,
    cost optimization, and rejection reasons.
    """

    def setUp(self):
        # Create standard catalog boxes matching the warehouse inventory
        self.box_xs = Box.objects.create(
            code="BOX-XS",
            name="Extra Small Padded Mailer",
            length=Decimal("15.00"),
            width=Decimal("10.00"),
            height=Decimal("5.00"),
            max_weight=Decimal("1.00"),
            cost=Decimal("0.75"),
            is_active=True,
        )
        self.box_flat = Box.objects.create(
            code="BOX-FLAT",
            name="Slim Book & Document Box",
            length=Decimal("35.00"),
            width=Decimal("26.00"),
            height=Decimal("6.00"),
            max_weight=Decimal("3.00"),
            cost=Decimal("1.10"),
            is_active=True,
        )
        self.box_s = Box.objects.create(
            code="BOX-S",
            name="Small Standard Box",
            length=Decimal("25.00"),
            width=Decimal("20.00"),
            height=Decimal("12.00"),
            max_weight=Decimal("4.00"),
            cost=Decimal("1.40"),
            is_active=True,
        )
        self.box_m = Box.objects.create(
            code="BOX-M",
            name="Medium Parcel Box",
            length=Decimal("35.00"),
            width=Decimal("28.00"),
            height=Decimal("18.00"),
            max_weight=Decimal("8.00"),
            cost=Decimal("2.60"),
            is_active=True,
        )
        self.box_l = Box.objects.create(
            code="BOX-L",
            name="Large Storage Box",
            length=Decimal("48.00"),
            width=Decimal("36.00"),
            height=Decimal("25.00"),
            max_weight=Decimal("15.00"),
            cost=Decimal("4.50"),
            is_active=True,
        )

        # The user's exact test parcel: 20 x 15 x 10 cm, 1.2 kg, volume 3,000 cm3
        self.test_parcel = ItemToPack(
            id="test_parcel_1",
            name="Test Parcel",
            sku="PARCEL-20-15-10",
            length=20.0,
            width=15.0,
            height=10.0,
            weight=1.2,
        )

    def test_optimal_recommendation_and_utilization_metrics(self):
        """
        Verify that for the test parcel (20x15x10cm, 1.2kg), Box-S is selected
        at $1.40 with exactly 50.0% volume utilization and 30.0% weight utilization.
        """
        result = BoxSelector.select_box([self.test_parcel])

        self.assertEqual(result['status'], 'OPTIMAL')
        self.assertEqual(result['selected_box'].code, 'BOX-S')
        self.assertEqual(result['total_cost'], 1.40)

        # Volume utilization: 3,000 / (25 * 20 * 12 = 6,000) = 50.0%
        self.assertAlmostEqual(result['volume_utilization'], 50.0, places=1)

        # Weight utilization: 1.2 / 4.0 = 30.0%
        self.assertAlmostEqual(result['weight_utilization'], 30.0, places=1)

        # Packing coordinates
        self.assertEqual(len(result['packing_layout']), 1)
        placed = result['packing_layout'][0]
        self.assertEqual(placed['x'], 0.0)
        self.assertEqual(placed['y'], 0.0)
        self.assertEqual(placed['z'], 0.0)
        # Rotated dimensions must fit within box bounds (25 x 20 x 12)
        self.assertLessEqual(placed['dx'], 25.0)
        self.assertLessEqual(placed['dy'], 20.0)
        self.assertLessEqual(placed['dz'], 12.0)

    def test_slim_book_box_rejection_against_all_orientations(self):
        """
        Verify that the Slim Book & Document Box (35x26x6cm, 3kg, $1.10) is rejected
        because the parcel (20x15x10cm) physically cannot fit in any of its 6 orthogonal orientations.
        """
        # Test directly via PackingEngine
        pack_res = PackingEngine.pack(
            box_length=float(self.box_flat.length),
            box_width=float(self.box_flat.width),
            box_height=float(self.box_flat.height),
            box_max_weight=float(self.box_flat.max_weight),
            box_cost=float(self.box_flat.cost),
            box_name=self.box_flat.name,
            box_code=self.box_flat.code,
            items=[self.test_parcel],
        )
        self.assertFalse(pack_res.success, "Slim Book Box must reject parcel that exceeds height")
        self.assertIn("exceeds box dimensions", pack_res.rejection_reason)
        # Rejection reason must detail the orientation conflict
        self.assertIn("minimum item dimension", pack_res.rejection_reason)

        # Verify all 6 orientations manually to prove physical impossibility:
        box_dims = (35.0, 26.0, 6.0)
        orientations = self.test_parcel.get_rotations()
        self.assertEqual(len(orientations), 6, "Cuboid with 3 unique dimensions must have 6 rotations")

        for dx, dy, dz in orientations:
            # At least one dimension must exceed the box bounds
            fits = (dx <= box_dims[0] and dy <= box_dims[1] and dz <= box_dims[2])
            self.assertFalse(fits, f"Orientation ({dx}, {dy}, {dz}) should not fit in {box_dims}")

    def test_extra_small_padded_mailer_rejection(self):
        """
        Verify Extra Small Padded Mailer (15x10x5cm, max 1.0kg, $0.75) is rejected
        for weight capacity violation (1.2kg > 1.0kg).
        """
        pack_res = PackingEngine.pack(
            box_length=float(self.box_xs.length),
            box_width=float(self.box_xs.width),
            box_height=float(self.box_xs.height),
            box_max_weight=float(self.box_xs.max_weight),
            box_cost=float(self.box_xs.cost),
            box_name=self.box_xs.name,
            box_code=self.box_xs.code,
            items=[self.test_parcel],
        )
        self.assertFalse(pack_res.success)
        self.assertIn("Exceeds max weight capacity", pack_res.rejection_reason)

    def test_every_box_evaluated_in_audit_trail(self):
        """
        Verify that EVERY active box in inventory is evaluated in the audit trail,
        including cheaper rejected boxes, the accepted box, and higher-cost skipped boxes.
        """
        result = BoxSelector.select_box([self.test_parcel])
        audit_trail = result['audit_trail']

        evaluated_codes = [b['box_code'] for b in audit_trail]
        self.assertIn("BOX-XS", evaluated_codes)
        self.assertIn("BOX-FLAT", evaluated_codes)
        self.assertIn("BOX-S", evaluated_codes)
        self.assertIn("BOX-M", evaluated_codes)
        self.assertIn("BOX-L", evaluated_codes)

        # Check statuses
        audit_xs = next(b for b in audit_trail if b['box_code'] == 'BOX-XS')
        self.assertEqual(audit_xs['status'], 'REJECTED')

        audit_flat = next(b for b in audit_trail if b['box_code'] == 'BOX-FLAT')
        self.assertEqual(audit_flat['status'], 'REJECTED')
        self.assertIn("exceeds box dimensions", audit_flat['reason'])

        audit_s = next(b for b in audit_trail if b['box_code'] == 'BOX-S')
        self.assertEqual(audit_s['status'], 'ACCEPTED')

        audit_m = next(b for b in audit_trail if b['box_code'] == 'BOX-M')
        self.assertEqual(audit_m['status'], 'SKIPPED')
        self.assertIn("saves", audit_m['reason'])

    def test_decision_rationale_consistency(self):
        """
        Verify that the generated explanation is completely consistent with the audit trail.
        """
        result = BoxSelector.select_box([self.test_parcel])
        explanation = result['explanation']

        self.assertIn("RECOMMENDATION: Use 'Small Standard Box' (BOX-S).", explanation)
        self.assertIn("Extra Small Padded Mailer ($0.75): Exceeds max weight capacity", explanation)
        self.assertIn("Slim Book & Document Box ($1.10): Item 'Test Parcel'", explanation)
        self.assertIn("Medium Parcel Box at $2.60) were avoided, saving $1.20 in packaging cost", explanation)

    def test_item_orientation_rotation_enables_fit(self):
        """
        Verify that when an item is provided in an orientation that doesn't fit (e.g. height 15cm > 12cm),
        the packing engine rotates the item so it fits inside Box-S.
        """
        # Entered as: length=10, width=20, height=15 (height 15 > box height 12)
        misoriented_item = ItemToPack(
            id="misoriented",
            name="Misoriented Parcel",
            sku="ROT-1",
            length=10.0,
            width=20.0,
            height=15.0,
            weight=1.2,
        )
        result = BoxSelector.select_box([misoriented_item])
        self.assertEqual(result['status'], 'OPTIMAL')
        self.assertEqual(result['selected_box'].code, 'BOX-S')

        placed = result['packing_layout'][0]
        # Rotated height must be <= 12 cm
        self.assertLessEqual(placed['dz'], 12.0)
        self.assertEqual(placed['original_dimensions'], [10.0, 20.0, 15.0])

    def test_cost_optimization_prioritizes_lowest_cost(self):
        """
        Verify that the engine always chooses the lowest cost box among all feasible candidates,
        even if a larger box has lower volumetric occupancy.
        """
        result = BoxSelector.select_box([self.test_parcel])
        self.assertEqual(result['selected_box'].cost, Decimal("1.40"))
        self.assertLess(result['selected_box'].cost, Decimal("2.60"))

    def test_product_32_21_12_recommends_medium_parcel_box(self):
        """
        Verify recommendation for product measuring 32 x 21 x 12 cm and weighing 1.1 kg:
        Medium Parcel Box (BOX-M at $2.60) is selected as the cheapest feasible option,
        while all cheaper boxes (BOX-XS at $0.75, BOX-FLAT at $1.10, BOX-S at $1.40)
        are rejected due to physical constraints across all rotations.
        """
        item_32 = ItemToPack(
            id="item_32_21_12",
            name="Electronics Console",
            sku="CONSOLE-32",
            length=32.0,
            width=21.0,
            height=12.0,
            weight=1.1,
        )
        result = BoxSelector.select_box([item_32])

        self.assertEqual(result['status'], 'OPTIMAL')
        self.assertEqual(result['selected_box'].code, 'BOX-M')
        self.assertEqual(result['total_cost'], 2.60)

        # Volume utilization: (32 * 21 * 12 = 8,064) / (35 * 28 * 18 = 17,640) = 45.71%
        self.assertAlmostEqual(result['volume_utilization'], 45.7, places=1)
        # Weight utilization: 1.1 / 8.0 = 13.75%
        self.assertAlmostEqual(result['weight_utilization'], 13.8, places=1)

        # Check audit trail rejections for cheaper options
        audit_trail = {b['box_code']: b for b in result['audit_trail']}
        self.assertEqual(audit_trail['BOX-XS']['status'], 'REJECTED')
        self.assertIn("max weight capacity", audit_trail['BOX-XS']['reason'])

        self.assertEqual(audit_trail['BOX-FLAT']['status'], 'REJECTED')
        self.assertIn("Exceeds internal volume", audit_trail['BOX-FLAT']['reason'])

        self.assertEqual(audit_trail['BOX-S']['status'], 'REJECTED')
        self.assertIn("Exceeds internal volume", audit_trail['BOX-S']['reason'])

        self.assertEqual(audit_trail['BOX-M']['status'], 'ACCEPTED')

    def test_catalog_product_vs_custom_item_equivalence(self):
        """
        Verify that selecting a catalog product and adding a custom item with
        identical dimensions (32 x 21 x 12 cm, 1.1 kg) produce identical feasibility,
        selected box, status, packaging cost, and utilization.
        """
        # 1. Catalog product simulation
        catalog_product = Product.objects.create(
            sku="SKU-CATALOG-32",
            name="Catalog Item 32x21x12",
            length=Decimal("32.00"),
            width=Decimal("21.00"),
            height=Decimal("12.00"),
            weight=Decimal("1.10"),
        )
        catalog_raw = [{
            'name': catalog_product.name,
            'sku': catalog_product.sku,
            'length': float(catalog_product.length),
            'width': float(catalog_product.width),
            'height': float(catalog_product.height),
            'weight': float(catalog_product.weight),
            'quantity': 1,
        }]
        catalog_items = BoxSelector.items_from_raw_data(catalog_raw)
        catalog_result = BoxSelector.select_box(catalog_items)

        # 2. Custom item simulation (identical dimensions)
        custom_raw = [{
            'name': 'Custom Parcel 32x21x12',
            'sku': 'CUSTOM-3221',
            'length': 32.0,
            'width': 21.0,
            'height': 12.0,
            'weight': 1.1,
            'quantity': 1,
        }]
        custom_items = BoxSelector.items_from_raw_data(custom_raw)
        custom_result = BoxSelector.select_box(custom_items)

        # Assert identical outcomes
        self.assertEqual(catalog_result['status'], custom_result['status'])
        self.assertEqual(catalog_result['selected_box'].code, custom_result['selected_box'].code)
        self.assertEqual(catalog_result['total_cost'], custom_result['total_cost'])
        self.assertEqual(catalog_result['volume_utilization'], custom_result['volume_utilization'])
        self.assertEqual(catalog_result['weight_utilization'], custom_result['weight_utilization'])
        self.assertEqual(len(catalog_result['audit_trail']), len(custom_result['audit_trail']))
