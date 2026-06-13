import hmac
import hashlib
from cryptography.fernet import Fernet
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Optional


class FernetCipher:
    def __init__(self, key: str):
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: Optional[str]) -> Optional[str]:
        if ciphertext is None:
            return None
        return self._fernet.decrypt(ciphertext.encode()).decode()


class WebhookValidator:
    def __init__(self, secret_token: str):
        # Telegram firma con HMAC-SHA256 usando SHA256(secret_token) como clave
        self._key = hashlib.sha256(secret_token.encode()).digest()

    def is_valid(self, body: bytes, signature: str) -> bool:
        expected = hmac.new(self._key, body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)


class RateLimiter:
    def __init__(self, max_per_minute: int):
        self._max = max_per_minute
        self._counts: dict[str, list[datetime]] = defaultdict(list)

    def allow(self, user_id: str) -> bool:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=1)
        self._counts[user_id] = [t for t in self._counts[user_id] if t > cutoff]
        if len(self._counts[user_id]) >= self._max:
            return False
        self._counts[user_id].append(now)
        return True
