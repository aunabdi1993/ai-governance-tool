"""Claude provider implementation using Anthropic API.

This module provides the ClaudeProvider class which implements the AIProvider
interface for Anthropic's Claude models. It includes comprehensive error handling,
retry logic, and token usage tracking.

Example:
    >>> from ai_governance.providers import ClaudeProvider
    >>> provider = ClaudeProvider(api_key="sk-...", model="claude-sonnet-4-5-20250929")
    >>> result = provider.refactor_code(
    ...     code="def foo(): pass",
    ...     target_description="add type hints",
    ...     filepath="main.py"
    ... )
    >>> if result.success:
    ...     print(f"Refactored code: {result.refactored_code}")
    ...     print(f"Cost: ${result.cost}")
    ... else:
    ...     print(f"Error: {result.error}")
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any, Dict, Optional

from anthropic import Anthropic, APIError, APIConnectionError, APITimeoutError

from ..core.base import AIProvider
from ..core.exceptions import (
    ProviderAuthError,
    ProviderError,
    ProviderQuotaError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from ..core.types import CostEstimate, RefactorResult, TokenUsage
from ..utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class ClaudeProvider(AIProvider):
    """Claude AI provider implementation using Anthropic API.

    This provider implements the AIProvider interface for Anthropic's Claude models.
    It handles all API interactions, error mapping, cost calculation, and retry logic.

    Pricing (as of 2025):
        - Claude Sonnet 4.5: $3.00 per 1M input tokens, $15.00 per 1M output tokens
        - Other models may have different pricing

    Attributes:
        api_key: Anthropic API key for authentication.
        model: Model identifier (default: "claude-sonnet-4-5-20250929").
        client: Anthropic client instance.
        max_tokens: Maximum tokens for API responses (default: 4096).

    Example:
        >>> provider = ClaudeProvider(api_key="sk-...", model="claude-sonnet-4-5-20250929")
        >>> result = provider.refactor_code(
        ...     code="def foo(): pass",
        ...     target_description="add type hints",
        ...     filepath="main.py"
        ... )
    """

    # Pricing constants (USD per 1M tokens)
    INPUT_PRICE_PER_1M = 3.0
    OUTPUT_PRICE_PER_1M = 15.0
    MAX_TOKENS = 4096
    DEFAULT_MODEL = "claude-sonnet-4-5-20250929"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = MAX_TOKENS,
    ) -> None:
        """Initialize Claude provider.

        Args:
            api_key: Anthropic API key. If not provided, reads from ANTHROPIC_API_KEY env var.
            model: Model to use for refactoring (default: claude-sonnet-4-5-20250929).
            max_tokens: Maximum tokens for API responses (default: 4096).

        Raises:
            ProviderAuthError: If API key is missing or invalid.

        Example:
            >>> provider = ClaudeProvider(api_key="sk-...", model="claude-sonnet-4-5-20250929")
            >>> # Or let it read from environment:
            >>> provider = ClaudeProvider()
        """
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ProviderAuthError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter",
                provider="claude",
            )

        super().__init__(api_key=api_key, model=model or self.DEFAULT_MODEL)

        self.max_tokens = max_tokens
        self.client = Anthropic(api_key=self.api_key)

        logger.info(f"Initialized ClaudeProvider with model: {self.model}")

    @retry_with_backoff(
        max_attempts=3,
        backoff_factor=2.0,
        initial_delay=1.0,
        max_delay=60.0,
    )
    def refactor_code(
        self,
        code: str,
        target_description: str,
        filepath: str,
    ) -> RefactorResult:
        """Refactor code using Claude API.

        Args:
            code: Source code to refactor.
            target_description: Description of desired refactoring.
            filepath: Path to source file (for context).

        Returns:
            RefactorResult with success status, refactored code, and token usage.

        Raises:
            ProviderAuthError: If authentication fails.
            ProviderRateLimitError: If rate limit is exceeded.
            ProviderTimeoutError: If request times out.
            ProviderError: For other API errors.

        Example:
            >>> result = provider.refactor_code(
            ...     code="def foo(): pass",
            ...     target_description="add type hints",
            ...     filepath="main.py"
            ... )
            >>> if result.success:
            ...     print(f"Refactored: {result.refactored_code}")
        """
        try:
            # Build refactoring prompt
            prompt = self._build_refactor_prompt(code, target_description, filepath)

            logger.debug(f"Calling Claude API for refactoring {filepath}")

            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract refactored code
            refactored_code = message.content[0].text

            # Calculate tokens and cost
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            total_tokens = input_tokens + output_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)

            logger.info(
                f"Successfully refactored {filepath}: "
                f"{input_tokens} input, {output_tokens} output tokens, ${cost:.6f}"
            )

            return RefactorResult(
                success=True,
                refactored_code=refactored_code,
                tokens_used=TokenUsage(
                    input=input_tokens,
                    output=output_tokens,
                    total=total_tokens,
                ),
                cost=cost,
                model=self.model,
            )

        except Exception as e:
            error_result = self._handle_api_error(e, filepath)
            logger.error(f"Failed to refactor {filepath}: {error_result.error}")
            return error_result

    @retry_with_backoff(
        max_attempts=3,
        backoff_factor=2.0,
        initial_delay=1.0,
        max_delay=60.0,
    )
    def refactor_with_context(
        self,
        code: str,
        target_description: str,
        filepath: str,
        context_files: Optional[Dict[str, str]] = None,
        dependency_info: Optional[Dict[str, Any]] = None,
    ) -> RefactorResult:
        """Refactor code with awareness of related files and dependencies.

        Args:
            code: Source code to refactor.
            target_description: Description of desired refactoring.
            filepath: Path to source file.
            context_files: Dict of {file_path: file_content} for related files.
            dependency_info: Dependency analysis results with imports/exports.

        Returns:
            RefactorResult with same structure as refactor_code().

        Raises:
            ProviderAuthError: If authentication fails.
            ProviderRateLimitError: If rate limit is exceeded.
            ProviderTimeoutError: If request times out.
            ProviderError: For other API errors.

        Example:
            >>> context_files = {"utils.py": "def helper(): pass"}
            >>> dependency_info = {"imports": {"main.py": [{"module": "utils", "symbols": ["helper"]}]}}
            >>> result = provider.refactor_with_context(
            ...     code="from utils import helper",
            ...     target_description="refactor imports",
            ...     filepath="main.py",
            ...     context_files=context_files,
            ...     dependency_info=dependency_info
            ... )
        """
        try:
            # Build context-aware prompt
            prompt = self._build_context_aware_prompt(
                code,
                target_description,
                filepath,
                context_files or {},
                dependency_info or {},
            )

            logger.debug(f"Calling Claude API with context for {filepath}")

            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract refactored code
            refactored_code = message.content[0].text

            # Calculate tokens and cost
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            total_tokens = input_tokens + output_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)

            logger.info(
                f"Successfully refactored {filepath} with context: "
                f"{input_tokens} input, {output_tokens} output tokens, ${cost:.6f}"
            )

            return RefactorResult(
                success=True,
                refactored_code=refactored_code,
                tokens_used=TokenUsage(
                    input=input_tokens,
                    output=output_tokens,
                    total=total_tokens,
                ),
                cost=cost,
                model=self.model,
            )

        except Exception as e:
            error_result = self._handle_api_error(e, filepath)
            logger.error(f"Failed to refactor {filepath} with context: {error_result.error}")
            return error_result

    def estimate_cost(self, code: str, target_description: str) -> CostEstimate:
        """Estimate the cost of refactoring without making the API call.

        Uses a rough estimation: approximately 4 characters per token.

        Args:
            code: Source code.
            target_description: Refactoring target.

        Returns:
            CostEstimate with estimated tokens and cost.

        Example:
            >>> estimate = provider.estimate_cost(
            ...     code="def foo(): pass",
            ...     target_description="add type hints"
            ... )
            >>> print(f"Estimated cost: ${estimate.estimated_cost:.6f}")
        """
        # Rough estimation: ~4 characters per token
        estimated_input_tokens = len(code + target_description) // 4
        estimated_output_tokens = len(code) // 4  # Assume similar length output

        estimated_cost = self._calculate_cost(
            estimated_input_tokens,
            estimated_output_tokens,
        )

        return CostEstimate(
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            estimated_total_tokens=estimated_input_tokens + estimated_output_tokens,
            estimated_cost=estimated_cost,
        )

    @lru_cache(maxsize=1)
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the provider and model.

        Returns:
            Dictionary with provider name, model ID, pricing, and capabilities.

        Example:
            >>> info = provider.get_model_info()
            >>> print(info["provider"])
            "claude"
            >>> print(info["model"])
            "claude-sonnet-4-5-20250929"
        """
        return {
            "provider": "claude",
            "model": self.model,
            "input_price_per_1m": self.INPUT_PRICE_PER_1M,
            "output_price_per_1m": self.OUTPUT_PRICE_PER_1M,
            "max_tokens": self.max_tokens,
            "capabilities": [
                "refactor_code",
                "refactor_with_context",
                "estimate_cost",
                "cost_tracking",
            ],
        }

    # ─── Private Methods ───────────────────────────────────────────────────────

    def _build_refactor_prompt(
        self,
        code: str,
        target_description: str,
        filepath: str,
    ) -> str:
        """Build the refactoring prompt for Claude.

        Args:
            code: Source code.
            target_description: Refactoring target.
            filepath: Source file path.

        Returns:
            Formatted prompt string.
        """
        prompt = f"""You are an expert code refactoring assistant. Your task is to refactor the provided code according to the specified requirements.

Source File: {filepath}
Refactoring Goal: {target_description}

Original Code:
```
{code}
```

Please refactor this code according to the goal. Follow these guidelines:
1. Preserve all functionality while improving code quality
2. Apply modern best practices and patterns
3. Improve readability and maintainability
4. Add appropriate comments where helpful
5. Ensure the refactored code is production-ready

Provide ONLY the refactored code in your response, without explanations or markdown code blocks unless they are part of the code itself."""

        return prompt

    def _build_context_aware_prompt(
        self,
        code: str,
        target_description: str,
        filepath: str,
        context_files: Dict[str, str],
        dependency_info: Dict[str, Any],
    ) -> str:
        """Build a context-aware refactoring prompt that includes related files.

        Args:
            code: Source code to refactor.
            target_description: Refactoring goal.
            filepath: Path to source file.
            context_files: Related file contents.
            dependency_info: Imports/exports information.

        Returns:
            Formatted prompt string.
        """
        prompt = f"""You are an expert code refactoring assistant working on a multi-file codebase. Your task is to refactor the specified file while maintaining compatibility with related files.

Source File: {filepath}
Refactoring Goal: {target_description}

"""

        # Add dependency context
        if dependency_info:
            imports = dependency_info.get("imports", {}).get(filepath, [])
            exports = dependency_info.get("exports", {}).get(filepath, [])

            if imports:
                prompt += "This file imports from:\n"
                for imp in imports[:5]:  # Limit to avoid token overflow
                    module = imp.get("module", "")
                    symbols = imp.get("symbols", [])
                    prompt += f"  - {module}: {', '.join(symbols)}\n"
                prompt += "\n"

            if exports:
                prompt += "This file exports:\n"
                for exp in exports[:10]:  # Limit to avoid token overflow
                    name = exp.get("name", "") if isinstance(exp, dict) else exp
                    prompt += f"  - {name}\n"
                prompt += "\n"

        # Add related file context (summarized to save tokens)
        if context_files:
            prompt += "RELATED FILES (for context - DO NOT modify these):\n\n"

            for related_path, related_content in list(context_files.items())[:3]:  # Limit to 3 files
                # Extract key signatures/exports only to save tokens
                summary = self._summarize_file_interface(related_content, related_path)
                prompt += f"## {related_path}\n```\n{summary}\n```\n\n"

        # Add the main file to refactor
        prompt += f"FILE TO REFACTOR:\n## {filepath}\n```\n{code}\n```\n\n"

        prompt += """REFACTORING REQUIREMENTS:
1. Maintain compatibility with imported interfaces and types
2. Preserve backward compatibility for all exported functions/classes/variables
3. Ensure function signatures remain compatible if other files depend on them
4. Update import statements if necessary, but maintain existing functionality
5. Apply modern best practices and improve code quality
6. Add comments to explain complex logic
7. Ensure the refactored code is production-ready

CRITICAL: If this file exports symbols used by other files, you MUST NOT:
- Change exported function/class names
- Modify function signatures (parameter names, order, or types)
- Remove exported symbols
- Break type compatibility

Provide ONLY the refactored code in your response, without explanations or markdown code blocks unless they are part of the code itself."""

        return prompt

    def _summarize_file_interface(self, content: str, filepath: str) -> str:
        """Summarize a file's public interface to save tokens.

        Extracts key exports, function signatures, and class definitions.

        Args:
            content: File content.
            filepath: File path to determine language.

        Returns:
            Summarized interface.
        """
        # Limit to first 2000 characters for context
        max_chars = 2000

        if len(content) <= max_chars:
            return content

        # For longer files, extract key parts
        lines = content.split("\n")
        summary_lines = []

        # Include imports (first 20 lines typically)
        for i, line in enumerate(lines[:20]):
            if any(keyword in line for keyword in ["import", "from", "require", "export"]):
                summary_lines.append(line)

        summary_lines.append("\n// ... (additional implementation details omitted) ...\n")

        # Include function/class definitions
        for line in lines:
            if any(
                keyword in line
                for keyword in ["def ", "class ", "function ", "export function", "export class"]
            ):
                summary_lines.append(line)

        summary = "\n".join(summary_lines)

        # If still too long, truncate
        if len(summary) > max_chars:
            summary = summary[:max_chars] + "\n// ... (truncated) ..."

        return summary

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Cost in USD.
        """
        input_cost = (input_tokens / 1_000_000) * self.INPUT_PRICE_PER_1M
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_PRICE_PER_1M

        return round(input_cost + output_cost, 6)

    def _handle_api_error(self, error: Exception, filepath: str) -> RefactorResult:
        """Handle API errors and map them to custom exceptions.

        Args:
            error: Exception from API call.
            filepath: File path being processed (for context).

        Returns:
            RefactorResult with error details.

        Raises:
            Specific ProviderError subclass if the error is retryable.
        """
        error_str = str(error)
        error_type = type(error).__name__

        logger.debug(f"Handling API error: {error_type}: {error_str}")

        # Authentication errors (should not retry)
        if isinstance(error, APIError):
            if "401" in error_str or "invalid_api_key" in error_str.lower():
                exc = ProviderAuthError(
                    "Invalid API key. Please check your API key is correct. "
                    "Run 'ai-governance init' to reconfigure.",
                    provider="claude",
                    status_code=401,
                )
                logger.error(f"Authentication error: {exc}")
                return RefactorResult(
                    success=False,
                    error=exc.message,
                    tokens_used=TokenUsage(input=0, output=0, total=0),
                    cost=0.0,
                    model=self.model,
                )

            # Rate limit errors (retryable)
            elif "429" in error_str or "rate_limit" in error_str.lower():
                exc = ProviderRateLimitError(
                    "Rate limit exceeded. You're making requests too quickly. "
                    "Please wait a moment and try again.",
                    provider="claude",
                    retry_after=None,
                )
                logger.warning(f"Rate limit error: {exc}")
                raise exc

            # Quota errors (should not retry)
            elif (
                "quota" in error_str.lower()
                or "insufficient_quota" in error_str.lower()
            ):
                exc = ProviderQuotaError(
                    "API quota exceeded. Your account has run out of credits. "
                    "Please check your usage at https://console.anthropic.com/ "
                    "and add more credits to continue.",
                    provider="claude",
                )
                logger.error(f"Quota error: {exc}")
                return RefactorResult(
                    success=False,
                    error=exc.message,
                    tokens_used=TokenUsage(input=0, output=0, total=0),
                    cost=0.0,
                    model=self.model,
                )

            # API overloaded (retryable)
            elif "529" in error_str or "overloaded" in error_str.lower():
                exc = ProviderUnavailableError(
                    "Anthropic's API is temporarily overloaded. "
                    "Please wait a few moments and try again.",
                    provider="claude",
                    status_code=529,
                )
                logger.warning(f"API overloaded: {exc}")
                raise exc

        # Timeout errors (retryable)
        elif isinstance(error, APITimeoutError):
            exc = ProviderTimeoutError(
                "Request timed out. The API took too long to respond. "
                "Please try again with a smaller file or simpler refactoring goal.",
                provider="claude",
            )
            logger.warning(f"Timeout error: {exc}")
            raise exc

        # Connection errors (retryable)
        elif isinstance(error, APIConnectionError):
            exc = ProviderTimeoutError(
                "Network error. Please check your internet connection and try again.",
                provider="claude",
            )
            logger.warning(f"Connection error: {exc}")
            raise exc

        # Generic error
        else:
            exc = ProviderError(
                f"API error: {error_str}",
                provider="claude",
            )
            logger.error(f"Provider error: {exc}")
            return RefactorResult(
                success=False,
                error=exc.message,
                tokens_used=TokenUsage(input=0, output=0, total=0),
                cost=0.0,
                model=self.model,
            )
