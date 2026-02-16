"""Analyzes function calls across files to build a call graph."""

import ast
import re
from typing import Dict, List, Set, Optional
from collections import defaultdict
from pathlib import Path


class CallGraphAnalyzer:
    """Analyzes function calls within and across files to build a call graph."""

    def __init__(self):
        """Initialize the call graph analyzer."""
        self.python_analyzer = PythonCallAnalyzer()
        self.javascript_analyzer = JavaScriptCallAnalyzer()

    def build_call_graph(self, files: Dict[str, str]) -> Dict:
        """
        Build a complete call graph across multiple files.

        Args:
            files: Dict of {file_path: file_content}

        Returns:
            {
                'calls': {file_path: {called_function: [calling_locations]}},
                'callers': {function_name: [files_that_call_it]},
                'hot_spots': [most_called_functions],
                'all_calls': {file_path: call_info}
            }
        """
        call_graph = defaultdict(lambda: defaultdict(list))
        all_calls = {}

        # Analyze each file
        for file_path, code in files.items():
            ext = Path(file_path).suffix

            try:
                if ext == '.py':
                    file_calls = self.python_analyzer.analyze_calls(file_path, code)
                elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                    file_calls = self.javascript_analyzer.analyze_calls(file_path, code)
                else:
                    continue

                all_calls[file_path] = file_calls

                # Build call relationships
                for call in file_calls.get('external_calls', []):
                    call_graph[file_path][call['name']].append(call.get('lineno', 0))

            except Exception:
                # If analysis fails, mark file as standalone
                all_calls[file_path] = {
                    'internal_calls': [],
                    'external_calls': [],
                    'function_defs': []
                }

        # Build reverse lookup (which files call which functions)
        callers = defaultdict(set)
        for file_path, calls in call_graph.items():
            for func_name in calls.keys():
                callers[func_name].add(file_path)

        # Find hot spots (most called functions)
        call_counts = defaultdict(int)
        for file_path, calls in call_graph.items():
            for func_name, locations in calls.items():
                call_counts[func_name] += len(locations)

        hot_spots = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'calls': dict(call_graph),
            'callers': {k: list(v) for k, v in callers.items()},
            'hot_spots': hot_spots,
            'all_calls': all_calls
        }


class PythonCallAnalyzer:
    """Analyzes Python function calls."""

    def analyze_calls(self, file_path: str, code: str) -> Dict:
        """
        Extract function calls from Python code.

        Returns:
            {
                'internal_calls': [calls to functions in same file],
                'external_calls': [calls to imported functions],
                'function_defs': [functions defined in this file]
            }
        """
        try:
            tree = ast.parse(code, filename=file_path)
        except SyntaxError:
            return {
                'internal_calls': [],
                'external_calls': [],
                'function_defs': []
            }

        calls = {
            'internal_calls': [],
            'external_calls': [],
            'function_defs': []
        }

        # Find all function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                calls['function_defs'].append({
                    'name': node.name,
                    'lineno': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'is_public': not node.name.startswith('_')
                })

        # Find all function calls
        defined_funcs = {f['name'] for f in calls['function_defs']}

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_info = self._extract_call_info(node)
                if call_info:
                    func_name = call_info['name']

                    # Determine if internal or external
                    if func_name in defined_funcs:
                        calls['internal_calls'].append(call_info)
                    else:
                        calls['external_calls'].append(call_info)

        return calls

    def _extract_call_info(self, node: ast.Call) -> Optional[Dict]:
        """Extract information about a function call."""
        try:
            if isinstance(node.func, ast.Name):
                return {
                    'name': node.func.id,
                    'lineno': node.lineno,
                    'args_count': len(node.args),
                    'type': 'simple'
                }
            elif isinstance(node.func, ast.Attribute):
                full_name = self._get_full_name(node.func)
                return {
                    'name': full_name,
                    'lineno': node.lineno,
                    'args_count': len(node.args),
                    'type': 'method'
                }
        except Exception:
            pass

        return None

    def _get_full_name(self, node) -> str:
        """Get full dotted name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_full_name(node.value)
            if base:
                return f"{base}.{node.attr}"
            return node.attr
        return ""


class JavaScriptCallAnalyzer:
    """Analyzes JavaScript/TypeScript function calls."""

    def analyze_calls(self, file_path: str, code: str) -> Dict:
        """
        Extract function calls from JavaScript/TypeScript code using regex.

        Returns:
            {
                'internal_calls': [calls to functions in same file],
                'external_calls': [calls to imported functions],
                'function_defs': [functions defined in this file]
            }
        """
        calls = {
            'internal_calls': [],
            'external_calls': [],
            'function_defs': []
        }

        # Extract function definitions
        # Function declarations: function name(...) or const name = (...) =>
        func_patterns = [
            r'function\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>',
            r'export\s+function\s+(\w+)\s*\(',
            r'export\s+const\s+(\w+)\s*=\s*\([^)]*\)\s*=>'
        ]

        for pattern in func_patterns:
            for match in re.finditer(pattern, code):
                func_name = match.group(1)
                line_num = code[:match.start()].count('\n') + 1
                calls['function_defs'].append({
                    'name': func_name,
                    'lineno': line_num,
                    'is_public': not func_name.startswith('_')
                })

        defined_funcs = {f['name'] for f in calls['function_defs']}

        # Extract function calls
        # Pattern: functionName( or object.method(
        call_pattern = r'(\w+(?:\.\w+)*)\s*\('

        for match in re.finditer(call_pattern, code):
            func_name = match.group(1)
            line_num = code[:match.start()].count('\n') + 1

            # Skip keywords and common patterns
            if func_name in ['if', 'for', 'while', 'switch', 'return', 'catch']:
                continue

            call_info = {
                'name': func_name,
                'lineno': line_num,
                'type': 'method' if '.' in func_name else 'simple'
            }

            # Determine if internal or external
            base_name = func_name.split('.')[0]
            if base_name in defined_funcs:
                calls['internal_calls'].append(call_info)
            else:
                calls['external_calls'].append(call_info)

        return calls
