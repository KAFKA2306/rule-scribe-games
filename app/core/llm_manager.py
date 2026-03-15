from typing import List
import os


class LLMKeyRotator:
    """Round-robin API key rotator for high-volume LLM workloads."""

    def __init__(self, prefix: str = "GEMINI_API_KEY"):
        """Load all numbered API keys (KEY_1, KEY_2, etc.) from environment."""
        self.prefix = prefix
        self.keys: List[str] = []
        self.valid: List[bool] = []

        # Load numbered keys (KEY_1, KEY_2, etc.)
        i = 1
        while True:
            key = os.getenv(f"{prefix}_{i}")
            if not key:
                break
            self.keys.append(key)
            self.valid.append(True)
            i += 1

        # Fallback to single key
        if not self.keys:
            key = os.getenv(prefix)
            if key:
                self.keys = [key]
                self.valid = [True]

        self.index = 0

    def get_next_key(self) -> str:
        """Get next valid key, round-robin style."""
        if not self.keys:
            raise ValueError(f"No API keys configured for {self.prefix}")

        attempts = 0
        while attempts < len(self.keys):
            idx = self.index % len(self.keys)
            self.index += 1
            if self.valid[idx]:
                return self.keys[idx]
            attempts += 1

        raise RuntimeError("All API keys are rate-limited. Try again in 1 hour.")

    def mark_rate_limited(self, key: str):
        """Mark a key as temporarily invalid (rate-limited)."""
        try:
            idx = self.keys.index(key)
            self.valid[idx] = False
            valid_count = sum(self.valid)
            import logging
            logging.warning(
                f"[LLM] Key {idx + 1}/{len(self.keys)} rate-limited. "
                f"{valid_count} keys remaining."
            )
        except ValueError:
            pass

    def reset_validity(self):
        """Reset all keys to valid (call periodically, e.g., hourly)."""
        self.valid = [True] * len(self.keys)
        import logging
        logging.info(f"[LLM] Reset all {len(self.keys)} keys to valid status.")

    def get_status(self) -> dict:
        """Get current key manager status."""
        return {
            "total_keys": len(self.keys),
            "valid_keys": sum(self.valid),
            "current_index": self.index,
        }
