"""
Batch processor with rate limiting and error handling.
Use this module to safely process large datasets with controlled concurrency.
"""

import asyncio
from typing import Callable, TypeVar, List, Any, Coroutine
from app.core import logger

T = TypeVar("T")
R = TypeVar("R")


async def batch_process(
    items: List[T],
    process_fn: Callable[[T], Coroutine[Any, Any, R]],
    batch_size: int = 5,
    delay_between_batches: float = 0.5,
    on_error: str = "raise",  # "raise", "skip", or "log"
) -> List[R]:
    """
    Process items in controlled batches with rate limiting.

    Args:
        items: List of items to process
        process_fn: Async function to apply to each item
        batch_size: Number of items per batch
        delay_between_batches: Seconds to wait between batches
        on_error: How to handle errors ("raise", "skip", "log")

    Returns:
        List of results (empty for skipped items if on_error="skip")
    """
    results = []
    total_batches = (len(items) + batch_size - 1) // batch_size

    for batch_idx in range(0, len(items), batch_size):
        batch_num = batch_idx // batch_size + 1
        batch = items[batch_idx : batch_idx + batch_size]

        logger.info(
            f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)"
        )

        try:
            batch_results = await asyncio.gather(
                *[process_fn(item) for item in batch],
                return_exceptions=on_error != "raise",
            )

            for result in batch_results:
                if isinstance(result, Exception):
                    if on_error == "raise":
                        raise result
                    elif on_error == "skip":
                        logger.warning(f"Skipped item due to error: {result}")
                    elif on_error == "log":
                        logger.error(f"Error processing item: {result}")
                else:
                    results.append(result)

        except Exception as e:
            logger.error(f"Batch {batch_num} failed: {e}")
            if on_error == "raise":
                raise
            else:
                continue

        if batch_idx + batch_size < len(items):
            logger.info(f"Waiting {delay_between_batches}s before next batch...")
            await asyncio.sleep(delay_between_batches)

    logger.info(f"Batch processing complete: {len(results)}/{len(items)} items")
    return results


async def batch_process_with_retry(
    items: List[T],
    process_fn: Callable[[T], Coroutine[Any, Any, R]],
    batch_size: int = 5,
    delay_between_batches: float = 0.5,
    max_retries: int = 3,
) -> tuple[List[R], List[T]]:
    """
    Process items with automatic retry on failure.

    Args:
        items: List of items to process
        process_fn: Async function to apply to each item
        batch_size: Number of items per batch
        delay_between_batches: Seconds to wait between batches
        max_retries: Number of retries per item

    Returns:
        Tuple of (successful_results, failed_items)
    """
    results = []
    failed_items = []

    for batch_idx in range(0, len(items), batch_size):
        batch_num = batch_idx // batch_size + 1
        batch = items[batch_idx : batch_idx + batch_size]

        logger.info(f"Processing batch {batch_num} ({len(batch)} items)")

        for item in batch:
            success = False
            for attempt in range(1, max_retries + 1):
                try:
                    result = await process_fn(item)
                    results.append(result)
                    success = True
                    break
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(f"Item {item} failed after {max_retries} attempts: {e}")
                    else:
                        wait_time = 2 ** attempt  # exponential backoff
                        logger.warning(
                            f"Item {item} attempt {attempt} failed, retrying in {wait_time}s: {e}"
                        )
                        await asyncio.sleep(wait_time)

            if not success:
                failed_items.append(item)

        if batch_idx + batch_size < len(items):
            await asyncio.sleep(delay_between_batches)

    logger.info(
        f"Batch processing complete: {len(results)} succeeded, {len(failed_items)} failed"
    )
    return results, failed_items
