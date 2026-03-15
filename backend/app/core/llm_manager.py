import logging
import os
from typing import Any


class LLMKeyRotator:
    def __init__(self, prefix: str = "GEMINI_API_KEY"):
        self.prefix = prefix
        self.keys: list[str] = []
        self.valid: list[bool] = []
        self.key_map: dict[str, int] = {}

        i = 1
        while True:
            key = os.getenv(f"{prefix}_{i}")
            if not key:
                break
            self.key_map[key] = len(self.keys)
            self.keys.append(key)
            self.valid.append(True)
            i += 1

        if not self.keys:
            key = os.getenv(prefix)
            if key:
                self.key_map[key] = 0
                self.keys = [key]
                self.valid = [True]

        self.index = 0

    def get_next_key(self) -> str:
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
        idx = self.key_map[key]
        self.valid[idx] = False
        valid_count = sum(self.valid)
        logging.warning(f"[LLM] Key {idx + 1}/{len(self.keys)} rate-limited. {valid_count} keys remaining.")

    def reset_validity(self):
        self.valid = [True] * len(self.keys)
        logging.info(f"[LLM] Reset all {len(self.keys)} keys to valid status.")

    def get_status(self) -> dict[str, Any]:
        return {
            "total_keys": len(self.keys),
            "valid_keys": sum(self.valid),
            "current_index": self.index,
        }
