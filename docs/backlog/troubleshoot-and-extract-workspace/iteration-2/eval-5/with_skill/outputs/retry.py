"""
Retry utilities with exponential backoff and jitter.
Use this module for resilient Supabase operations.
"""

import asyncio
import random
from typing import Callable, TypeVar, Any, Coroutine

R = TypeVar("R")


async def retry_with_backoff(
    fn: Callable[[], Coroutine[Any, Any, R]],
    max_retries: int = 3,
    initial_delay: float = 0.5,
    max_delay: float = 10.0,
    jitter: bool = True,
) -> R:
    """
    Retry async function with exponential backoff and optional jitter.

    Args:
        fn: Async function to retry
        max_retries: Maximum number of attempts (total attempts = max_retries + 1)
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        jitter: Whether to add random jitter to delay

    Returns:
        Result of successful function call

    Raises:
        Exception: Original exception from final attempt if all retries fail
    """
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except Exception as e:
            if attempt == max_retries:
                raise
            delay = initial_delay * (2 ** attempt)
            if jitter:
                delay = min(delay + random.uniform(0, delay * 0.1), max_delay)
            else:
                delay = min(delay, max_delay)
            await asyncio.sleep(delay)


async def retry_with_backoff_sync(
    fn: Callable[[], R],
    max_retries: int = 3,
    initial_delay: float = 0.5,
    max_delay: float = 10.0,
    jitter: bool = True,
) -> R:
    """
    Retry sync function with exponential backoff (wraps in async).
    Use this for non-async functions that need retry logic.

    Args:
        fn: Synchronous function to retry
        max_retries: Maximum number of attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        jitter: Whether to add random jitter to delay

    Returns:
        Result of successful function call

    Raises:
        Exception: Original exception from final attempt if all retries fail
    """

    async def async_wrapper():
        return fn()

    return await retry_with_backoff(
        async_wrapper,
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay,
        jitter=jitter,
    )
