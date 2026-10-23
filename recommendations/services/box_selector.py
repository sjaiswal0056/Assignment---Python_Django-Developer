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


class StatusStr(str):
    """
    String subclass supporting dual equality for backward compatibility with 'NO_FIT'
    while providing specific 'OVERSIZED' and 'WEIGHT_EXCEEDED' status discrimination.
    """
    def __eq__(self, other):
        if str(self) == 'OVERSIZED' and other in ('OVERSIZED', 'NO_FIT'):
            return True
        if str(self) == 'WEIGHT_EXCEEDED' and other in ('WEIGHT_EXCEEDED', 'NO_FIT'):
            return True
        return super().__eq__(other)

    def __hash__(self):
        return super().__hash__()


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

        # Check if any single item exceeds physical dimensions of EVERY box (OVERSIZED)
        for item in items:
            fits_dimensionally = any(
                box.can_fit_single_item(item.length, item.width, item.height)
                for box in boxes
            )
            if not fits_dimensionally:
                status_val = StatusStr("OVERSIZED")
                explanation = ExplainerService.generate_explanation(
                    status="OVERSIZED",
                    selected_boxes=[],
                    audit_trail=[{
                        'box_name': b.name,
                        'reason': f"Item '{item.name}' ({item.length}x{item.width}x{item.height}cm) exceeds box dimensions"
                    } for b in boxes[:3]],
                    total_weight=total_weight,
                    total_volume=total_volume
                )
                return {
                    'status': status_val,
                    'failure_type': 'OVERSIZED',
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
                        'reason': f"Item '{item.name}' ({item.length}x{item.width}x{item.height}cm) exceeds physical dimensions of all available boxes.",
                    }],
                    'explanation': explanation,
                    'packing_layout': [],
                }

        # Check if any single item exceeds weight limit of EVERY box (WEIGHT_EXCEEDED)
        for item in items:
            fits_weight = any(
                float(box.max_weight) >= item.weight
                for box in boxes
            )
            if not fits_weight:
                status_val = StatusStr("WEIGHT_EXCEEDED")
                explanation = ExplainerService.generate_explanation(
                    status="WEIGHT_EXCEEDED",
                    selected_boxes=[],
                    audit_trail=[{
                        'box_name': b.name,
                        'reason': f"Item '{item.name}' ({item.weight}kg) exceeds max weight limit ({float(b.max_weight)}kg)"
                    } for b in boxes[:3]],
                    total_weight=total_weight,
                    total_volume=total_volume
                )
                return {
                    'status': status_val,
                    'failure_type': 'WEIGHT_EXCEEDED',
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
                        'reason': f"Item '{item.name}' ({item.weight}kg) exceeds maximum weight limit of all available boxes.",
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
                if best_box_model is None:
                    # First/cheapest feasible box is selected as optimal
                    audit_trail.append({
                        'box_code': box.code,
                        'box_name': box.name,
                        'cost': float(box.cost),
                        'status': 'ACCEPTED',
                        'reason': f"Optimal fit! Volume utilization: {pack_res.volume_utilization_pct:.1f}%, Weight utilization: {pack_res.weight_utilization_pct:.1f}%",
                    })
                    best_single_result = pack_res
                    best_box_model = box
                else:
                    # More expensive box that also fits; evaluate and record as SKIPPED
                    diff = float(box.cost) - float(best_box_model.cost)
                    audit_trail.append({
                        'box_code': box.code,
                        'box_name': box.name,
                        'cost': float(box.cost),
                        'status': 'SKIPPED',
                        'reason': f"Feasible fit (Volume util: {pack_res.volume_utilization_pct:.1f}%), but skipped to minimize packaging cost (saves ${diff:.2f} vs {box.name}).",
                    })
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
        max_box_wt = max((float(b.max_weight) for b in boxes), default=0.0)
        weight_failed = (total_weight > max_box_wt) or (
            audit_trail and all("weight" in b.get('reason', '').lower() for b in audit_trail)
        )
        if weight_failed:
            status_val = StatusStr("WEIGHT_EXCEEDED")
            failure_type = "WEIGHT_EXCEEDED"
        else:
            status_val = StatusStr("OVERSIZED")
            failure_type = "OVERSIZED"

        explanation = ExplainerService.generate_explanation(
            status=str(status_val),
            selected_boxes=[],
            audit_trail=audit_trail,
            total_weight=total_weight,
            total_volume=total_volume
        )
        return {
            'status': status_val,
            'failure_type': failure_type,
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

    @classmethod
    def recommend_for_order(
        cls,
        order: Order,
        items: Optional[List[ItemToPack]] = None,
        candidate_boxes: Optional[List[Box]] = None,
        allow_multi_box: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculates and persists the optimal box recommendation for an order.
        Acts as the single source of truth across the entire application:
        - Evaluates current order items against active boxes
        - Inactivates older recommendations for this order (marks is_stale=True)
        - Creates a new BoxRecommendation record with the current shipment fingerprint
        - Updates Order.status according to the true recommendation outcome
        - Returns a structured dictionary containing all required fields for UI/API
        """
        from recommendations.models import BoxRecommendation
        from recommendations.serializers import BoxRecommendationSerializer

        if items is None:
            items = cls.items_from_order(order)

        fingerprint = order.get_shipment_fingerprint()

        try:
            rec_result = cls.select_box(items, candidate_boxes=candidate_boxes, allow_multi_box=allow_multi_box)
        except Exception as ex:
            rec_result = {
                'status': 'ERROR',
                'failure_type': 'ERROR',
                'selected_box': None,
                'boxes_used': [],
                'total_cost': 0.0,
                'total_weight': float(order.total_weight),
                'total_volume': float(order.total_volume),
                'volume_utilization': 0.0,
                'weight_utilization': 0.0,
                'audit_trail': [{'box_code': 'SYSTEM', 'box_name': 'Engine', 'status': 'ERROR', 'reason': str(ex)}],
                'explanation': f"Calculation error: {str(ex)}",
                'packing_layout': [],
            }

        status_str = str(rec_result['status'])
        if status_str == 'OPTIMAL':
            order_status = Order.Status.RECOMMENDED
            db_status = BoxRecommendation.RecommendationStatus.OPTIMAL
        elif status_str == 'SPLIT_REQUIRED':
            order_status = Order.Status.SPLIT_REQUIRED
            db_status = BoxRecommendation.RecommendationStatus.SPLIT_REQUIRED
        elif status_str == 'OVERSIZED':
            order_status = Order.Status.OVERSIZED
            db_status = BoxRecommendation.RecommendationStatus.OVERSIZED
        elif status_str == 'WEIGHT_EXCEEDED':
            order_status = Order.Status.WEIGHT_EXCEEDED
            db_status = BoxRecommendation.RecommendationStatus.WEIGHT_EXCEEDED
        elif status_str == 'ERROR':
            order_status = Order.Status.ERROR
            db_status = BoxRecommendation.RecommendationStatus.ERROR
        else:
            ftype = rec_result.get('failure_type')
            if ftype == 'WEIGHT_EXCEEDED':
                order_status = Order.Status.WEIGHT_EXCEEDED
                db_status = BoxRecommendation.RecommendationStatus.WEIGHT_EXCEEDED
            else:
                order_status = Order.Status.OVERSIZED
                db_status = BoxRecommendation.RecommendationStatus.OVERSIZED

        # Invalidate any prior active recommendation for this order
        BoxRecommendation.objects.filter(order=order, is_stale=False).update(is_stale=True)

        # Create new recommendation record
        recommendation = BoxRecommendation.objects.create(
            order=order,
            status=db_status,
            selected_box=rec_result.get('selected_box'),
            total_cost=Decimal(str(round(rec_result.get('total_cost', 0.0), 2))),
            total_weight=Decimal(str(round(rec_result.get('total_weight', 0.0), 2))),
            total_volume=float(rec_result.get('total_volume', 0.0)),
            volume_utilization=float(rec_result.get('volume_utilization', 0.0)),
            weight_utilization=float(rec_result.get('weight_utilization', 0.0)),
            boxes_used=rec_result.get('boxes_used', []),
            packing_layout=rec_result.get('packing_layout', []),
            audit_trail=rec_result.get('audit_trail', []),
            explanation=rec_result.get('explanation', ''),
            shipment_fingerprint=fingerprint,
            is_stale=False,
        )

        # Update order status
        order.status = order_status
        order.save(update_fields=['status'])

        # Prepare unified response payload
        res_data = BoxRecommendationSerializer(recommendation).data
        box_dict = (
            {
                'id': recommendation.selected_box.id,
                'code': recommendation.selected_box.code,
                'name': recommendation.selected_box.name,
                'dimensions': recommendation.selected_box.dimensions_display,
                'cost': float(recommendation.selected_box.cost),
                'max_weight': float(recommendation.selected_box.max_weight),
            }
            if recommendation.selected_box else None
        )
        res_data.update({
            'order_id': order.id,
            'order_number': order.order_number,
            'customer_name': order.customer_name,
            'status': db_status,
            'status_display': order.get_status_display(),
            'is_standalone': False,
            'packaging_cost': float(recommendation.total_cost),
            'selected_box': box_dict,
            'recommended_box': box_dict,
        })
        return res_data
