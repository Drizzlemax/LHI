"""
PANDORA Quiz Service IRT Models
"""
from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass
class ItemParameters:
    """Item parameters for IRT models."""
    difficulty: float = 0.0  # b parameter
    discrimination: float = 1.0  # a parameter
    guessing: float = 0.25  # c parameter (for 3PL)
    item_id: str = ""


@dataclass
class AbilityEstimate:
    """Ability estimate with uncertainty."""
    theta: float  # Ability estimate
    standard_error: float  # Standard error of measurement
    information: float  # Test information at this ability level
    converged: bool = True
    iterations: int = 0


@dataclass
class ResponsePattern:
    """Response pattern for IRT estimation."""
    item_ids: list[str]
    responses: list[bool]  # True = correct, False = incorrect
    time_spent: list[int] | None = None  # Optional time data


@dataclass
class SelectionInfo:
    """Information about item selection."""
    item_id: str
    information: float
    probability: float
    reason: str


def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid function."""
    if x < -700:
        return 0.0
    if x > 700:
        return 1.0
    return 1 / (1 + np.exp(x))


@dataclass
class IRT2PL:
    """Two-Parameter Logistic IRT Model.
    
    P(θ) = 1 / (1 + exp(a(b - θ)))
    
    where:
    - θ (theta): ability
    - a: discrimination
    - b: difficulty
    """
    
    @staticmethod
    def probability(ability: float, item: ItemParameters) -> float:
        """Calculate probability of correct response."""
        exponent = item.discrimination * (item.difficulty - ability)
        return _sigmoid(exponent)
    
    @staticmethod
    def information(ability: float, item: ItemParameters) -> float:
        """Calculate Fisher information at given ability level."""
        p = IRT2PL.probability(ability, item)
        q = 1 - p
        return item.discrimination**2 * q / p


@dataclass  
class IRT3PL:
    """Three-Parameter Logistic IRT Model.
    
    P(θ) = c + (1 - c) / (1 + exp(a(b - θ)))
    
    where:
    - θ (theta): ability
    - a: discrimination
    - b: difficulty
    - c: guessing parameter (lower asymptote)
    """
    
    @staticmethod
    def probability(ability: float, item: ItemParameters) -> float:
        """Calculate probability of correct response."""
        p_base = _sigmoid(item.discrimination * (item.difficulty - ability))
        return item.guessing + (1 - item.guessing) * p_base
    
    @staticmethod
    def information(ability: float, item: ItemParameters) -> float:
        """Calculate Fisher information at given ability level."""
        p = IRT3PL.probability(ability, item)
        q = 1 - p
        c = item.guessing
        
        # Information formula for 3PL
        numerator = item.discrimination**2 * (p - c)**2 * q
        denominator = p * (1 - c)**2
        
        return numerator / denominator
