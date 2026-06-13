import hmac
import hashlib
import pytest
from app.security.middleware import FernetCipher, WebhookValidator, RateLimiter


class TestFernetCipher:
    def test_encrypt_decrypt_roundtrip(self):
        from tests.conftest import TEST_FERNET_KEY
        cipher = FernetCipher(key=TEST_FERNET_KEY)
        original = "12.345.678-9"
        encrypted = cipher.encrypt(original)
        assert encrypted != original
        assert cipher.decrypt(encrypted) == original

    def test_encrypt_returns_string(self):
        from tests.conftest import TEST_FERNET_KEY
        cipher = FernetCipher(key=TEST_FERNET_KEY)
        result = cipher.encrypt("test@email.com")
        assert isinstance(result, str)

    def test_decrypt_none_returns_none(self):
        from tests.conftest import TEST_FERNET_KEY
        cipher = FernetCipher(key=TEST_FERNET_KEY)
        assert cipher.decrypt(None) is None


class TestWebhookValidator:
    def test_valid_signature_passes(self):
        secret = "my_secret_token"
        body = b'{"message": "test"}'
        secret_hash = hashlib.sha256(secret.encode()).digest()
        sig = hmac.new(secret_hash, body, hashlib.sha256).hexdigest()
        validator = WebhookValidator(secret_token=secret)
        assert validator.is_valid(body, sig) is True

    def test_invalid_signature_fails(self):
        validator = WebhookValidator(secret_token="real_secret")
        assert validator.is_valid(b"body", "firma_falsa") is False


class TestRateLimiter:
    def test_allows_requests_under_limit(self):
        limiter = RateLimiter(max_per_minute=5)
        for _ in range(5):
            assert limiter.allow("user_123") is True

    def test_blocks_requests_over_limit(self):
        limiter = RateLimiter(max_per_minute=2)
        limiter.allow("user_456")
        limiter.allow("user_456")
        assert limiter.allow("user_456") is False

    def test_different_users_have_independent_limits(self):
        limiter = RateLimiter(max_per_minute=1)
        limiter.allow("user_A")
        assert limiter.allow("user_B") is True
