"""
Legacy Utility Functions - Clean code, no sensitive data
This file should PASS the security scanner and be allowed for refactoring
"""

import re
from datetime import datetime


def format_date(date_obj, format_string='%Y-%m-%d'):
    """Format a date object to string - old implementation"""
    if not date_obj:
        return None
    return date_obj.strftime(format_string)


def parse_date(date_string, format_string='%Y-%m-%d'):
    """Parse a date string to datetime object - old implementation"""
    try:
        return datetime.strptime(date_string, format_string)
    except ValueError:
        return None


def validate_username(username):
    """Validate username format - legacy regex pattern"""
    if not username:
        return False

    # Old pattern: 3-20 chars, alphanumeric and underscore
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None


def sanitize_input(user_input):
    """Sanitize user input - basic implementation"""
    if not user_input:
        return ""

    # Remove potentially dangerous characters
    sanitized = user_input.strip()
    sanitized = sanitized.replace('<', '&lt;')
    sanitized = sanitized.replace('>', '&gt;')
    sanitized = sanitized.replace('"', '&quot;')

    return sanitized


def calculate_age(birth_date):
    """Calculate age from birth date - old implementation"""
    if not birth_date:
        return None

    today = datetime.today()
    age = today.year - birth_date.year

    # Adjust if birthday hasn't occurred this year
    if today.month < birth_date.month:
        age -= 1
    elif today.month == birth_date.month and today.day < birth_date.day:
        age -= 1

    return age


def truncate_string(text, max_length, suffix='...'):
    """Truncate a string to maximum length - legacy method"""
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    truncated_length = max_length - len(suffix)
    return text[:truncated_length] + suffix


def generate_slug(title):
    """Generate URL slug from title - old implementation"""
    if not title:
        return ""

    # Convert to lowercase
    slug = title.lower()

    # Replace spaces with hyphens
    slug = slug.replace(' ', '-')

    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)

    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    return slug


def chunk_list(lst, chunk_size):
    """Split a list into chunks - old implementation"""
    if not lst or chunk_size <= 0:
        return []

    chunks = []
    for i in range(0, len(lst), chunk_size):
        chunks.append(lst[i:i + chunk_size])

    return chunks


def merge_dictionaries(dict1, dict2):
    """Merge two dictionaries - Python 2.x compatible way"""
    result = dict1.copy()
    result.update(dict2)
    return result


# Example usage
if __name__ == "__main__":
    # Test date formatting
    today = datetime.now()
    print(format_date(today))

    # Test username validation
    print(validate_username("john_doe"))  # True
    print(validate_username("ab"))  # False

    # Test slug generation
    print(generate_slug("Hello World Example"))  # hello-world-example
