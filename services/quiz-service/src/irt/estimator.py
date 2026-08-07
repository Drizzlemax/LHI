"""
PANDORA Quiz Service IRT Ability Estimator
"""
from typing import Literal

import numpy as np
from scipy.optimize import minimize

from src.irt.models import (
    AbilityEstimate,
    IRT2PL,
    IRT3PL,
    ItemParameters,
    ResponsePattern,
)


class IRTEstimator:
    """Estimates ability using Item Response Theory."""
    
    def __init__(
        self,
        model: Literal["2pl", "3pl"] = "3pl",
        initial_theta: float = 0.0,
        initial_std: float = 1.0,
        max_iterations: int = 50,
        convergence_threshold: float = 0.001,
    ):
        self.model = IRT3PL if model == "3pl" else IRT2PL
        self.initial_theta = initial_theta
        self.initial_std = initial_std
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
    
    def estimate_ability(
        self,
        responses: ResponsePattern,
        items: list[ItemParameters],
    ) -> AbilityEstimate:
        """Estimate ability from response pattern.
        
        Uses Maximum Likelihood Estimation (MLE) with
        Newton-Raphson optimization.
        """
        if len(responses.item_ids) != len(items):
            raise ValueError("Number of items must match response pattern")
        
        if len(responses.responses) == 0:
            return AbilityEstimate(
                theta=self.initial_theta,
                standard_error=self.initial_std,
                information=0.0,
                converged=True,
                iterations=0,
            )
        
        # Initial estimate
        theta = self.initial_theta
        
        for iteration in range(self.max_iterations):
            # Calculate first and second derivatives
            first_deriv = 0.0
            second_deriv = 0.0
            total_info = 0.0
            
            for response, item in zip(responses.responses, items):
                p = self.model.probability(theta, item)
                p = max(min(p, 0.9999), 0.0001)  # Clip for numerical stability
                q = 1 - p
                
                # First derivative of log-likelihood
                # For correct response: d/dθ log(P) = a * (1 - P)
                # For incorrect response: d/dθ log(1-P) = -a * P
                if response:
                    first_deriv += item.discrimination * q
                else:
                    first_deriv -= item.discrimination * p
                
                # Second derivative (negative Fisher information)
                info = self.model.information(theta, item)
                total_info += info
                second_deriv -= info
            
            # Newton-Raphson update
            if abs(second_deriv) < 1e-10:
                break
                
            delta = first_deriv / second_deriv
            theta_new = theta - delta
            
            # Bound theta to prevent runaway values
            theta_new = max(-10.0, min(10.0, theta_new))
            
            # Check convergence
            if abs(theta_new - theta) < self.convergence_threshold:
                theta = theta_new
                break
            
            theta = theta_new
        
        # Calculate final standard error
        total_info = sum(
            self.model.information(theta, item)
            for item in items
        )
        
        se = 1 / np.sqrt(total_info) if total_info > 0 else self.initial_std
        
        # Check convergence
        converged = iteration < self.max_iterations - 1
        
        return AbilityEstimate(
            theta=theta,
            standard_error=se,
            information=total_info,
            converged=converged,
            iterations=iteration + 1,
        )
    
    def estimate_ability_bayesian(
        self,
        responses: ResponsePattern,
        items: list[ItemParameters],
        prior_mean: float = 0.0,
        prior_std: float = 1.0,
    ) -> AbilityEstimate:
        """Estimate ability using Bayesian MLE (with prior).
        
        Uses Maximum A Posteriori (MAP) estimation.
        """
        if len(responses.responses) == 0:
            return AbilityEstimate(
                theta=prior_mean,
                standard_error=prior_std,
                information=0.0,
                converged=True,
                iterations=0,
            )
        
        def neg_log_posterior(theta: float) -> float:
            """Negative log posterior for optimization."""
            log_lik = 0.0
            
            for response, item in zip(responses.responses, items):
                p = self.model.probability(theta, item)
                p = max(min(p, 0.9999), 0.0001)  # Clip for numerical stability
                
                if response:
                    log_lik += np.log(p)
                else:
                    log_lik += np.log(1 - p)
            
            # Add prior
            log_prior = -0.5 * ((theta - prior_mean) / prior_std) ** 2
            
            return -(log_lik + log_prior)
        
        # Optimize
        result = minimize(
            neg_log_posterior,
            x0=[self.initial_theta],
            method="BFGS",
            options={"maxiter": self.max_iterations},
        )
        
        theta = result.x[0]
        
        # Approximate standard error from Hessian
        total_info = sum(
            self.model.information(theta, item)
            for item in items
        )
        total_info += 1 / (prior_std**2)  # Add prior precision
        
        se = 1 / np.sqrt(total_info) if total_info > 0 else self.initial_std
        
        return AbilityEstimate(
            theta=theta,
            standard_error=se,
            information=total_info,
            converged=result.success,
            iterations=int(result.nit),
        )
    
    def calculate_test_information(
        self,
        theta: float,
        items: list[ItemParameters],
    ) -> float:
        """Calculate total test information at a given ability level."""
        return sum(
            self.model.information(theta, item)
            for item in items
        )
    
    def standard_error_at(
        self,
        theta: float,
        items: list[ItemParameters],
    ) -> float:
        """Calculate standard error of measurement at a given ability."""
        info = self.calculate_test_information(theta, items)
        return 1 / np.sqrt(info) if info > 0 else float("inf")
