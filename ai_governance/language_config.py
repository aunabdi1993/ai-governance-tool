"""
Language Configuration for AI Governance Tool.

Defines supported programming languages and their file extensions.
"""

from typing import Set, Dict, List


# Common programming languages and their file extensions
LANGUAGE_EXTENSIONS: Dict[str, Set[str]] = {
    'python': {'.py', '.pyw', '.pyx', '.pyi'},
    'javascript': {'.js', '.jsx', '.mjs', '.cjs'},
    'typescript': {'.ts', '.tsx'},
    'java': {'.java'},
    'c': {'.c', '.h'},
    'cpp': {'.cpp', '.cc', '.cxx', '.hpp', '.hxx', '.h++', '.hh'},
    'csharp': {'.cs'},
    'go': {'.go'},
    'rust': {'.rs'},
    'ruby': {'.rb', '.rake'},
    'php': {'.php', '.phtml'},
    'swift': {'.swift'},
    'kotlin': {'.kt', '.kts'},
    'scala': {'.scala', '.sc'},
    'r': {'.r', '.R'},
    'perl': {'.pl', '.pm'},
    'shell': {'.sh', '.bash', '.zsh', '.fish'},
    'sql': {'.sql'},
    'html': {'.html', '.htm'},
    'css': {'.css', '.scss', '.sass', '.less'},
    'xml': {'.xml'},
    'yaml': {'.yaml', '.yml'},
    'json': {'.json'},
    'markdown': {'.md', '.markdown'},
    'lua': {'.lua'},
    'dart': {'.dart'},
    'elixir': {'.ex', '.exs'},
    'erlang': {'.erl', '.hrl'},
    'haskell': {'.hs', '.lhs'},
    'clojure': {'.clj', '.cljs', '.cljc', '.edn'},
    'ocaml': {'.ml', '.mli'},
    'fsharp': {'.fs', '.fsx', '.fsi'},
    'vim': {'.vim'},
    'powershell': {'.ps1', '.psm1', '.psd1'},
    'matlab': {'.m'},
    'groovy': {'.groovy', '.gradle'},
    'terraform': {'.tf', '.tfvars'},
    'dockerfile': {'Dockerfile', '.dockerfile'},
    'makefile': {'Makefile', 'makefile', '.make'},
}


def get_all_extensions() -> Set[str]:
    """
    Get all supported file extensions.

    Returns:
        Set of all file extensions
    """
    all_extensions = set()
    for extensions in LANGUAGE_EXTENSIONS.values():
        all_extensions.update(extensions)
    return all_extensions


def get_extensions_for_language(language: str) -> Set[str]:
    """
    Get file extensions for a specific language.

    Args:
        language: Language name (case-insensitive)

    Returns:
        Set of file extensions for the language

    Raises:
        ValueError: If language is not supported
    """
    language_lower = language.lower()
    if language_lower not in LANGUAGE_EXTENSIONS:
        raise ValueError(
            f"Unsupported language: {language}. "
            f"Supported languages: {', '.join(sorted(LANGUAGE_EXTENSIONS.keys()))}"
        )
    return LANGUAGE_EXTENSIONS[language_lower]


def get_extensions_for_languages(languages: List[str]) -> Set[str]:
    """
    Get file extensions for multiple languages.

    Args:
        languages: List of language names

    Returns:
        Set of file extensions for all specified languages
    """
    extensions = set()
    for language in languages:
        extensions.update(get_extensions_for_language(language))
    return extensions


def get_language_for_extension(extension: str) -> str:
    """
    Get language name for a file extension.

    Args:
        extension: File extension (e.g., '.py', '.js')

    Returns:
        Language name or 'unknown' if not found
    """
    ext = extension if extension.startswith('.') else f'.{extension}'
    for language, extensions in LANGUAGE_EXTENSIONS.items():
        if ext in extensions:
            return language
    return 'unknown'


def parse_extensions(extensions_str: str) -> Set[str]:
    """
    Parse comma-separated extension string.

    Args:
        extensions_str: Comma-separated extensions (e.g., "py,js,ts" or ".py,.js,.ts")

    Returns:
        Set of extensions with leading dots
    """
    extensions = set()
    for ext in extensions_str.split(','):
        ext = ext.strip()
        if ext:
            # Add leading dot if not present
            if not ext.startswith('.'):
                ext = f'.{ext}'
            extensions.add(ext)
    return extensions


def get_supported_languages() -> List[str]:
    """
    Get list of all supported language names.

    Returns:
        Sorted list of language names
    """
    return sorted(LANGUAGE_EXTENSIONS.keys())
