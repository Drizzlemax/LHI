"""
PANDORA Quiz Service Adaptive Item Selector
"""
from typing import Literal

import numpy as np

from src.irt.models import (
    AbilityEstimate,
    IRT2PL,
    IRT3PL,
    ItemParameters,
    ResponsePattern,
    SelectionInfo,
)
from src.irt.estimator import IRTEstimator


class ItemSelector:
    """Selects items for adaptive testing based on IRT."""
    
    def __init__(
        self,
        model: Literal["2pl", "3pl"] = "3pl",
        selection_method: Literal["maximum_information", "minimum_error", "random"] = "maximum_information",
        exposure_control: float = 0.0,  # 0 = no control, 1 = maximum control
        randomization: float = 0.1,  # Randomization factor
    ):
        self.model = IRT3PL if model == "3pl" else IRT2PL
        self.selection_method = selection_method
        self.exposure_control = exposure_control
        self.randomization = randomization
        self.estimator = IRTEstimator(model=model)
        
        # Track item usage for exposure control
        self.item_usage_count: dict[str, int] = {}
        self.total_selections = 0
    
    def select_next_item(
        self,
        current_ability: AbilityEstimate,
        available_items: list[ItemParameters],
        used_item_ids: set[str],
        target_difficulty: float | None = None,
    ) -> SelectionInfo | None:
        """Select the next item for adaptive testing.
        
        Args:
            current_ability: Current ability estimate
            available_items: Items available for selection
            used_item_ids: IDs of already used items
            target_difficulty: Target difficulty (if None, uses current ability)
        
        Returns:
            SelectionInfo or None if no items available
        """
        # Filter out used items
        candidate_items = [
            item for item in available_items
            if item.item_id not in used_item_ids
        ]
        
        if not candidate_items:
            return None
        
        # Calculate information for each item
        theta = target_difficulty if target_difficulty is not None else current_ability.theta
        item_infos = []
        
        for item in candidate_items:
            info = self.model.information(theta, item)
            
            # Apply exposure control
            if self.total_selections > 0 and self.exposure_control > 0:
                usage_rate = self.item_usage_count.get(item.item_id, 0) / self.total_selections
                # Penalize items with high usage
                exposure_penalty = self.exposure_control * usage_rate
                info *= (1 - exposure_penalty)
            
            item_infos.append((item, info))
        
        # Sort by information
        item_infos.sort(key=lambda x: x[1], reverse=True)
        
        # Apply randomization
        if self.randomization > 0:
            k = max(1, int(len(item_infos) * self.randomization))
            selected_idx = np.random.randint(0, min(k, len(item_infos)))
        else:
            selected_idx = 0
        
        selected_item, info = item_infos[selected_idx]
        
        # Calculate probability
        prob = self.model.probability(theta, selected_item)
        
        # Update usage tracking
        self.item_usage_count[selected_item.item_id] = (
            self.item_usage_count.get(selected_item.item_id, 0) + 1
        )
        self.total_selections += 1
        
        return SelectionInfo(
            item_id=selected_item.item_id,
            information=info,
            probability=prob,
            reason=f"Selected via {self.selection_method}",
        )
    
    def select_items_for_static_test(
        self,
        target_ability: float,
        items: list[ItemParameters],
        num_items: int,
        difficulty_range: tuple[float, float] | None = None,
    ) -> list[ItemParameters]:
        """Select items for a static (non-adaptive) test.
        
        Creates a balanced test targeting specific difficulty range.
        """
        if num_items > len(items):
            num_items = len(items)
        
        # Sort items by difficulty
        sorted_items = sorted(items, key=lambda x: x.difficulty)
        
        if difficulty_range:
            low, high = difficulty_range
            sorted_items = [
                item for item in sorted_items
                if low <= item.difficulty <= high
            ]
        
        if len(sorted_items) <= num_items:
            return sorted_items
        
        # Select items evenly distributed across difficulty range
        indices = np.linspace(0, len(sorted_items) - 1, num_items, dtype=int)
        return [sorted_items[i] for i in indices]
    
    def estimate_ability_from_pattern(
        self,
        responses: ResponsePattern,
        items: list[ItemParameters],
    ) -> AbilityEstimate:
        """Estimate ability from response pattern."""
        return self.estimator.estimate_ability(responses, items)
    
    def update_usage_stats(self, item_id: str) -> None:
        """Update usage statistics for an item."""
        self.item_usage_count[item_id] = self.item_usage_count.get(item_id, 0) + 1
        self.total_selections += 1
    
    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self.item_usage_count.clear()
        self.total_selections = 0
    
    def get_item_statistics(self) -> dict[str, dict]:
        """Get usage statistics for all items."""
        if self.total_selections == 0:
            return {}
        
        return {
            item_id: {
                "count": count,
                "rate": count / self.total_selections,
            }
            for item_id, count in self.item_usage_count.items()
        }
