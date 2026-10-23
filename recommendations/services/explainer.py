"""
Explanation service for warehouse operators.
Generates clear, human-readable rationale for box recommendations,
explaining why rejected boxes failed and why the chosen box is cost-optimal.
"""

from typing import List, Dict, Any


class ExplainerService:
    @staticmethod
    def generate_explanation(
        status: str,
        selected_boxes: List[Dict[str, Any]],
        audit_trail: List[Dict[str, Any]],
        total_weight: float,
        total_volume: float,
    ) -> str:
        lines = []

        if status == "OPTIMAL":
            chosen = selected_boxes[0]
            lines.append(f"RECOMMENDATION: Use '{chosen['box_name']}' ({chosen['box_code']}).")
            lines.append(f"Packaging Cost: ${chosen['box_cost']:.2f}")
            lines.append(f"Efficiency Metrics: Volume Utilization {chosen['volume_utilization_pct']:.1f}%, Weight Capacity Utilization {chosen['weight_utilization_pct']:.1f}%.")
            lines.append("")
            lines.append("Decision Rationale:")

            # Review audit trail
            cheaper_rejected = [b for b in audit_trail if b.get('status') == 'REJECTED' and b.get('cost', 0) < chosen['box_cost']]
            more_expensive_skipped = [b for b in audit_trail if b.get('cost', 0) > chosen['box_cost']]

            if cheaper_rejected:
                lines.append(f"- Lower-cost box options were evaluated and rejected due to physical constraints:")
                for b in cheaper_rejected:
                    lines.append(f"  * {b['box_name']} (${b['cost']:.2f}): {b['reason']}")
            else:
                lines.append(f"- '{chosen['box_name']}' is the most economical box option in catalog.")

            lines.append(f"- '{chosen['box_name']}' passed all 3D orthogonal collision checks and weight limits.")

            if more_expensive_skipped:
                cheapest_higher = more_expensive_skipped[0]
                diff = cheapest_higher['cost'] - chosen['box_cost']
                lines.append(f"- Larger/higher-tier boxes (e.g. {cheapest_higher['box_name']} at ${cheapest_higher['cost']:.2f}) were avoided, saving ${diff:.2f} in packaging cost.")

        elif status == "SPLIT_REQUIRED":
            lines.append("RECOMMENDATION: Multi-Box Split Required.")
            lines.append(f"The items in this order cannot safely fit into any single standard shipping box.")
            lines.append(f"The order has been partitioned into {len(selected_boxes)} shipping boxes:")
            total_c = 0.0
            for idx, box in enumerate(selected_boxes, 1):
                total_c += box['box_cost']
                lines.append(f"  Box {idx}: {box['box_name']} ({box['box_code']}) - ${box['box_cost']:.2f} ({len(box['packed_items'])} items packed)")
            lines.append(f"Total Multi-Box Packaging Cost: ${total_c:.2f}")

        elif status in ("NO_FIT", "OVERSIZED"):
            lines.append("ALERT: No Suitable Standard Box Found.")
            lines.append("One or more items exceed the maximum dimension threshold of all warehouse shipping boxes.")
            lines.append("Action Required: Route this order to the Custom Freight / Oversized Cargo handling station.")
            if audit_trail:
                lines.append("")
                lines.append("Evaluation details:")
                for b in audit_trail[:3]:
                    lines.append(f"- {b['box_name']}: {b.get('reason', 'Exceeded capacity')}")

        elif status == "WEIGHT_EXCEEDED":
            lines.append("ALERT: Weight Limit Exceeded.")
            lines.append("The shipment weight exceeds the maximum safe weight capacity of available shipping boxes.")
            lines.append("Action Required: Divide shipment or route to heavy-duty handling station.")
            if audit_trail:
                lines.append("")
                lines.append("Evaluation details:")
                for b in audit_trail[:3]:
                    lines.append(f"- {b['box_name']}: {b.get('reason', 'Exceeded capacity')}")

        elif status == "ERROR":
            lines.append("ERROR: Calculation Error.")
            lines.append("An error occurred during the box recommendation calculation.")

        return "\n".join(lines)
