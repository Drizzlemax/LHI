"""
PANDORA Quiz Service Unit Tests - IRT Models
"""
import pytest

from src.irt.models import IRT2PL, IRT3PL, ItemParameters, ResponsePattern
from src.irt.estimator import IRTEstimator
from src.irt.item_selector import ItemSelector

pytestmark = pytest.mark.unit


class TestIRT2PL:
    """Tests for 2-Parameter Logistic IRT Model."""

    def test_probability_at_difficulty(self):
        """Test probability when ability equals difficulty."""
        item = ItemParameters(difficulty=0.0, discrimination=1.0)
        prob = IRT2PL.probability(ability=0.0, item=item)
        assert prob == pytest.approx(0.5, rel=0.01)

    def test_probability_high_ability(self):
        """Test probability for high ability student."""
        item = ItemParameters(difficulty=0.0, discrimination=1.0)
        prob = IRT2PL.probability(ability=2.0, item=item)
        # P = 1/(1+exp(a(b-θ))) = 1/(1+exp(-2)) = 0.88
        assert prob > 0.8

    def test_probability_low_ability(self):
        """Test probability for low ability student."""
        item = ItemParameters(difficulty=0.0, discrimination=1.0)
        prob = IRT2PL.probability(ability=-2.0, item=item)
        # P = 1/(1+exp(a(b-θ))) = 1/(1+exp(2)) = 0.12
        assert prob < 0.2

    def test_information_at_difficulty(self):
        """Test information at difficulty level."""
        item = ItemParameters(difficulty=0.0, discrimination=1.0)
        info = IRT2PL.information(ability=0.0, item=item)
        assert info > 0


class TestIRT3PL:
    """Tests for 3-Parameter Logistic IRT Model."""

    def test_probability_with_guessing(self):
        """Test probability includes guessing parameter."""
        item = ItemParameters(difficulty=0.0, discrimination=1.0, guessing=0.25)
        prob = IRT3PL.probability(ability=-5.0, item=item)
        assert prob > 0.25  # Should be above guessing

    def test_probability_no_guessing(self):
        """Test 3PL with no guessing equals 2PL at high ability."""
        item_3pl = ItemParameters(difficulty=0.0, discrimination=1.0, guessing=0.0)
        item_2pl = ItemParameters(difficulty=0.0, discrimination=1.0)
        
        prob_3pl = IRT3PL.probability(ability=2.0, item=item_3pl)
        prob_2pl = IRT2PL.probability(ability=2.0, item=item_2pl)
        
        assert prob_3pl == pytest.approx(prob_2pl, rel=0.01)


class TestIRTEstimator:
    """Tests for IRT Ability Estimator."""

    def test_estimator_instantiation(self):
        """Test estimator can be created."""
        estimator = IRTEstimator(model="3pl")
        assert estimator is not None
        assert estimator.model == IRT3PL

    def test_empty_response_pattern(self):
        """Test estimation with no responses."""
        estimator = IRTEstimator(model="3pl")
        pattern = ResponsePattern(item_ids=[], responses=[])
        items = []
        
        result = estimator.estimate_ability(pattern, items)
        assert result.theta == 0.0  # Initial value
        assert result.converged is True

    def test_all_correct_responses(self):
        """Test estimation with all correct responses."""
        estimator = IRTEstimator(model="3pl", initial_theta=0.0)
        
        items = [
            ItemParameters(item_id="1", difficulty=0.0, discrimination=1.0),
            ItemParameters(item_id="2", difficulty=0.0, discrimination=1.0),
        ]
        pattern = ResponsePattern(
            item_ids=["1", "2"],
            responses=[True, True],
        )
        
        result = estimator.estimate_ability(pattern, items)
        assert result.theta > 1.0  # Should estimate high ability

    def test_all_incorrect_responses(self):
        """Test estimation with all incorrect responses."""
        estimator = IRTEstimator(model="3pl", initial_theta=0.0)
        
        items = [
            ItemParameters(item_id="1", difficulty=0.0, discrimination=1.0),
            ItemParameters(item_id="2", difficulty=0.0, discrimination=1.0),
        ]
        pattern = ResponsePattern(
            item_ids=["1", "2"],
            responses=[False, False],
        )
        
        result = estimator.estimate_ability(pattern, items)
        assert result.theta < -1.0  # Should estimate low ability

    def test_mixed_responses(self):
        """Test estimation with mixed correct/incorrect."""
        estimator = IRTEstimator(model="3pl")
        
        items = [
            ItemParameters(item_id="1", difficulty=-1.0, discrimination=1.0),
            ItemParameters(item_id="2", difficulty=1.0, discrimination=1.0),
        ]
        pattern = ResponsePattern(
            item_ids=["1", "2"],
            responses=[True, False],
        )
        
        result = estimator.estimate_ability(pattern, items)
        # Should be close to 0 with mixed results
        assert -1.0 <= result.theta <= 1.0


class TestItemSelector:
    """Tests for Item Selector."""

    def test_selector_instantiation(self):
        """Test selector can be created."""
        selector = ItemSelector(model="3pl")
        assert selector is not None
        assert selector.model == IRT3PL

    def test_select_next_item(self):
        """Test item selection."""
        from src.irt.models import AbilityEstimate
        
        selector = ItemSelector(model="3pl")
        
        items = [
            ItemParameters(item_id="1", difficulty=0.0, discrimination=1.0),
            ItemParameters(item_id="2", difficulty=1.0, discrimination=1.0),
            ItemParameters(item_id="3", difficulty=-1.0, discrimination=1.0),
        ]
        
        ability = AbilityEstimate(theta=0.0, standard_error=1.0, information=1.0)
        
        result = selector.select_next_item(
            current_ability=ability,
            available_items=items,
            used_item_ids=set(),
        )
        
        assert result is not None
        assert result.item_id in ["1", "2", "3"]
        assert result.information > 0

    def test_exclude_used_items(self):
        """Test that used items are excluded."""
        from src.irt.models import AbilityEstimate
        
        selector = ItemSelector(model="3pl")
        
        items = [
            ItemParameters(item_id="1", difficulty=0.0, discrimination=1.0),
            ItemParameters(item_id="2", difficulty=1.0, discrimination=1.0),
        ]
        
        ability = AbilityEstimate(theta=0.0, standard_error=1.0, information=1.0)
        
        result = selector.select_next_item(
            current_ability=ability,
            available_items=items,
            used_item_ids={"1"},  # Item 1 already used
        )
        
        assert result is not None
        assert result.item_id == "2"  # Should select item 2

    def test_no_available_items(self):
        """Test selection when no items available."""
        from src.irt.models import AbilityEstimate
        
        selector = ItemSelector(model="3pl")
        ability = AbilityEstimate(theta=0.0, standard_error=1.0, information=1.0)
        
        result = selector.select_next_item(
            current_ability=ability,
            available_items=[],
            used_item_ids={"1", "2", "3"},
        )
        
        assert result is None
