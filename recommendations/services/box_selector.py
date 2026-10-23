"""
Box Selector Service.
Orchestrates candidate box filtering, cost minimization, 3D bin packing verification,
multi-box split fallback, and warehouse decision reporting.
"""

from decimal import Decimal
from typing import List, Dict, Any, Optional, Union
from boxes.models import Box
from orders.models import Order
from recommendations.services.packing_engine import PackingEngine, ItemToPack, PackingResult
from recommendations.services.explainer import ExplainerService


class BoxSelector:
    """
    Main business logic service for intelligent ecommerce box selection.
    """

    @classmethod
    def items_from_order(cls, order: Order) -> List[ItemToPack]:
        """Convert a Django Order model into individual ItemToPack objects."""
        items: List[ItemToPack] = []
        for order_item in order.items.select_related('product').all():
            product = order_item.product
            for idx in range(order_item.quantity):
                items.append(
                    ItemToPack(
                        id=f"{product.sku}_{order_item.id}_{idx + 1}",
                        name=product.name,
                        sku=product.sku,
                        length=float(product.length),
                        width=float(product.width),
                        height=float(product.height),
                        weight=float(product.weight),
                    )
                )
        return items

    @classmethod
    def items_from_raw_data(cls, items_data: List[Dict[str, Any]]) -> List[ItemToPack]:
        """Convert raw dict payload from API into ItemToPack instances."""
        items: List[ItemToPack] = []
        for i, it in enumerate(items_data):
            qty = int(it.get('quantity', 1))
            name = it.get('name', f"Item {i + 1}")
            sku = it.get('sku', f"SKU-{i + 1}")
            length = float(it['length'])
            width = float(it['width'])
            height = float(it['height'])
            weight = float(it['weight'])

            for idx in range(qty):
                items.append(
                    ItemToPack(
                        id=f"{sku}_{i + 1}_{idx + 1}",
                        name=name,
                        sku=sku,
                        length=length,
                        width=width,
                        height=height,
                        weight=weight,
                    )
                )
        return items

    @classmethod
    def select_box(
        cls,
        items: List[ItemToPack],
        candidate_boxes: Optional[List[Box]] = None,
        allow_multi_box: bool = True,
    ) -> Dict[str, Any]:
        """
        Evaluates candidate boxes for the given items and returns the optimal recommendation.

        Returns:
            Dict containing status, selected_box, boxes_used, audit_trail, metrics, and explanation.
        """
        if not items:
            return {
                'status': 'NO_FIT',
                'selected_box': None,
                'boxes_used': [],
                'total_cost': 0.0,
                'total_weight': 0.0,
                'total_volume': 0.0,
                'volume_utilization': 0.0,
                'weight_utilization': 0.0,
                'audit_trail': [],
                'explanation': "Order contains no items to pack.",
                'packing_layout': [],
            }

        total_weight = sum(item.weight for item in items)
        total_volume = sum(item.volume for item in items)

        # Retrieve active boxes if not provided
        if candidate_boxes is None:
            boxes = list(Box.objects.filter(is_active=True).all())
        else:
            boxes = list(candidate_boxes)

        if not boxes:
            return {
                'status': 'NO_FIT',
                'selected_box': None,
                'boxes_used': [],
                'total_cost': 0.0,
                'total_weight': total_weight,
                'total_volume': total_volume,
                'volume_utilization': 0.0,
                'weight_utilization': 0.0,
                'audit_trail': [],
                'explanation': "No active shipping boxes found in warehouse inventory.",
                'packing_layout': [],
            }

        # Check if any single item exceeds EVERY box in the warehouse
        for item in items:
            fits_in_any = any(
                box.can_fit_single_item(item.length, item.width, item.height) and float(box.max_weight) >= item.weight
                for box in boxes
            )
            if not fits_in_any:
                explanation = ExplainerService.generate_explanation(
                    status="NO_FIT",
                    selected_boxes=[],
                    audit_trail=[{
                        'box_name': b.name,
                        'reason': f"Item '{item.name}' ({item.length}x{item.width}x{item.height}cm, {item.weight}kg) exceeds box limits"
                    } for b in boxes[:3]],
                    total_weight=total_weight,
                    total_volume=total_volume
                )
                return {
                    'status': 'NO_FIT',
                    'selected_box': None,
                    'boxes_used': [],
                    'total_cost': 0.0,
                    'total_weight': total_weight,
                    'total_volume': total_volume,
                    'volume_utilization': 0.0,
                    'weight_utilization': 0.0,
                    'audit_trail': [{
                        'box_code': 'ALL',
                        'box_name': 'All Boxes',
                        'status': 'REJECTED',
                        'reason': f"Item '{item.name}' exceeds capacity of all available boxes.",
                    }],
                    'explanation': explanation,
                    'packing_layout': [],
                }

        # Sort candidate boxes:
        # 1. Cost ASC (cheapest box first)
        # 2. Volume ASC (tighter fit = less void fill / less dunnage)
        sorted_boxes = sorted(
            boxes,
            key=lambda b: (float(b.cost), b.volume)
        )

        audit_trail: List[Dict[str, Any]] = []
        best_single_result: Optional[PackingResult] = None
        best_box_model: Optional[Box] = None

        # Evaluate each box in order of cost
        for box in sorted_boxes:
            pack_res = PackingEngine.pack(
                box_length=float(box.length),
                box_width=float(box.width),
                box_height=float(box.height),
                box_max_weight=float(box.max_weight),
                box_cost=float(box.cost),
                box_name=box.name,
                box_code=box.code,
                items=items,
            )

            if pack_res.success:
                audit_trail.append({
                    'box_code': box.code,
                    'box_name': box.name,
                    'cost': float(box.cost),
                    'status': 'ACCEPTED',
                    'reason': f"Optimal fit! Volume utilization: {pack_res.volume_utilization_pct:.1f}%, Weight utilization: {pack_res.weight_utilization_pct:.1f}%",
                })
                best_single_result = pack_res
                best_box_model = box
                break
            else:
                audit_trail.append({
                    'box_code': box.code,
                    'box_name': box.name,
                    'cost': float(box.cost),
                    'status': 'REJECTED',
                    'reason': pack_res.rejection_reason or "Does not fit",
                })

        # If a single box fits all items
        if best_single_result and best_box_model:
            selected_boxes_data = [best_single_result.to_dict()]
            explanation = ExplainerService.generate_explanation(
                status="OPTIMAL",
                selected_boxes=selected_boxes_data,
                audit_trail=audit_trail,
                total_weight=total_weight,
                total_volume=total_volume
            )

            return {
                'status': 'OPTIMAL',
                'selected_box': best_box_model,
                'boxes_used': selected_boxes_data,
                'total_cost': float(best_box_model.cost),
                'total_weight': total_weight,
                'total_volume': total_volume,
                'volume_utilization': best_single_result.volume_utilization_pct,
                'weight_utilization': best_single_result.weight_utilization_pct,
                'audit_trail': audit_trail,
                'explanation': explanation,
                'packing_layout': [item.to_dict() for item in best_single_result.packed_items],
            }

        # If no single box fits, attempt Multi-Box Partitioning (if allowed)
        if allow_multi_box:
            multi_box_res = cls._partition_multi_box(items, sorted_boxes)
            if multi_box_res['success']:
                explanation = ExplainerService.generate_explanation(
                    status="SPLIT_REQUIRED",
                    selected_boxes=multi_box_res['boxes_used'],
                    audit_trail=audit_trail,
                    total_weight=total_weight,
                    total_volume=total_volume
                )
                return {
                    'status': 'SPLIT_REQUIRED',
                    'selected_box': None,
                    'boxes_used': multi_box_res['boxes_used'],
                    'total_cost': multi_box_res['total_cost'],
                    'total_weight': total_weight,
                    'total_volume': total_volume,
                    'volume_utilization': multi_box_res['avg_volume_utilization'],
                    'weight_utilization': multi_box_res['avg_weight_utilization'],
                    'audit_trail': audit_trail,
                    'explanation': explanation,
                    'packing_layout': multi_box_res['combined_layout'],
                }

        # If multi-box also cannot pack items or is disallowed
        explanation = ExplainerService.generate_explanation(
            status="NO_FIT",
            selected_boxes=[],
            audit_trail=audit_trail,
            total_weight=total_weight,
            total_volume=total_volume
        )
        return {
            'status': 'NO_FIT',
            'selected_box': None,
            'boxes_used': [],
            'total_cost': 0.0,
            'total_weight': total_weight,
            'total_volume': total_volume,
            'volume_utilization': 0.0,
            'weight_utilization': 0.0,
            'audit_trail': audit_trail,
            'explanation': explanation,
            'packing_layout': [],
        }

    @classmethod
    def _partition_multi_box(
        cls,
        items: List[ItemToPack],
        sorted_boxes: List[Box],
    ) -> Dict[str, Any]:
        """
        Greedy multi-box packing algorithm.
        Packs largest items first into the cheapest available box that fits them.
        """
        remaining_items = sorted(items, key=lambda it: (it.volume, it.weight), reverse=True)
        chosen_boxes: List[Dict[str, Any]] = []
        combined_layout: List[Dict[str, Any]] = []
        total_cost = 0.0

        max_iterations = len(items) + 5
        iteration = 0

        while remaining_items and iteration < max_iterations:
            iteration += 1
            box_found = False

            # Try candidate boxes from cheapest to largest
            for box in sorted_boxes:
                # Try packing as many items as possible into this box
                # Binary search / greedy subset packing
                subset_packed: List[ItemToPack] = []
                last_successful_pack: Optional[PackingResult] = None

                for candidate_item in remaining_items:
                    test_group = subset_packed + [candidate_item]
                    pack_test = PackingEngine.pack(
                        box_length=float(box.length),
                        box_width=float(box.width),
                        box_height=float(box.height),
                        box_max_weight=float(box.max_weight),
                        box_cost=float(box.cost),
                        box_name=box.name,
                        box_code=box.code,
                        items=test_group,
                    )
                    if pack_test.success:
                        subset_packed.append(candidate_item)
                        last_successful_pack = pack_test

                if subset_packed and last_successful_pack:
                    box_dict = last_successful_pack.to_dict()
                    chosen_boxes.append(box_dict)
                    total_cost += float(box.cost)

                    # Tag layout with box identifier
                    box_idx = len(chosen_boxes)
                    for p_item in last_successful_pack.packed_items:
                        item_dict = p_item.to_dict()
                        item_dict['box_index'] = box_idx
                        item_dict['box_code'] = box.code
                        combined_layout.append(item_dict)

                    # Remove packed items from remaining_items
                    for p in subset_packed:
                        remaining_items.remove(p)

                    box_found = True
                    break

            if not box_found:
                # Cannot pack remaining items even into any box
                return {'success': False}

        if remaining_items:
            return {'success': False}

        avg_vol = sum(b['volume_utilization_pct'] for b in chosen_boxes) / len(chosen_boxes) if chosen_boxes else 0.0
        avg_wt = sum(b['weight_utilization_pct'] for b in chosen_boxes) / len(chosen_boxes) if chosen_boxes else 0.0

        return {
            'success': True,
            'boxes_used': chosen_boxes,
            'total_cost': total_cost,
            'avg_volume_utilization': avg_vol,
            'avg_weight_utilization': avg_wt,
            'combined_layout': combined_layout,
        }
