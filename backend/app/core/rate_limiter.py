import time
from collections import deque
from typing import ClassVar


class RateLimiter:
    _instances: ClassVar[dict[str, "RateLimiter"]] = {}

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque[float] = deque()

    @classmethod
    def get_limiter(cls, name: str, max_requests: int, window_seconds: int) -> "RateLimiter":
        if name not in cls._instances:
            cls._instances[name] = cls(max_requests, window_seconds)
        return cls._instances[name]

    def acquire(self) -> bool:
        now = time.time()
        while self.requests and self.requests[0] <= now - self.window_seconds:
            self.requests.popleft()

        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
