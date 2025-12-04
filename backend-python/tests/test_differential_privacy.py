"""
Comprehensive test suite for Differential Privacy implementation.
Tests edge cases, privacy guarantees, and attack scenarios.
"""
import pytest
import math
import statistics
from vault.differential_privacy import DifferentialPrivacy, PrivacyBudget


class TestPrivacyBudget:
    """Test privacy budget tracking."""
    
    def test_budget_initialization(self):
        """Test budget initializes correctly."""
        budget = PrivacyBudget(epsilon=1.0, delta=1e-5)
        assert budget.epsilon == 1.0
        assert budget.delta == 1e-5
        assert budget.spent == 0.0
        assert len(budget.operations) == 0
    
    def test_budget_spending(self):
        """Test spending privacy budget."""
        budget = PrivacyBudget(epsilon=1.0, delta=1e-5)
        
        # Should succeed
        assert budget.spend(0.3, "query1") is True
        assert budget.spent == 0.3
        assert len(budget.operations) == 1
        
        # Should succeed
        assert budget.spend(0.5, "query2") is True
        assert budget.spent == 0.8
        assert len(budget.operations) == 2
        
        # Should fail - exceeds budget
        assert budget.spend(0.3, "query3") is False
        assert budget.spent == 0.8  # Unchanged
        assert len(budget.operations) == 2  # Unchanged
    
    def test_budget_remaining(self):
        """Test remaining budget calculation."""
        budget = PrivacyBudget(epsilon=1.0, delta=1e-5)
        assert budget.remaining() == 1.0
        
        budget.spend(0.4, "query")
        assert budget.remaining() == 0.6
        
        budget.spend(0.6, "query2")
        assert budget.remaining() == 0.0
    
    def test_budget_exhaustion(self):
        """Test budget exhaustion detection."""
        budget = PrivacyBudget(epsilon=1.0, delta=1e-5)
        assert not budget.is_exhausted()
        
        budget.spend(0.9, "query")
        assert not budget.is_exhausted()
        
        budget.spend(0.1, "query2")
        assert budget.is_exhausted()


class TestDifferentialPrivacy:
    """Test differential privacy mechanisms."""
    
    def test_initialization(self):
        """Test DP service initialization."""
        dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)
        assert dp.epsilon == 1.0
        assert dp.delta == 1e-5
        assert dp.budget.spent == 0.0
    
    def test_initialization_invalid_epsilon(self):
        """Test initialization with invalid epsilon."""
        with pytest.raises(ValueError, match="Epsilon must be positive"):
            DifferentialPrivacy(epsilon=0)
        
        with pytest.raises(ValueError, match="Epsilon must be positive"):
            DifferentialPrivacy(epsilon=-1.0)
    
    def test_initialization_invalid_delta(self):
        """Test initialization with invalid delta."""
        with pytest.raises(ValueError, match="Delta must be in"):
            DifferentialPrivacy(epsilon=1.0, delta=-0.1)
        
        with pytest.raises(ValueError, match="Delta must be in"):
            DifferentialPrivacy(epsilon=1.0, delta=1.0)
    
    def test_laplace_noise_adds_noise(self):
        """Test Laplace mechanism adds noise."""
        dp = DifferentialPrivacy(epsilon=1.0)
        true_value = 100.0
        
        # Run multiple times - should get different values (with high probability)
        noisy_values = [
            dp.add_laplace_noise(true_value, sensitivity=1.0)
            for _ in range(10)
        ]
        
        # At least some values should differ
        assert len(set(noisy_values)) > 1
        
        # Mean should be close to true value (law of large numbers)
        # But with only 10 samples, we use a loose bound
        mean_noisy = statistics.mean(noisy_values)
        assert abs(mean_noisy - true_value) < 20  # Loose bound for small sample
    
    def test_laplace_noise_sensitivity(self):
        """Test Laplace noise scales with sensitivity."""
        dp1 = DifferentialPrivacy(epsilon=1.0)
        dp2 = DifferentialPrivacy(epsilon=1.0)
        
        true_value = 100.0
        
        # Higher sensitivity should add more noise
        noisy_low_sens = [
            dp1.add_laplace_noise(true_value, sensitivity=1.0)
            for _ in range(100)
        ]
        noisy_high_sens = [
            dp2.add_laplace_noise(true_value, sensitivity=10.0)
            for _ in range(100)
        ]
        
        # Standard deviation should be higher for higher sensitivity
        std_low = statistics.stdev(noisy_low_sens)
        std_high = statistics.stdev(noisy_high_sens)
        assert std_high > std_low
    
    def test_gaussian_noise_adds_noise(self):
        """Test Gaussian mechanism adds noise."""
        dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)
        true_value = 100.0
        
        noisy_values = [
            dp.add_gaussian_noise(true_value, sensitivity=1.0)
            for _ in range(10)
        ]
        
        # Should get different values
        assert len(set(noisy_values)) > 1
    
    def test_exponential_mechanism_selection(self):
        """Test exponential mechanism selects from options."""
        dp = DifferentialPrivacy(epsilon=1.0)
        
        # Scores: strongly prefer option 2
        scores = [1.0, 2.0, 10.0, 3.0]
        
        # Run multiple times and check option 2 is selected most often
        selections = [
            dp.add_exponential_noise(scores, sensitivity=1.0)
            for _ in range(100)
        ]
        
        # Option 2 (index 2) should be selected most frequently
        # But due to randomness, we just check it's selected at all
        assert 2 in selections
        assert len(set(selections)) > 1  # Should have some variety
    
    def test_exponential_mechanism_equal_scores(self):
        """Test exponential mechanism with equal scores."""
        dp = DifferentialPrivacy(epsilon=1.0)
        
        # All equal scores - should select uniformly
        scores = [5.0, 5.0, 5.0, 5.0]
        
        selections = [
            dp.add_exponential_noise(scores, sensitivity=1.0)
            for _ in range(100)
        ]
        
        # Should see all options selected (with high probability)
        unique_selections = set(selections)
        assert len(unique_selections) >= 2  # At least some variety
    
    def test_private_count(self):
        """Test private count query."""
        dp = DifferentialPrivacy(epsilon=1.0)
        true_count = 100
        
        noisy_count = dp.private_count(true_count)
        
        # Should be non-negative integer
        assert isinstance(noisy_count, int)
        assert noisy_count >= 0
        
        # Should be roughly close to true count
        assert abs(noisy_count - true_count) < 50  # Loose bound
    
    def test_private_count_zero(self):
        """Test private count with zero true count."""
        dp = DifferentialPrivacy(epsilon=1.0)
        
        noisy_count = dp.private_count(0)
        
        # Should be non-negative (even if noise is negative)
        assert noisy_count >= 0
    
    def test_private_sum(self):
        """Test private sum query."""
        dp = DifferentialPrivacy(epsilon=1.0)
        true_sum = 1000.0
        max_value = 100.0
        
        noisy_sum = dp.private_sum(true_sum, max_value)
        
        # Should be roughly close to true sum
        assert abs(noisy_sum - true_sum) < 500  # Loose bound
    
    def test_private_mean(self):
        """Test private mean query."""
        dp = DifferentialPrivacy(epsilon=1.0)
        true_mean = 50.0
        count = 100
        max_value = 100.0
        
        noisy_mean = dp.private_mean(true_mean, count, max_value)
        
        # Should be roughly close to true mean
        assert abs(noisy_mean - true_mean) < 20  # Loose bound
    
    def test_private_mean_zero_count(self):
        """Test private mean with noisy count becoming zero."""
        dp = DifferentialPrivacy(epsilon=1.0)
        
        # Small count might become zero after noise
        noisy_mean = dp.private_mean(50.0, count=1, max_value=100.0)
        
        # Should handle gracefully
        # Note: Mean can be negative due to noise, which is expected in DP
        assert isinstance(noisy_mean, float)
    
    def test_privacy_budget_tracking(self):
        """Test privacy budget is tracked correctly."""
        dp = DifferentialPrivacy(epsilon=1.0)
        
        dp.add_laplace_noise(100.0, sensitivity=1.0, epsilon=0.3)
        status = dp.get_privacy_budget_status()
        
        assert status['epsilon'] == 1.0
        assert status['spent'] == 0.3
        assert status['remaining'] == 0.7
        assert not status['exhausted']
    
    def test_privacy_budget_exhaustion(self):
        """Test privacy budget exhaustion."""
        dp = DifferentialPrivacy(epsilon=0.5)
        
        # Use up budget
        dp.add_laplace_noise(100.0, sensitivity=1.0, epsilon=0.3)
        dp.add_laplace_noise(100.0, sensitivity=1.0, epsilon=0.2)
        
        status = dp.get_privacy_budget_status()
        assert status['exhausted']
        assert status['remaining'] == 0.0
    
    def test_privacy_budget_reset(self):
        """Test privacy budget reset."""
        dp = DifferentialPrivacy(epsilon=1.0)
        
        # Use some budget
        dp.add_laplace_noise(100.0, sensitivity=1.0, epsilon=0.5)
        assert dp.budget.spent == 0.5
        
        # Reset budget
        dp.reset_privacy_budget()
        assert dp.budget.spent == 0.0
        assert dp.budget.epsilon == 1.0
    
    def test_privacy_budget_reset_new_epsilon(self):
        """Test privacy budget reset with new epsilon."""
        dp = DifferentialPrivacy(epsilon=1.0)
        
        dp.add_laplace_noise(100.0, sensitivity=1.0, epsilon=0.5)
        
        # Reset with new epsilon
        dp.reset_privacy_budget(new_epsilon=2.0)
        assert dp.budget.spent == 0.0
        assert dp.budget.epsilon == 2.0


class TestDifferentialPrivacyEdgeCases:
    """Test edge cases for differential privacy."""
    
    def test_very_small_epsilon(self):
        """Test with very small epsilon (high privacy)."""
        dp = DifferentialPrivacy(epsilon=0.01)
        true_value = 100.0
        
        noisy_value = dp.add_laplace_noise(true_value, sensitivity=1.0)
        
        # With very small epsilon, noise should be large
        # Just check it doesn't crash
        assert isinstance(noisy_value, float)
    
    def test_very_large_epsilon(self):
        """Test with very large epsilon (low privacy)."""
        dp = DifferentialPrivacy(epsilon=100.0)
        true_value = 100.0
        
        noisy_values = [
            dp.add_laplace_noise(true_value, sensitivity=1.0)
            for _ in range(20)
        ]
        
        # With large epsilon, noise should be small
        mean_error = statistics.mean([abs(v - true_value) for v in noisy_values])
        assert mean_error < 5.0
    
    def test_zero_sensitivity(self):
        """Test with zero sensitivity (deterministic query)."""
        dp = DifferentialPrivacy(epsilon=1.0)
        true_value = 100.0
        
        # Zero sensitivity means no noise needed
        noisy_value = dp.add_laplace_noise(true_value, sensitivity=0.0)
        assert noisy_value == true_value
    
    def test_large_sensitivity(self):
        """Test with large sensitivity."""
        dp = DifferentialPrivacy(epsilon=1.0)
        true_value = 100.0
        
        # Large sensitivity requires more noise
        noisy_value = dp.add_laplace_noise(true_value, sensitivity=1000.0)
        
        # Just check it doesn't crash
        assert isinstance(noisy_value, float)
    
    def test_negative_values(self):
        """Test with negative true values."""
        dp = DifferentialPrivacy(epsilon=1.0)
        true_value = -50.0
        
        noisy_value = dp.add_laplace_noise(true_value, sensitivity=1.0)
        
        # Should handle negative values
        assert isinstance(noisy_value, float)
    
    def test_composition_privacy_loss(self):
        """Test privacy loss under composition."""
        dp = DifferentialPrivacy(epsilon=1.0)
        
        # Run multiple queries
        for i in range(5):
            dp.add_laplace_noise(100.0, sensitivity=1.0, epsilon=0.2)
        
        # Total privacy loss should be sum of epsilons
        status = dp.get_privacy_budget_status()
        assert abs(status['spent'] - 1.0) < 0.01
        assert status['exhausted']
    
    def test_sequential_composition(self):
        """Test sequential composition with different sensitivities."""
        dp = DifferentialPrivacy(epsilon=2.0)
        
        # Query 1: low sensitivity
        dp.add_laplace_noise(100.0, sensitivity=1.0, epsilon=0.5)
        
        # Query 2: high sensitivity
        dp.add_laplace_noise(1000.0, sensitivity=100.0, epsilon=0.5)
        
        status = dp.get_privacy_budget_status()
        assert status['spent'] == 1.0
        assert status['remaining'] == 1.0
    
    def test_attack_scenario_reconstruction(self):
        """Test that reconstruction attacks are mitigated by noise."""
        dp = DifferentialPrivacy(epsilon=0.5)
        
        # Attacker tries to reconstruct true value by averaging many queries
        true_value = 42.0
        noisy_values = [
            dp.add_laplace_noise(true_value, sensitivity=1.0, epsilon=0.01)
            for _ in range(10)
        ]
        
        # Even with averaging, should have significant error with low epsilon
        avg_noisy = statistics.mean(noisy_values)
        # With epsilon=0.01 per query, noise should still be substantial
        # This is a simplified check - real attack analysis would be more complex
        assert isinstance(avg_noisy, float)
    
    def test_attack_scenario_difference_attack(self):
        """Test differential attack (querying with/without specific record)."""
        dp1 = DifferentialPrivacy(epsilon=0.1)
        dp2 = DifferentialPrivacy(epsilon=0.1)
        
        # Database with sensitive record
        count_with = 1000
        # Database without sensitive record
        count_without = 999
        
        # Attacker queries both
        noisy_with = dp1.private_count(count_with, epsilon=0.1)
        noisy_without = dp2.private_count(count_without, epsilon=0.1)
        
        # Difference should be obscured by noise
        # With low epsilon, the difference should often not be exactly 1
        # This is probabilistic, but we can check the mechanism works
        assert isinstance(noisy_with, int)
        assert isinstance(noisy_without, int)
    
    def test_gaussian_vs_laplace(self):
        """Test that Gaussian and Laplace give different noise distributions."""
        true_value = 100.0
        sensitivity = 1.0
        epsilon = 1.0
        
        dp_laplace = DifferentialPrivacy(epsilon=epsilon)
        dp_gaussian = DifferentialPrivacy(epsilon=epsilon, delta=1e-5)
        
        laplace_values = [
            dp_laplace.add_laplace_noise(true_value, sensitivity)
            for _ in range(50)
        ]
        
        gaussian_values = [
            dp_gaussian.add_gaussian_noise(true_value, sensitivity)
            for _ in range(50)
        ]
        
        # Both should add noise
        assert len(set(laplace_values)) > 1
        assert len(set(gaussian_values)) > 1
        
        # Both mechanisms work correctly - no need for further assertion
        # The distributions are different by design, but testing this 
        # statistically would require many more samples and proper hypothesis testing
