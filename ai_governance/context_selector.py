"""Smart context selection for refactoring based on relevance scoring."""

from typing import Dict, List, Tuple
from pathlib import Path


class ContextSelector:
    """Selects most relevant files for context based on multiple factors."""

    def select_context_files(
        self,
        target_file: str,
        all_files: Dict[str, str],
        dep_graph: Dict,
        max_context_files: int = 5,
        max_context_tokens: int = 6000
    ) -> Dict[str, str]:
        """
        Select most relevant files for context using multi-factor scoring.

        Scoring factors:
        - Direct imports/exports (highest priority - 100 points)
        - Function calls (medium priority - 50 points per call)
        - Shared dependencies (low priority - 10 points per shared import)
        - File proximity (same directory - 20 points)
        - Size penalty (prefer smaller files to save tokens)

        Args:
            target_file: The file being refactored
            all_files: All available files {path: content}
            dep_graph: Dependency graph with imports, exports, call_graph
            max_context_files: Maximum number of context files to include
            max_context_tokens: Maximum tokens for all context files

        Returns:
            Dict of {file_path: file_content} for selected context files
        """
        scores = {}

        for other_file, content in all_files.items():
            if other_file == target_file:
                continue

            score = 0.0

            # Factor 1: Direct dependency (highest priority)
            if self._has_direct_dependency(target_file, other_file, dep_graph):
                score += 100

            # Factor 2: Call graph relationship
            call_score = self._get_call_graph_score(target_file, other_file, dep_graph)
            score += call_score * 50

            # Factor 3: Reverse dependency (files that depend on target)
            if self._has_direct_dependency(other_file, target_file, dep_graph):
                score += 80  # Important to see who uses this file

            # Factor 4: Shared imports (common dependencies)
            shared_imports = self._count_shared_imports(target_file, other_file, dep_graph)
            score += shared_imports * 10

            # Factor 5: File proximity (same directory)
            if self._are_files_nearby(target_file, other_file):
                score += 20

            # Factor 6: Similar naming (likely related functionality)
            if self._have_similar_names(target_file, other_file):
                score += 15

            # Factor 7: Size penalty (prefer smaller files to save tokens)
            size_penalty = len(content) / 1000
            score -= size_penalty

            scores[other_file] = score

        # Sort by score and select top N
        ranked_files = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Select files within token budget
        selected = {}
        total_tokens = 0

        for file_path, score in ranked_files[:max_context_files * 2]:  # Check 2x files
            if score <= 0:  # Stop at negative scores
                break

            file_content = all_files[file_path]
            estimated_tokens = len(file_content) // 4

            if total_tokens + estimated_tokens <= max_context_tokens:
                selected[file_path] = file_content
                total_tokens += estimated_tokens

                if len(selected) >= max_context_files:
                    break

        return selected

    def _has_direct_dependency(self, file1: str, file2: str, dep_graph: Dict) -> bool:
        """Check if file1 directly imports from file2."""
        imports = dep_graph.get('imports', {}).get(file1, [])

        for imp in imports:
            module = imp.get('module', '')
            # Normalize paths for comparison
            file2_normalized = file2.replace('/', '.').replace('\\', '.').replace('.py', '').replace('.js', '').replace('.ts', '')

            if module in file2 or file2_normalized in module or module in file2_normalized:
                return True

        return False

    def _get_call_graph_score(self, file1: str, file2: str, dep_graph: Dict) -> float:
        """
        Calculate call graph relationship strength.

        Returns a score based on how many functions in file2 are called by file1.
        """
        call_graph = dep_graph.get('call_graph', {})

        if not call_graph:
            return 0

        callers = call_graph.get('callers', {})
        all_calls = call_graph.get('all_calls', {})

        # Get functions defined in file2
        file2_calls = all_calls.get(file2, {})
        file2_functions = {f['name'] for f in file2_calls.get('function_defs', [])}

        # Count how many of file2's functions are called by file1
        call_count = 0

        for func_name in file2_functions:
            if file1 in callers.get(func_name, []):
                call_count += 1

        return call_count

    def _count_shared_imports(self, file1: str, file2: str, dep_graph: Dict) -> int:
        """Count shared import dependencies between two files."""
        imports1 = {imp.get('module') for imp in dep_graph.get('imports', {}).get(file1, [])}
        imports2 = {imp.get('module') for imp in dep_graph.get('imports', {}).get(file2, [])}

        # Count intersection
        shared = imports1 & imports2
        return len(shared)

    def _are_files_nearby(self, file1: str, file2: str) -> bool:
        """Check if files are in same or nearby directories."""
        dir1 = Path(file1).parent
        dir2 = Path(file2).parent

        # Same directory
        if dir1 == dir2:
            return True

        # Parent-child relationship
        try:
            dir1.relative_to(dir2)
            return True
        except ValueError:
            pass

        try:
            dir2.relative_to(dir1)
            return True
        except ValueError:
            pass

        return False

    def _have_similar_names(self, file1: str, file2: str) -> bool:
        """Check if files have similar names (likely related)."""
        name1 = Path(file1).stem.lower()
        name2 = Path(file2).stem.lower()

        # Check for common prefixes/suffixes
        # e.g., user_model.py and user_controller.py
        if len(name1) >= 4 and len(name2) >= 4:
            # Share prefix
            if name1[:4] == name2[:4] or name1[:5] == name2[:5]:
                return True

            # One contains the other
            if name1 in name2 or name2 in name1:
                return True

        return False

    def get_context_summary(self, selected_files: Dict[str, str]) -> str:
        """
        Generate a summary of selected context files.

        Args:
            selected_files: Dict of {file_path: content}

        Returns:
            Human-readable summary
        """
        if not selected_files:
            return "No context files selected"

        total_tokens = sum(len(content) // 4 for content in selected_files.values())
        file_list = "\n".join(f"  - {path}" for path in selected_files.keys())

        return f"Selected {len(selected_files)} context files (~{total_tokens} tokens):\n{file_list}"
