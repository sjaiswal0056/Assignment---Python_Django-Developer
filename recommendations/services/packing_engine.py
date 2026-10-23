"""
3D Bin Packing Engine using the Extreme Points (EP-3D-BPP) Heuristic.

Solves the orthogonal 3D packing problem for cuboid items with 6 rotational degrees
of freedom, ensuring no overlapping items and full containment within box boundaries.
"""

from dataclasses import dataclass, field
from itertools import permutations
from typing import List, Tuple, Optional, Dict, Any


@dataclass
class ItemToPack:
    id: str
    name: str
    sku: str
    length: float
    width: float
    height: float
    weight: float

    @property
    def volume(self) -> float:
        return self.length * self.width * self.height

    @property
    def max_dimension(self) -> float:
        return max(self.length, self.width, self.height)

    def get_rotations(self) -> List[Tuple[float, float, float]]:
        """
        Return all unique orthogonal 3D rotations (dx, dy, dz).
        For general cuboids, up to 6 orientations exist.
        """
        dims = (self.length, self.width, self.height)
        unique_orientations = sorted(list(set(permutations(dims))), reverse=True)
        return unique_orientations


@dataclass
class PackedItem:
    id: str
    name: str
    sku: str
    x: float
    y: float
    z: float
    dx: float
    dy: float
    dz: float
    weight: float
    original_dimensions: Tuple[float, float, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'x': round(self.x, 2),
            'y': round(self.y, 2),
            'z': round(self.z, 2),
            'dx': round(self.dx, 2),
            'dy': round(self.dy, 2),
            'dz': round(self.dz, 2),
            'weight': round(self.weight, 2),
            'original_dimensions': [round(d, 2) for d in self.original_dimensions],
        }

    def overlaps_with(self, x: float, y: float, z: float, dx: float, dy: float, dz: float, eps: float = 1e-5) -> bool:
        """
        Check if another cuboid intersects with this packed item.
        Touching boundaries are allowed (non-overlapping).
        """
        if (x + dx <= self.x + eps) or (self.x + self.dx <= x + eps):
            return False
        if (y + dy <= self.y + eps) or (self.y + self.dy <= y + eps):
            return False
        if (z + dz <= self.z + eps) or (self.z + self.dz <= z + eps):
            return False
        return True


@dataclass
class PackingResult:
    success: bool
    box_code: str
    box_name: str
    box_dimensions: Tuple[float, float, float]
    box_max_weight: float
    box_cost: float
    packed_items: List[PackedItem] = field(default_factory=list)
    unpacked_items: List[ItemToPack] = field(default_factory=list)
    total_packed_weight: float = 0.0
    total_packed_volume: float = 0.0
    volume_utilization_pct: float = 0.0
    weight_utilization_pct: float = 0.0
    rejection_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'box_code': self.box_code,
            'box_name': self.box_name,
            'box_dimensions': {
                'length': self.box_dimensions[0],
                'width': self.box_dimensions[1],
                'height': self.box_dimensions[2],
            },
            'box_max_weight': self.box_max_weight,
            'box_cost': self.box_cost,
            'packed_items': [item.to_dict() for item in self.packed_items],
            'unpacked_items': [
                {
                    'id': u.id,
                    'name': u.name,
                    'sku': u.sku,
                    'dimensions': [u.length, u.width, u.height],
                    'weight': u.weight,
                }
                for u in self.unpacked_items
            ],
            'total_packed_weight': round(self.total_packed_weight, 2),
            'total_packed_volume': round(self.total_packed_volume, 2),
            'volume_utilization_pct': round(self.volume_utilization_pct, 2),
            'weight_utilization_pct': round(self.weight_utilization_pct, 2),
            'rejection_reason': self.rejection_reason,
        }


class PackingEngine:
    """
    3D Bin Packing implementation using Extreme Points heuristic.
    Generates non-overlapping placements of 3D items inside a bounding box.
    """

    @staticmethod
    def pack(
        box_length: float,
        box_width: float,
        box_height: float,
        box_max_weight: float,
        box_cost: float,
        box_name: str,
        box_code: str,
        items: List[ItemToPack],
    ) -> PackingResult:
        """
        Attempt to pack all items into the specified box dimensions and weight limit.
        """
        box_vol = float(box_length * box_width * box_height)
        box_dims = (float(box_length), float(box_width), float(box_height))
        total_items_weight = sum(item.weight for item in items)
        total_items_vol = sum(item.volume for item in items)

        # Pre-check 1: Total weight capacity
        if total_items_weight > box_max_weight + 1e-5:
            return PackingResult(
                success=False,
                box_code=box_code,
                box_name=box_name,
                box_dimensions=box_dims,
                box_max_weight=box_max_weight,
                box_cost=box_cost,
                unpacked_items=items,
                rejection_reason=f"Exceeds max weight capacity: items weigh {total_items_weight:.2f}kg, box max is {box_max_weight:.2f}kg."
            )

        # Pre-check 2: Total volume capacity
        if total_items_vol > box_vol + 1e-5:
            return PackingResult(
                success=False,
                box_code=box_code,
                box_name=box_name,
                box_dimensions=box_dims,
                box_max_weight=box_max_weight,
                box_cost=box_cost,
                unpacked_items=items,
                rejection_reason=f"Exceeds internal volume: items volume is {total_items_vol:.0f} cm³, box volume is {box_vol:.0f} cm³."
            )

        # Pre-check 3: Single item boundary fit (every item must fit alone in at least one orientation)
        sorted_box = sorted([box_length, box_width, box_height])
        for item in items:
            sorted_item = sorted([item.length, item.width, item.height])
            if (sorted_item[0] > sorted_box[0] or
                sorted_item[1] > sorted_box[1] or
                sorted_item[2] > sorted_box[2]):
                if sorted_item[0] > sorted_box[0]:
                    reason_detail = f"minimum item dimension {sorted_item[0]:.1f}cm exceeds box height/minimum limit {sorted_box[0]:.1f}cm"
                elif sorted_item[2] > sorted_box[2]:
                    reason_detail = f"maximum item dimension {sorted_item[2]:.1f}cm exceeds box length/maximum limit {sorted_box[2]:.1f}cm"
                else:
                    reason_detail = f"intermediate item dimension {sorted_item[1]:.1f}cm exceeds box width limit {sorted_box[1]:.1f}cm"

                return PackingResult(
                    success=False,
                    box_code=box_code,
                    box_name=box_name,
                    box_dimensions=box_dims,
                    box_max_weight=box_max_weight,
                    box_cost=box_cost,
                    unpacked_items=items,
                    rejection_reason=f"Item '{item.name}' ({item.length:.1f}x{item.width:.1f}x{item.height:.1f}cm) exceeds box dimensions ({box_length:.1f}x{box_width:.1f}x{box_height:.1f}cm): {reason_detail} in all orientations."
                )

        # Sort items using Best-Fit Decreasing strategy:
        # Largest volume first, then largest max dimension, then weight
        sorted_items = sorted(
            items,
            key=lambda it: (it.volume, it.max_dimension, it.weight),
            reverse=True
        )

        packed_items: List[PackedItem] = []
        extreme_points: List[Tuple[float, float, float]] = [(0.0, 0.0, 0.0)]

        for item in sorted_items:
            placed = False
            best_placement: Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = None

            # Sort extreme points: lowest z first (stability/gravity), then y, then x
            extreme_points.sort(key=lambda pt: (pt[2], pt[1], pt[0]))

            for pt in extreme_points:
                px, py, pz = pt

                # Test all unique orthogonal rotations
                for dx, dy, dz in item.get_rotations():
                    # 1. Box boundary check
                    if (px + dx > box_length + 1e-5 or
                        py + dy > box_width + 1e-5 or
                        pz + dz > box_height + 1e-5):
                        continue

                    # 2. Overlap check against all already placed items
                    overlaps = False
                    for placed_item in packed_items:
                        if placed_item.overlaps_with(px, py, pz, dx, dy, dz):
                            overlaps = True
                            break

                    if not overlaps:
                        best_placement = (pt, (dx, dy, dz))
                        placed = True
                        break

                if placed:
                    break

            if not placed or best_placement is None:
                # Failed to place this item in this box
                return PackingResult(
                    success=False,
                    box_code=box_code,
                    box_name=box_name,
                    box_dimensions=box_dims,
                    box_max_weight=box_max_weight,
                    box_cost=box_cost,
                    packed_items=packed_items,
                    unpacked_items=[item] + [it for it in sorted_items if it not in packed_items and it != item],
                    rejection_reason=f"Spatial arrangement collision: item '{item.name}' could not be fitted without overlapping."
                )

            # Record placed item
            (pt, (dx, dy, dz)) = best_placement
            px, py, pz = pt
            new_packed = PackedItem(
                id=item.id,
                name=item.name,
                sku=item.sku,
                x=px,
                y=py,
                z=pz,
                dx=dx,
                dy=dy,
                dz=dz,
                weight=item.weight,
                original_dimensions=(item.length, item.width, item.height)
            )
            packed_items.append(new_packed)

            # Update extreme points
            extreme_points.remove(pt)

            # Generate new potential extreme points
            new_candidates = [
                (px + dx, py, pz),
                (px, py + dy, pz),
                (px, py, pz + dz),
            ]

            # Additional projections against other placed items
            for p_item in packed_items[:-1]:
                if p_item.x + p_item.dx <= box_length and p_item.y + p_item.dy <= box_width:
                    new_candidates.append((p_item.x + p_item.dx, py, pz))
                    new_candidates.append((px, p_item.y + p_item.dy, pz))

            for cand in new_candidates:
                cx, cy, cz = round(cand[0], 4), round(cand[1], 4), round(cand[2], 4)
                # Must be within box bounds
                if cx >= box_length or cy >= box_width or cz >= box_height:
                    continue

                # Must not be inside any placed item
                inside_any = False
                for p_item in packed_items:
                    eps = 1e-4
                    if (p_item.x + eps <= cx < p_item.x + p_item.dx - eps and
                        p_item.y + eps <= cy < p_item.y + p_item.dy - eps and
                        p_item.z + eps <= cz < p_item.z + p_item.dz - eps):
                        inside_any = True
                        break

                if not inside_any and (cx, cy, cz) not in extreme_points:
                    extreme_points.append((cx, cy, cz))

        # Successfully packed all items!
        vol_util = (total_items_vol / box_vol) * 100.0 if box_vol > 0 else 0.0
        wt_util = (total_items_weight / box_max_weight) * 100.0 if box_max_weight > 0 else 0.0

        return PackingResult(
            success=True,
            box_code=box_code,
            box_name=box_name,
            box_dimensions=box_dims,
            box_max_weight=box_max_weight,
            box_cost=box_cost,
            packed_items=packed_items,
            unpacked_items=[],
            total_packed_weight=total_items_weight,
            total_packed_volume=total_items_vol,
            volume_utilization_pct=vol_util,
            weight_utilization_pct=wt_util,
            rejection_reason=None
        )
