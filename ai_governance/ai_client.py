"""AI client for interacting with Claude API for code refactoring."""

import os
from typing import Dict, Optional
from anthropic import Anthropic


class AIClient:
    """Client for AI-powered code refactoring using Claude."""

    # Pricing for Claude Sonnet 4 (as of 2025)
    # These are approximate values - adjust based on actual pricing
    INPUT_PRICE_PER_1M = 3.0  # USD per 1M input tokens
    OUTPUT_PRICE_PER_1M = 15.0  # USD per 1M output tokens

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-5-20250929"):
        """Initialize AI client.

        Args:
            api_key: Anthropic API key. If not provided, reads from ANTHROPIC_API_KEY env var
            model: Model to use for refactoring
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter"
            )

        self.model = model
        self.client = Anthropic(api_key=self.api_key)

    def refactor_code(
        self,
        code: str,
        target_description: str,
        filepath: str
    ) -> Dict:
        """Refactor code using Claude API.

        Args:
            code: Source code to refactor
            target_description: Description of desired refactoring
            filepath: Path to source file (for context)

        Returns:
            Dictionary with:
            - success: bool
            - refactored_code: str (if successful)
            - error: str (if failed)
            - tokens_used: dict with input and output tokens
            - cost: float (estimated cost in USD)
        """
        try:
            # Build prompt
            prompt = self._build_refactor_prompt(code, target_description, filepath)

            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract refactored code
            refactored_code = message.content[0].text

            # Calculate tokens and cost
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            total_tokens = input_tokens + output_tokens

            cost = self._calculate_cost(input_tokens, output_tokens)

            return {
                'success': True,
                'refactored_code': refactored_code,
                'tokens_used': {
                    'input': input_tokens,
                    'output': output_tokens,
                    'total': total_tokens
                },
                'cost': cost,
                'model': self.model
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tokens_used': {'input': 0, 'output': 0, 'total': 0},
                'cost': 0.0,
                'model': self.model
            }

    def _build_refactor_prompt(
        self,
        code: str,
        target_description: str,
        filepath: str
    ) -> str:
        """Build the refactoring prompt for Claude.

        Args:
            code: Source code
            target_description: Refactoring target
            filepath: Source file path

        Returns:
            Formatted prompt string
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

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        input_cost = (input_tokens / 1_000_000) * self.INPUT_PRICE_PER_1M
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_PRICE_PER_1M

        return round(input_cost + output_cost, 6)

    def estimate_cost(self, code: str, target_description: str) -> Dict:
        """Estimate the cost of refactoring without making the API call.

        Args:
            code: Source code
            target_description: Refactoring target

        Returns:
            Dictionary with estimated tokens and cost
        """
        # Rough estimation: ~4 characters per token
        estimated_input_tokens = len(code + target_description) // 4
        estimated_output_tokens = len(code) // 4  # Assume similar length output

        estimated_cost = self._calculate_cost(
            estimated_input_tokens,
            estimated_output_tokens
        )

        return {
            'estimated_input_tokens': estimated_input_tokens,
            'estimated_output_tokens': estimated_output_tokens,
            'estimated_total_tokens': estimated_input_tokens + estimated_output_tokens,
            'estimated_cost': estimated_cost
        }
