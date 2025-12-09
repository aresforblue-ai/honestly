"""
Differential Privacy implementation for vault operations.
Provides privacy guarantees through noise addition and privacy budget tracking.
"""

import math
import secrets
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class PrivacyBudget:
    """Tracks privacy budget (epsilon) for differential privacy."""

    epsilon: float  # Privacy budget
    delta: float  # Failure probability
    spent: float = 0.0  # Amount of budget spent
    operations: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def spend(self, amount: float, operation: str) -> bool:
        """
        Spend privacy budget for an operation.

        Args:
            amount: Amount of epsilon to spend
            operation: Description of the operation

        Returns:
            True if budget available, False otherwise
        """
        if self.spent + amount > self.epsilon:
            logger.warning(f"Privacy budget exceeded: {self.spent + amount} > {self.epsilon}")
            return False

        self.spent += amount
        self.operations.append(
            {
                "operation": operation,
                "epsilon_spent": amount,
                "timestamp": datetime.utcnow().isoformat(),
                "total_spent": self.spent,
            }
        )
        return True

    def remaining(self) -> float:
        """Get remaining privacy budget."""
        return max(0, self.epsilon - self.spent)

    def is_exhausted(self) -> bool:
        """Check if privacy budget is exhausted."""
        return self.spent >= self.epsilon


class DifferentialPrivacy:
    """Service for applying differential privacy to vault queries and analytics."""

    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        """
        Initialize differential privacy service.

        Args:
            epsilon: Privacy budget (lower = more private, typical: 0.1-1.0)
            delta: Failure probability (typical: 1e-5 to 1e-10)
        """
        if epsilon <= 0:
            raise ValueError("Epsilon must be positive")
        if delta < 0 or delta >= 1:
            raise ValueError("Delta must be in [0, 1)")

        self.epsilon = epsilon
        self.delta = delta
        self.budget = PrivacyBudget(epsilon=epsilon, delta=delta)
        logger.info(f"Initialized DP with epsilon={epsilon}, delta={delta}")

    def add_laplace_noise(
        self, true_value: float, sensitivity: float, epsilon: Optional[float] = None
    ) -> float:
        """
        Add Laplace noise for differential privacy.

        Used for count queries and numeric aggregations.

        Args:
            true_value: The true value to protect
            sensitivity: Global sensitivity (max change from one record)
            epsilon: Privacy parameter (uses instance epsilon if None)

        Returns:
            Noisy value with differential privacy guarantee
        """
        if epsilon is None:
            epsilon = self.epsilon

        # Laplace scale parameter
        scale = sensitivity / epsilon

        # Generate Laplace noise using two exponential distributions
        # Ensure u1 and u2 are non-zero to avoid log(0) or division by zero
        rng = secrets.SystemRandom()
        u1 = rng.random()
        while u1 == 0.0:
            u1 = rng.random()
        u2 = rng.random()
        while u2 == 0.0:
            u2 = rng.random()
        noise = scale * math.log(u1 / u2)

        noisy_value = true_value + noise

        # Track budget spending
        self.budget.spend(epsilon, f"Laplace noise (sensitivity={sensitivity})")

        logger.debug(f"Added Laplace noise: {true_value} -> {noisy_value}")
        return noisy_value

    def add_gaussian_noise(
        self,
        true_value: float,
        sensitivity: float,
        epsilon: Optional[float] = None,
        delta: Optional[float] = None,
    ) -> float:
        """
        Add Gaussian noise for approximate differential privacy.

        Provides (epsilon, delta)-DP guarantee. More accurate than Laplace for large datasets.

        Args:
            true_value: The true value to protect
            sensitivity: Global sensitivity
            epsilon: Privacy parameter (uses instance epsilon if None)
            delta: Failure probability (uses instance delta if None)

        Returns:
            Noisy value with (epsilon, delta)-DP guarantee
        """
        if epsilon is None:
            epsilon = self.epsilon
        if delta is None:
            delta = self.delta

        # Gaussian mechanism: sigma = sensitivity * sqrt(2 * ln(1.25/delta)) / epsilon
        sigma = sensitivity * math.sqrt(2 * math.log(1.25 / delta)) / epsilon

        # Generate Gaussian noise using Box-Muller transform
        u1 = secrets.SystemRandom().random()
        u2 = secrets.SystemRandom().random()
        z0 = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
        noise = sigma * z0

        noisy_value = true_value + noise

        # Track budget spending
        self.budget.spend(epsilon, f"Gaussian noise (sensitivity={sensitivity}, delta={delta})")

        logger.debug(f"Added Gaussian noise: {true_value} -> {noisy_value}")
        return noisy_value

    def add_exponential_noise(
        self, scores: List[float], sensitivity: float, epsilon: Optional[float] = None
    ) -> int:
        """
        Exponential mechanism for selecting from discrete set with privacy.

        Used for selecting best option while preserving privacy.

        Args:
            scores: Quality scores for each option
            sensitivity: Sensitivity of the scoring function
            epsilon: Privacy parameter

        Returns:
            Index of selected option
        """
        if epsilon is None:
            epsilon = self.epsilon

        # Calculate probabilities proportional to exp(epsilon * score / (2 * sensitivity))
        max_score = max(scores)
        exp_scores = [
            math.exp((epsilon * (score - max_score)) / (2 * sensitivity)) for score in scores
        ]

        total = sum(exp_scores)
        probabilities = [exp_score / total for exp_score in exp_scores]

        # Sample from categorical distribution
        r = secrets.SystemRandom().random()
        cumulative = 0
        for i, prob in enumerate(probabilities):
            cumulative += prob
            if r <= cumulative:
                selected = i
                break
        else:
            selected = len(scores) - 1

        # Track budget spending
        self.budget.spend(epsilon, f"Exponential mechanism (sensitivity={sensitivity})")

        logger.debug(f"Exponential mechanism selected index {selected} from {len(scores)} options")
        return selected

    def private_count(self, true_count: int, epsilon: Optional[float] = None) -> int:
        """
        Return differentially private count.

        Args:
            true_count: Actual count
            epsilon: Privacy parameter

        Returns:
            Noisy count (rounded to nearest integer)
        """
        # Sensitivity of count query is 1 (adding/removing one record changes count by 1)
        noisy_count = self.add_laplace_noise(float(true_count), sensitivity=1.0, epsilon=epsilon)
        return max(0, round(noisy_count))  # Ensure non-negative

    def private_sum(
        self, true_sum: float, max_value: float, epsilon: Optional[float] = None
    ) -> float:
        """
        Return differentially private sum with bounded contributions.

        Args:
            true_sum: Actual sum
            max_value: Maximum contribution per record (for bounded sensitivity)
            epsilon: Privacy parameter

        Returns:
            Noisy sum
        """
        # Sensitivity is max_value (one record can contribute at most max_value)
        return self.add_laplace_noise(true_sum, sensitivity=max_value, epsilon=epsilon)

    def private_mean(
        self, true_mean: float, count: int, max_value: float, epsilon: Optional[float] = None
    ) -> float:
        """
        Return differentially private mean with bounded contributions.

        Args:
            true_mean: Actual mean
            count: Number of records
            max_value: Maximum value per record
            epsilon: Privacy parameter

        Returns:
            Noisy mean
        """
        if epsilon is None:
            epsilon = self.epsilon

        # Split privacy budget between sum and count
        epsilon_sum = epsilon / 2
        epsilon_count = epsilon / 2

        # Add noise to sum and count separately
        true_sum = true_mean * count
        noisy_sum = self.private_sum(true_sum, max_value, epsilon=epsilon_sum)
        noisy_count = self.private_count(count, epsilon=epsilon_count)

        if noisy_count == 0:
            return 0.0

        return noisy_sum / noisy_count

    def get_privacy_budget_status(self) -> Dict[str, Any]:
        """Get current privacy budget status."""
        return {
            "epsilon": self.budget.epsilon,
            "delta": self.budget.delta,
            "spent": self.budget.spent,
            "remaining": self.budget.remaining(),
            "exhausted": self.budget.is_exhausted(),
            "operations_count": len(self.budget.operations),
            "created_at": self.budget.created_at.isoformat(),
        }

    def reset_privacy_budget(
        self, new_epsilon: Optional[float] = None, new_delta: Optional[float] = None
    ) -> None:
        """
        Reset privacy budget (use with caution).

        Args:
            new_epsilon: New epsilon value (uses current if None)
            new_delta: New delta value (uses current if None)
        """
        epsilon = new_epsilon if new_epsilon is not None else self.epsilon
        delta = new_delta if new_delta is not None else self.delta

        old_budget = self.budget
        self.budget = PrivacyBudget(epsilon=epsilon, delta=delta)

        logger.warning(
            f"Privacy budget reset: old={old_budget.epsilon}, "
            f"new={epsilon}, operations={len(old_budget.operations)}"
        )
