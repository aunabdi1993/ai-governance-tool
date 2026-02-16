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
            # Parse error for user-friendly messages
            error_message = self._parse_api_error(e)

            return {
                'success': False,
                'error': error_message,
                'tokens_used': {'input': 0, 'output': 0, 'total': 0},
                'cost': 0.0,
                'model': self.model
            }

    def _parse_api_error(self, error: Exception) -> str:
        """Parse API errors into user-friendly messages.

        Args:
            error: Exception from API call

        Returns:
            User-friendly error message
        """
        error_str = str(error)

        # Check for specific error types
        if 'rate_limit_error' in error_str or '429' in error_str:
            return (
                "Rate limit exceeded. You're making requests too quickly. "
                "Please wait a moment and try again."
            )

        elif 'insufficient_quota' in error_str or 'quota' in error_str.lower():
            return (
                "API quota exceeded. Your account has run out of credits. "
                "Please check your usage at https://console.anthropic.com/ "
                "and add more credits to continue."
            )

        elif 'invalid_api_key' in error_str or 'authentication_error' in error_str or '401' in error_str:
            return (
                "Invalid API key. Please check your API key is correct. "
                "Run 'ai-governance init' to reconfigure."
            )

        elif 'overloaded_error' in error_str or '529' in error_str:
            return (
                "Anthropic's API is temporarily overloaded. "
                "Please wait a few moments and try again."
            )

        elif 'timeout' in error_str.lower() or 'timed out' in error_str.lower():
            return (
                "Request timed out. The API took too long to respond. "
                "Please try again with a smaller file or simpler refactoring goal."
            )

        elif 'network' in error_str.lower() or 'connection' in error_str.lower():
            return (
                "Network error. Please check your internet connection and try again."
            )

        # Generic error - show original message
        return f"API error: {error_str}"

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

    def refactor_with_context(
        self,
        code: str,
        target_description: str,
        filepath: str,
        context_files: Optional[Dict[str, str]] = None,
        dependency_info: Optional[Dict] = None
    ) -> Dict:
        """
        Refactor code with awareness of related files and dependencies.

        Args:
            code: Source code to refactor
            target_description: Description of desired refactoring
            filepath: Path to source file
            context_files: Dict of {file_path: file_content} for related files
            dependency_info: Dependency analysis results with imports/exports

        Returns:
            Dictionary with same structure as refactor_code()
        """
        try:
            # Build context-aware prompt
            prompt = self._build_context_aware_prompt(
                code, target_description, filepath,
                context_files or {}, dependency_info or {}
            )

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
            error_message = self._parse_api_error(e)
            return {
                'success': False,
                'error': error_message,
                'tokens_used': {'input': 0, 'output': 0, 'total': 0},
                'cost': 0.0,
                'model': self.model
            }

    def _build_context_aware_prompt(
        self,
        code: str,
        target_description: str,
        filepath: str,
        context_files: Dict[str, str],
        dependency_info: Dict
    ) -> str:
        """
        Build a context-aware refactoring prompt that includes related files.

        Args:
            code: Source code to refactor
            target_description: Refactoring goal
            filepath: Path to source file
            context_files: Related file contents
            dependency_info: Imports/exports information

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert code refactoring assistant working on a multi-file codebase. Your task is to refactor the specified file while maintaining compatibility with related files.

Source File: {filepath}
Refactoring Goal: {target_description}

"""

        # Add dependency context
        if dependency_info:
            imports = dependency_info.get('imports', {}).get(filepath, [])
            exports = dependency_info.get('exports', {}).get(filepath, [])

            if imports:
                prompt += "This file imports from:\n"
                for imp in imports[:5]:  # Limit to avoid token overflow
                    module = imp.get('module', '')
                    symbols = imp.get('symbols', [])
                    prompt += f"  - {module}: {', '.join(symbols)}\n"
                prompt += "\n"

            if exports:
                prompt += "This file exports:\n"
                for exp in exports[:10]:  # Limit to avoid token overflow
                    name = exp.get('name', '') if isinstance(exp, dict) else exp
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
        """
        Summarize a file's public interface to save tokens.
        Extracts key exports, function signatures, and class definitions.

        Args:
            content: File content
            filepath: File path to determine language

        Returns:
            Summarized interface
        """
        # Limit to first 2000 characters for context
        max_chars = 2000

        if len(content) <= max_chars:
            return content

        # For longer files, extract key parts
        lines = content.split('\n')
        summary_lines = []

        # Include imports (first 20 lines typically)
        for i, line in enumerate(lines[:20]):
            if any(keyword in line for keyword in ['import', 'from', 'require', 'export']):
                summary_lines.append(line)

        summary_lines.append('\n// ... (additional implementation details omitted) ...\n')

        # Include function/class definitions
        for line in lines:
            if any(keyword in line for keyword in ['def ', 'class ', 'function ', 'export function', 'export class']):
                summary_lines.append(line)

        summary = '\n'.join(summary_lines)

        # If still too long, truncate
        if len(summary) > max_chars:
            summary = summary[:max_chars] + '\n// ... (truncated) ...'

        return summary
