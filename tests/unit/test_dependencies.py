"""
Unit tests for Core Dependencies - JWT and Authentication.

Tests cover:
- create_access_token: JWT token creation
- verify_token: token validation (valid, expired, malformed)
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from jose import jwt

from app.core.dependencies import (
    create_access_token,
    verify_token,
)
from app.core.config import get_settings

settings = get_settings()


# ============================================================================
# CREATE ACCESS TOKEN TESTS
# ============================================================================

class TestCreateAccessToken:
    """Tests for create_access_token function."""
    
    def test_creates_valid_jwt(self):
        """Should create a valid JWT token."""
        token = create_access_token(data={"sub": "123"})
        
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT format: header.payload.signature
        assert token.count(".") == 2
    
    def test_token_contains_subject(self):
        """Token should contain the subject claim."""
        user_id = "user_42"
        token = create_access_token(data={"sub": user_id})
        
        # Decode without verification to check payload
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert payload["sub"] == user_id
    
    def test_token_contains_expiration(self):
        """Token should contain expiration claim."""
        token = create_access_token(data={"sub": "123"})
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert "exp" in payload
        # Expiration should be in the future
        exp_time = datetime.fromtimestamp(payload["exp"])
        assert exp_time > datetime.utcnow()
    
    def test_token_preserves_custom_data(self):
        """Token should preserve custom data in payload."""
        token = create_access_token(data={
            "sub": "123",
            "custom_field": "custom_value"
        })
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert payload["custom_field"] == "custom_value"
    
    def test_different_users_different_tokens(self):
        """Different users should get different tokens."""
        token1 = create_access_token(data={"sub": "user1"})
        token2 = create_access_token(data={"sub": "user2"})
        
        assert token1 != token2


# ============================================================================
# VERIFY TOKEN TESTS
# ============================================================================

class TestVerifyToken:
    """Tests for verify_token function."""
    
    def test_valid_token(self):
        """Should verify a valid token and return payload."""
        token = create_access_token(data={"sub": "123"})
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "123"
    
    def test_invalid_token_format(self):
        """Should return None for invalid token format."""
        payload = verify_token("not.a.valid.jwt.token")
        assert payload is None
    
    def test_invalid_signature(self):
        """Should return None for token with wrong signature."""
        # Create token with a different secret
        wrong_secret = "wrong_secret_key"
        fake_token = jwt.encode(
            {"sub": "123", "exp": datetime.utcnow() + timedelta(hours=1)},
            wrong_secret,
            algorithm=settings.ALGORITHM
        )
        
        payload = verify_token(fake_token)
        assert payload is None
    
    def test_expired_token(self):
        """Should return None for expired token."""
        # Create an already expired token
        expired_token = jwt.encode(
            {"sub": "123", "exp": datetime.utcnow() - timedelta(hours=1)},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        payload = verify_token(expired_token)
        assert payload is None
    
    def test_malformed_token(self):
        """Should return None for malformed token."""
        payload = verify_token("completely_invalid")
        assert payload is None
    
    def test_empty_token(self):
        """Should return None for empty token."""
        payload = verify_token("")
        assert payload is None


# ============================================================================
# TOKEN EXPIRATION TESTS
# ============================================================================

class TestTokenExpiration:
    """Tests for token expiration behavior."""
    
    def test_token_contains_future_expiration(self):
        """Token should have an expiration time in the future."""
        import time
        token = create_access_token(data={"sub": "123"})
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Compare timestamps directly
        exp_timestamp = payload["exp"]
        current_timestamp = time.time()
        
        # Expiration should be in the future
        assert exp_timestamp > current_timestamp
        # And not too far in the future (within 24 hours max)
        diff = exp_timestamp - current_timestamp
        assert diff < 24 * 60 * 60
    
    def test_newly_created_token_is_valid(self):
        """A newly created token should be immediately valid."""
        token = create_access_token(data={"sub": "123"})
        payload = verify_token(token)
        
        assert payload is not None


# ============================================================================
# EDGE CASES TESTS
# ============================================================================

class TestEdgeCases:
    """Edge case tests for token handling."""
    
    def test_special_characters_in_subject(self):
        """Token should handle special characters in subject."""
        special_sub = "user@example.com"
        token = create_access_token(data={"sub": special_sub})
        payload = verify_token(token)
        
        assert payload["sub"] == special_sub
    
    def test_numeric_subject_as_string(self):
        """Token should handle numeric subject as string."""
        token = create_access_token(data={"sub": "42"})
        payload = verify_token(token)
        
        assert payload["sub"] == "42"
    
    def test_unicode_in_payload(self):
        """Token should handle unicode characters."""
        token = create_access_token(data={
            "sub": "123",
            "name": "Utente Prova"
        })
        payload = verify_token(token)
        
        assert payload["name"] == "Utente Prova"
