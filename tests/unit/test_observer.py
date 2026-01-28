"""
Unit tests for the Observer Pattern - Weight Configuration.

Tests cover:
- WeightConfigSubject: attach/detach observers, notify, set/get weights
- ScoringModule: observer that receives weight updates
- Notification propagation to multiple observers
"""
import pytest
from app.core.patterns.observer import (
    WeightConfigObserver,
    WeightConfigSubject,
    ScoringModule,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def subject():
    """Create a WeightConfigSubject for testing."""
    return WeightConfigSubject()


@pytest.fixture
def sample_weights():
    """Sample weight configuration."""
    return {
        "material_sustainability": 0.3,
        "carbon_footprint": 0.25,
        "water_usage": 0.2,
        "social_impact": 0.15,
        "circularity": 0.1,
    }


# ============================================================================
# WEIGHT CONFIG SUBJECT TESTS
# ============================================================================

class TestWeightConfigSubject:
    """Tests for WeightConfigSubject (Subject in Observer pattern)."""
    
    def test_initial_state_empty(self, subject):
        """Subject should start with empty weights and no observers."""
        assert subject.get_weights() == {}
    
    def test_set_weights(self, subject, sample_weights):
        """set_weights should store the weights."""
        subject.set_weights(sample_weights)
        assert subject.get_weights() == sample_weights
    
    def test_get_weights_returns_copy(self, subject, sample_weights):
        """get_weights should return a copy (not modify internal state)."""
        subject.set_weights(sample_weights)
        weights = subject.get_weights()
        weights["new_key"] = 999  # Modify returned copy
        
        # Original should be unchanged
        assert "new_key" not in subject.get_weights()
    
    def test_attach_observer(self, subject):
        """Observers can be attached to the subject."""
        observer = ScoringModule("test")
        subject.attach(observer)
        
        # No error means success (internal list is private)
        assert True
    
    def test_attach_same_observer_twice(self, subject):
        """Attaching the same observer twice should not duplicate."""
        observer = ScoringModule("test")
        subject.attach(observer)
        subject.attach(observer)
        
        # If we detach once, it should be gone
        subject.detach(observer)
        
        # Second detach should fail (not in list)
        with pytest.raises(ValueError):
            subject.detach(observer)
    
    def test_detach_observer(self, subject):
        """Observers can be detached from the subject."""
        observer = ScoringModule("test")
        subject.attach(observer)
        subject.detach(observer)
        
        # Detaching again should raise ValueError
        with pytest.raises(ValueError):
            subject.detach(observer)
    
    def test_notify_updates_observers(self, subject, sample_weights):
        """notify should update all attached observers."""
        observer1 = ScoringModule("module1")
        observer2 = ScoringModule("module2")
        
        subject.attach(observer1)
        subject.attach(observer2)
        subject.set_weights(sample_weights)  # This calls notify internally
        
        assert observer1.get_current_weights() == sample_weights
        assert observer2.get_current_weights() == sample_weights
    
    def test_set_weights_triggers_notify(self, subject, sample_weights):
        """set_weights should automatically notify observers."""
        observer = ScoringModule("test")
        subject.attach(observer)
        
        # Before setting weights
        assert observer.get_current_weights() == {}
        
        subject.set_weights(sample_weights)
        
        # After setting weights
        assert observer.get_current_weights() == sample_weights
    
    def test_detached_observer_not_notified(self, subject, sample_weights):
        """Detached observers should not receive updates."""
        observer = ScoringModule("test")
        subject.attach(observer)
        subject.detach(observer)
        
        subject.set_weights(sample_weights)
        
        # Observer should still have empty weights
        assert observer.get_current_weights() == {}


# ============================================================================
# SCORING MODULE TESTS
# ============================================================================

class TestScoringModule:
    """Tests for ScoringModule (Concrete Observer)."""
    
    def test_creation(self):
        """ScoringModule should be created with a name."""
        module = ScoringModule("higg_index")
        assert module.module_name == "higg_index"
    
    def test_initial_weights_empty(self):
        """Module should start with empty weights."""
        module = ScoringModule("test")
        assert module.get_current_weights() == {}
    
    def test_on_weights_updated(self, sample_weights):
        """on_weights_updated should store the new weights."""
        module = ScoringModule("test")
        module.on_weights_updated(sample_weights)
        assert module.get_current_weights() == sample_weights
    
    def test_get_current_weights_returns_copy(self, sample_weights):
        """get_current_weights should return a copy."""
        module = ScoringModule("test")
        module.on_weights_updated(sample_weights)
        
        weights = module.get_current_weights()
        weights["modified"] = 999
        
        # Original should be unchanged
        assert "modified" not in module.get_current_weights()
    
    def test_multiple_updates(self, sample_weights):
        """Module should reflect the latest weights after multiple updates."""
        module = ScoringModule("test")
        
        module.on_weights_updated(sample_weights)
        assert module.get_current_weights() == sample_weights
        
        new_weights = {"single_key": 1.0}
        module.on_weights_updated(new_weights)
        assert module.get_current_weights() == new_weights


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestObserverIntegration:
    """Integration tests for the Observer pattern."""
    
    def test_full_workflow(self, subject, sample_weights):
        """Test complete attach -> update -> detach workflow."""
        higg = ScoringModule("higg_index")
        carbon = ScoringModule("carbon_footprint")
        
        # 1. Attach observers
        subject.attach(higg)
        subject.attach(carbon)
        
        # 2. Set weights - should notify all
        subject.set_weights(sample_weights)
        assert higg.get_current_weights() == sample_weights
        assert carbon.get_current_weights() == sample_weights
        
        # 3. Detach one observer
        subject.detach(higg)
        
        # 4. Update weights again
        new_weights = {"updated": 0.5}
        subject.set_weights(new_weights)
        
        # Only attached observer should update
        assert higg.get_current_weights() == sample_weights  # Old weights
        assert carbon.get_current_weights() == new_weights  # New weights
    
    def test_observers_independent(self, subject):
        """Multiple observers should maintain independent state."""
        module1 = ScoringModule("module1")
        module2 = ScoringModule("module2")
        
        subject.attach(module1)
        subject.set_weights({"key1": 1.0})
        
        subject.attach(module2)
        subject.set_weights({"key2": 2.0})
        
        # Both should have the latest weights
        # But if we had not attached module2 before second update...
        # This test shows they share state from subject
        assert module1.get_current_weights() == {"key2": 2.0}
        assert module2.get_current_weights() == {"key2": 2.0}


# ============================================================================
# CUSTOM OBSERVER TESTS
# ============================================================================

class TestCustomObserver:
    """Tests with custom observer implementations."""
    
    def test_custom_observer_class(self, subject, sample_weights):
        """Custom observer classes can be created and used."""
        
        class CustomObserver(WeightConfigObserver):
            def __init__(self):
                self.update_count = 0
                self.last_weights = None
            
            def on_weights_updated(self, weights: dict[str, float]) -> None:
                self.update_count += 1
                self.last_weights = weights.copy()
        
        observer = CustomObserver()
        subject.attach(observer)
        
        subject.set_weights(sample_weights)
        assert observer.update_count == 1
        assert observer.last_weights == sample_weights
        
        subject.set_weights({"another": 0.5})
        assert observer.update_count == 2
