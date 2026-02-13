"""
Legacy Helper Functions - Clean code for string and list operations
This file should PASS the security scanner and be allowed for refactoring
"""


def capitalize_words(text):
    """Capitalize first letter of each word - old implementation"""
    if not text:
        return ""

    words = text.split()
    capitalized = []

    for word in words:
        if len(word) > 0:
            capitalized.append(word[0].upper() + word[1:].lower())

    return ' '.join(capitalized)


def reverse_string(text):
    """Reverse a string - legacy method"""
    if not text:
        return ""

    return text[::-1]


def count_words(text):
    """Count words in text - old implementation"""
    if not text:
        return 0

    words = text.split()
    return len(words)


def remove_duplicates(items):
    """Remove duplicates from list - old Python 2.x way"""
    if not items:
        return []

    seen = []
    result = []

    for item in items:
        if item not in seen:
            seen.append(item)
            result.append(item)

    return result


def find_common_elements(list1, list2):
    """Find common elements between two lists - old implementation"""
    if not list1 or not list2:
        return []

    common = []
    for item in list1:
        if item in list2 and item not in common:
            common.append(item)

    return common


def flatten_list(nested_list):
    """Flatten a nested list - recursive old method"""
    if not nested_list:
        return []

    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)

    return result


def group_by_length(strings):
    """Group strings by their length - old dictionary approach"""
    if not strings:
        return {}

    groups = {}
    for string in strings:
        length = len(string)
        if length not in groups:
            groups[length] = []
        groups[length].append(string)

    return groups


def calculate_average(numbers):
    """Calculate average of numbers - old implementation"""
    if not numbers:
        return 0

    total = 0
    count = 0

    for num in numbers:
        total += num
        count += 1

    if count == 0:
        return 0

    return total / float(count)


def find_max_min(numbers):
    """Find maximum and minimum in list - old manual method"""
    if not numbers:
        return None, None

    max_val = numbers[0]
    min_val = numbers[0]

    for num in numbers[1:]:
        if num > max_val:
            max_val = num
        if num < min_val:
            min_val = num

    return max_val, min_val


def is_palindrome(text):
    """Check if text is palindrome - old implementation"""
    if not text:
        return False

    # Remove spaces and convert to lowercase
    cleaned = text.replace(' ', '').lower()

    # Compare with reverse
    return cleaned == cleaned[::-1]


def swap_case(text):
    """Swap case of characters - old manual method"""
    if not text:
        return ""

    result = []
    for char in text:
        if char.isupper():
            result.append(char.lower())
        elif char.islower():
            result.append(char.upper())
        else:
            result.append(char)

    return ''.join(result)


def rotate_list(lst, positions):
    """Rotate list by n positions - old implementation"""
    if not lst or positions == 0:
        return lst

    length = len(lst)
    positions = positions % length

    return lst[positions:] + lst[:positions]


# Example usage
if __name__ == "__main__":
    # Test capitalize
    print(capitalize_words("hello world"))  # Hello World

    # Test remove duplicates
    print(remove_duplicates([1, 2, 2, 3, 3, 3, 4]))  # [1, 2, 3, 4]

    # Test flatten
    print(flatten_list([1, [2, 3], [4, [5, 6]]]))  # [1, 2, 3, 4, 5, 6]

    # Test palindrome
    print(is_palindrome("racecar"))  # True
    print(is_palindrome("hello"))  # False
