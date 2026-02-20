"""Retry logic with exponential backoff for AI API calls.

Provides a decorator and utility class for retrying functions that may fail
due to rate limits, temporary network issues, or API unavailability.

Example:
    >>> from ai_governance.utils.retry import retry_with_backoff, RetryConfig
    >>> from ai_governance.core.exceptions import ProviderRateLimitError
    >>>
    >>> @retry_with_backoff(
    ...     max_attempts=3,
    ...     backoff_factor=2.0,
    ...     exceptions=(ProviderRateLimitError,),
    ... )
    ... def call_api():
    ...     # API call that might fail
    ...     pass
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type, TypeVar

from ..core.exceptions import (
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)

# Type variable for generic function signatures
F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of retry attempts (default: 3).
        backoff_factor: Multiplier for exponential backoff (default: 2.0).
        initial_delay: Initial delay in seconds before first retry (default: 1.0).
        max_delay: Maximum delay in seconds between retries (default: 60.0).
        exceptions: Tuple of exception types to retry on (default: common provider errors).
        on_retry: Optional callback function called before each retry.

    Example:
        >>> config = RetryConfig(
        ...     max_attempts=5,
        ...     backoff_factor=2.0,
        ...     initial_delay=2.0,
        ... )
    """

    max_attempts: int = 3
    backoff_factor: float = 2.0
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exceptions: Tuple[Type[Exception], ...] = (
        ProviderRateLimitError,
        ProviderTimeoutError,
        ProviderUnavailableError,
    )
    on_retry: Optional[Callable[[Exception, int, float], None]] = None

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number using exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed).

        Returns:
            Delay in seconds, capped at max_delay.

        Example:
            >>> config = RetryConfig(initial_delay=1.0, backoff_factor=2.0, max_delay=30.0)
            >>> config.calculate_delay(0)  # First retry
            1.0
            >>> config.calculate_delay(1)  # Second retry
            2.0
            >>> config.calculate_delay(2)  # Third retry
            4.0
        """
        delay = self.initial_delay * (self.backoff_factor**attempt)
        return min(delay, self.max_delay)


def retry_with_backoff(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (
        ProviderRateLimitError,
        ProviderTimeoutError,
        ProviderUnavailableError,
    ),
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
) -> Callable[[F], F]:
    """Decorator for retrying functions with exponential backoff.

    Automatically retries the decorated function when it raises specified exceptions,
    with increasing delays between attempts.

    Args:
        max_attempts: Maximum number of retry attempts.
        backoff_factor: Multiplier for exponential backoff.
        initial_delay: Initial delay in seconds before first retry.
        max_delay: Maximum delay in seconds between retries.
        exceptions: Tuple of exception types to retry on.
        on_retry: Optional callback called before each retry (receives exception, attempt, delay).

    Returns:
        Decorated function with retry logic.

    Example:
        >>> @retry_with_backoff(max_attempts=3, backoff_factor=2.0)
        ... def fetch_data():
        ...     response = api_client.get("/data")
        ...     return response.json()

        >>> # With custom retry callback
        >>> def log_retry(exc: Exception, attempt: int, delay: float):
        ...     print(f"Retry {attempt}/{max_attempts} after {delay}s due to: {exc}")
        >>>
        >>> @retry_with_backoff(max_attempts=5, on_retry=log_retry)
        ... def call_external_api():
        ...     # ...
        ...     pass

    Raises:
        The last exception encountered if all retries are exhausted.
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        backoff_factor=backoff_factor,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exceptions=exceptions,
        on_retry=on_retry,
    )

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e

                    # If this is the last attempt, re-raise immediately
                    if attempt == config.max_attempts - 1:
                        logger.warning(
                            f"All {config.max_attempts} retry attempts exhausted for {func.__name__}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = config.calculate_delay(attempt)

                    # Handle rate limit errors specially (use retry_after if provided)
                    if isinstance(e, ProviderRateLimitError) and hasattr(e, "retry_after"):
                        if e.retry_after is not None:
                            delay = float(e.retry_after)

                    logger.info(
                        f"Retry {attempt + 1}/{config.max_attempts} for {func.__name__} "
                        f"after {delay:.2f}s due to: {e}"
                    )

                    # Call retry callback if provided
                    if config.on_retry:
                        config.on_retry(e, attempt + 1, delay)

                    # Wait before retrying
                    time.sleep(delay)

            # This should never be reached, but satisfy type checkers
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Unexpected retry logic error in {func.__name__}")

        return wrapper  # type: ignore

    return decorator


def should_retry(exception: Exception, retryable_exceptions: Tuple[Type[Exception], ...]) -> bool:
    """Check if an exception is retryable.

    Args:
        exception: The exception to check.
        retryable_exceptions: Tuple of exception types that should be retried.

    Returns:
        True if the exception should trigger a retry, False otherwise.

    Example:
        >>> from ai_governance.core.exceptions import ProviderRateLimitError, ProviderAuthError
        >>> exc = ProviderRateLimitError("Too many requests")
        >>> should_retry(exc, (ProviderRateLimitError, ProviderTimeoutError))
        True
        >>> exc = ProviderAuthError("Invalid API key")
        >>> should_retry(exc, (ProviderRateLimitError, ProviderTimeoutError))
        False
    """
    return isinstance(exception, retryable_exceptions)
