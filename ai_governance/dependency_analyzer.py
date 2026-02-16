"""
Dependency analyzer for building cross-file dependency graphs.
Supports Python with extensibility for other languages.
"""

import ast
import os
from pathlib import Path
from typing import Dict, Set, List, Tuple, Optional
from collections import defaultdict
import re


class DependencyAnalyzer:
    """Analyzes code dependencies across multiple files."""

    def __init__(self, language: str = "python"):
        self.language = language.lower()
        self.analyzers = {
            "python": PythonDependencyAnalyzer(),
            "javascript": JavaScriptDependencyAnalyzer(),
            "typescript": TypeScriptDependencyAnalyzer(),
        }

    def analyze_project(self, file_paths: List[str]) -> Dict:
        """
        Build dependency graph for a list of files.

        Returns:
            dict: {
                'imports': {file_path: [imported_modules]},
                'exports': {file_path: [exported_symbols]},
                'callers': {symbol: [files_that_use_it]},
                'groups': [[related_files]],
                'order': [file_paths_in_refactor_order]
            }
        """
        # Group files by language
        files_by_lang = self._group_by_language(file_paths)

        # Analyze each language group
        all_imports = {}
        all_exports = {}

        for lang, files in files_by_lang.items():
            analyzer = self.analyzers.get(lang)
            if not analyzer:
                # Skip unsupported languages
                continue

            for file_path in files:
                try:
                    imports = analyzer.extract_imports(file_path)
                    exports = analyzer.extract_exports(file_path)

                    all_imports[file_path] = imports
                    all_exports[file_path] = exports
                except Exception as e:
                    # If analysis fails, mark file as standalone
                    all_imports[file_path] = []
                    all_exports[file_path] = []

        # Build reverse lookup (who uses what)
        callers = self._build_callers(all_imports, all_exports, file_paths)

        # Cluster related files
        groups = self._cluster_files(all_imports, all_exports, file_paths)

        # Determine refactoring order (topological sort)
        order = self._topological_sort(all_imports, file_paths)

        return {
            'imports': all_imports,
            'exports': all_exports,
            'callers': callers,
            'groups': groups,
            'order': order
        }

    def _group_by_language(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """Group files by programming language."""
        groups = defaultdict(list)

        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
        }

        for file_path in file_paths:
            ext = Path(file_path).suffix
            lang = ext_to_lang.get(ext, 'unknown')
            groups[lang].append(file_path)

        return dict(groups)

    def _build_callers(self, imports: Dict, exports: Dict, file_paths: List[str]) -> Dict[str, Set[str]]:
        """Build reverse lookup of which files use which symbols."""
        callers = defaultdict(set)

        for file_path, imported_modules in imports.items():
            for module_info in imported_modules:
                module_name = module_info.get('module', '')
                symbols = module_info.get('symbols', [])

                # Find which file exports this module
                for export_file in file_paths:
                    if self._matches_module(export_file, module_name):
                        # Track that file_path uses symbols from export_file
                        for symbol in symbols:
                            callers[f"{export_file}::{symbol}"].add(file_path)

        return dict(callers)

    def _matches_module(self, file_path: str, module_name: str) -> bool:
        """Check if a file matches a module import."""
        # Convert file path to module notation
        file_module = file_path.replace('/', '.').replace('\\', '.').replace('.py', '')
        return module_name in file_module or file_module.endswith(module_name)

    def _cluster_files(self, imports: Dict, exports: Dict, file_paths: List[str]) -> List[List[str]]:
        """
        Cluster related files into groups for batch refactoring.
        Files are related if they import from each other or share dependencies.
        """
        # Build adjacency list
        graph = defaultdict(set)

        for file_path, imported_modules in imports.items():
            for module_info in imported_modules:
                module_name = module_info.get('module', '')

                # Find which files this imports from
                for other_file in file_paths:
                    if file_path != other_file and self._matches_module(other_file, module_name):
                        graph[file_path].add(other_file)
                        graph[other_file].add(file_path)  # Bidirectional

        # Find connected components using DFS
        visited = set()
        clusters = []

        for file_path in file_paths:
            if file_path not in visited:
                cluster = self._dfs_cluster(file_path, graph, visited)
                clusters.append(sorted(cluster))

        return clusters

    def _dfs_cluster(self, start: str, graph: Dict, visited: Set) -> List[str]:
        """DFS to find connected component."""
        stack = [start]
        cluster = []

        while stack:
            node = stack.pop()
            if node in visited:
                continue

            visited.add(node)
            cluster.append(node)

            # Add neighbors
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    stack.append(neighbor)

        return cluster

    def _topological_sort(self, imports: Dict, file_paths: List[str]) -> List[str]:
        """
        Topological sort for refactoring order.
        Dependencies should be refactored before dependents.
        """
        # Build dependency graph
        in_degree = {f: 0 for f in file_paths}
        adj_list = defaultdict(list)

        for file_path, imported_modules in imports.items():
            for module_info in imported_modules:
                module_name = module_info.get('module', '')

                # Find dependency
                for other_file in file_paths:
                    if file_path != other_file and self._matches_module(other_file, module_name):
                        adj_list[other_file].append(file_path)
                        in_degree[file_path] += 1

        # Kahn's algorithm
        queue = [f for f in file_paths if in_degree[f] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in adj_list[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If not all files processed, there's a cycle - use original order
        if len(result) != len(file_paths):
            return file_paths

        return result


class PythonDependencyAnalyzer:
    """Analyzes Python file dependencies using AST."""

    def extract_imports(self, file_path: str) -> List[Dict]:
        """Extract import statements from Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            'module': alias.name,
                            'symbols': [alias.asname or alias.name],
                            'type': 'import'
                        })

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        symbols = [alias.name for alias in node.names]
                        imports.append({
                            'module': node.module,
                            'symbols': symbols,
                            'type': 'from_import'
                        })

            return imports

        except Exception as e:
            return []

    def extract_exports(self, file_path: str) -> List[str]:
        """Extract exported symbols (functions, classes) from Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)
            exports = []

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):  # Public function
                        exports.append({
                            'name': node.name,
                            'type': 'function',
                            'signature': self._get_function_signature(node)
                        })

                elif isinstance(node, ast.ClassDef):
                    if not node.name.startswith('_'):  # Public class
                        methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                        exports.append({
                            'name': node.name,
                            'type': 'class',
                            'methods': methods
                        })

                elif isinstance(node, ast.Assign):
                    # Module-level variables
                    for target in node.targets:
                        if isinstance(target, ast.Name) and not target.id.startswith('_'):
                            exports.append({
                                'name': target.id,
                                'type': 'variable'
                            })

            return exports

        except Exception as e:
            return []

    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature."""
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        return f"{node.name}({', '.join(args)})"


class JavaScriptDependencyAnalyzer:
    """Analyzes JavaScript/JSX file dependencies using regex patterns."""

    def extract_imports(self, file_path: str) -> List[Dict]:
        """Extract import statements from JavaScript file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            imports = []

            # ES6 imports: import { x, y } from 'module'
            es6_pattern = r"import\s+(?:{([^}]+)}|\*\s+as\s+(\w+)|(\w+))\s+from\s+['\"]([^'\"]+)['\"]"
            for match in re.finditer(es6_pattern, content):
                named, star, default, module = match.groups()
                symbols = []

                if named:
                    symbols = [s.strip() for s in named.split(',')]
                elif star:
                    symbols = [star]
                elif default:
                    symbols = [default]

                imports.append({
                    'module': module,
                    'symbols': symbols,
                    'type': 'import'
                })

            # CommonJS: require
            require_pattern = r"(?:const|let|var)\s+(?:{([^}]+)}|(\w+))\s*=\s*require\(['\"]([^'\"]+)['\"]\)"
            for match in re.finditer(require_pattern, content):
                named, default, module = match.groups()
                symbols = []

                if named:
                    symbols = [s.strip() for s in named.split(',')]
                elif default:
                    symbols = [default]

                imports.append({
                    'module': module,
                    'symbols': symbols,
                    'type': 'require'
                })

            return imports

        except Exception as e:
            return []

    def extract_exports(self, file_path: str) -> List[str]:
        """Extract exported symbols from JavaScript file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            exports = []

            # Named exports: export function/class/const
            named_pattern = r"export\s+(?:function|class|const|let|var)\s+(\w+)"
            for match in re.finditer(named_pattern, content):
                exports.append({
                    'name': match.group(1),
                    'type': 'named_export'
                })

            # Export list: export { x, y }
            list_pattern = r"export\s+{([^}]+)}"
            for match in re.finditer(list_pattern, content):
                names = [n.strip() for n in match.group(1).split(',')]
                for name in names:
                    exports.append({
                        'name': name,
                        'type': 'named_export'
                    })

            # Default export
            default_pattern = r"export\s+default\s+(\w+)"
            for match in re.finditer(default_pattern, content):
                exports.append({
                    'name': match.group(1),
                    'type': 'default_export'
                })

            return exports

        except Exception as e:
            return []


class TypeScriptDependencyAnalyzer(JavaScriptDependencyAnalyzer):
    """
    Analyzes TypeScript/TSX file dependencies.
    Extends JavaScript analyzer with type imports.
    """

    def extract_imports(self, file_path: str) -> List[Dict]:
        """Extract import statements including type imports."""
        # Get base JS imports
        imports = super().extract_imports(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Type imports: import type { Type } from 'module'
            type_pattern = r"import\s+type\s+{([^}]+)}\s+from\s+['\"]([^'\"]+)['\"]"
            for match in re.finditer(type_pattern, content):
                symbols, module = match.groups()
                imports.append({
                    'module': module,
                    'symbols': [s.strip() for s in symbols.split(',')],
                    'type': 'type_import'
                })

            return imports

        except Exception as e:
            return imports
