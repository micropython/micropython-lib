"""
Utility Functions for BFU UA Display Library
=============================================

Helper functions for text measurement, display detection, and common operations.
"""

from . import font5x7


def measure_text(text):
    """
    Measure the dimensions of a text string.

    Args:
        text: String to measure

    Returns:
        tuple: (width, height) in pixels

    Example:
        >>> width, height = measure_text("ПРИВІТ")
        >>> print(f"Text size: {width}x{height}")
    """
    width = font5x7.text_width(text)
    height = font5x7.FONT_HEIGHT
    return (width, height)


def measure_text_scaled(text, scale=2):
    """
    Measure the dimensions of scaled text.

    Args:
        text: String to measure
        scale: Scaling factor

    Returns:
        tuple: (width, height) in pixels

    Example:
        >>> width, height = measure_text_scaled("ПРИВІТ", scale=2)
    """
    base_width = font5x7.text_width(text)
    width = base_width * scale + (len(text) - 1) * scale if text else 0
    height = font5x7.FONT_HEIGHT * scale
    return (width, height)


def wrap_text(text, max_width, char_spacing=1):
    """
    Wrap text to fit within a maximum width.

    Breaks text into lines that fit within the specified width.
    Tries to break at spaces when possible.

    Args:
        text: String to wrap
        max_width: Maximum width in pixels
        char_spacing: Spacing between characters (default: 1)

    Returns:
        list: List of text lines

    Example:
        >>> lines = wrap_text("ПРИВІТ УКРАЇНО", 40)
        >>> for i, line in enumerate(lines):
        >>>     ua_text(oled, line, 0, i * 8)
    """
    if not text:
        return []

    lines = []
    words = text.split(" ")
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        test_width = len(test_line) * (font5x7.FONT_WIDTH + char_spacing)

        if test_width <= max_width:
            current_line = test_line
        else:
            # Current line is full, start new line
            if current_line:
                lines.append(current_line)

            # Check if single word is too long
            word_width = len(word) * (font5x7.FONT_WIDTH + char_spacing)
            if word_width > max_width:
                # Break word into chunks
                chars_per_line = max_width // (font5x7.FONT_WIDTH + char_spacing)
                for i in range(0, len(word), chars_per_line):
                    lines.append(word[i : i + chars_per_line])
                current_line = ""
            else:
                current_line = word

    # Add remaining text
    if current_line:
        lines.append(current_line)

    return lines


def truncate_text(text, max_width, suffix="..."):
    """
    Truncate text to fit within maximum width, adding suffix if truncated.

    Args:
        text: String to truncate
        max_width: Maximum width in pixels
        suffix: String to append if truncated (default: "...")

    Returns:
        str: Truncated text

    Example:
        >>> short = truncate_text("VERY LONG TEXT", 50)
        >>> ua_text(oled, short, 0, 0)
    """
    if not text:
        return ""

    text_w = font5x7.text_width(text)
    if text_w <= max_width:
        return text

    suffix_w = font5x7.text_width(suffix)
    available_width = max_width - suffix_w

    if available_width <= 0:
        return suffix[: max_width // (font5x7.FONT_WIDTH + 1)]

    # Binary search for optimal length
    left, right = 0, len(text)
    result = ""

    while left <= right:
        mid = (left + right) // 2
        test_text = text[:mid]
        test_width = font5x7.text_width(test_text)

        if test_width <= available_width:
            result = test_text
            left = mid + 1
        else:
            right = mid - 1

    return result + suffix


def get_display_info(display):
    """
    Get information about the display object.

    Attempts to detect display type and capabilities.

    Args:
        display: Display object

    Returns:
        dict: Display information

    Example:
        >>> info = get_display_info(oled)
        >>> print(f"Display: {info['type']}, Size: {info['width']}x{info['height']}")
    """
    info = {
        "type": "unknown",
        "width": 128,  # Default assumption
        "height": 64,  # Default assumption
        "has_pixel": hasattr(display, "pixel"),
        "has_fill_rect": hasattr(display, "fill_rect"),
        "has_show": hasattr(display, "show"),
        "has_fill": hasattr(display, "fill"),
    }

    # Try to detect display type from class name
    class_name = type(display).__name__
    info["class"] = class_name

    if "SSD1306" in class_name:
        info["type"] = "SSD1306"
    elif "ST7789" in class_name:
        info["type"] = "ST7789"
        info["width"] = 240
        info["height"] = 240
    elif "ILI9341" in class_name:
        info["type"] = "ILI9341"
        info["width"] = 320
        info["height"] = 240
    elif "GC9A01" in class_name:
        info["type"] = "GC9A01"
        info["width"] = 240
        info["height"] = 240

    # Try to get actual dimensions
    if hasattr(display, "width"):
        info["width"] = display.width
    if hasattr(display, "height"):
        info["height"] = display.height

    return info


def center_position(text, display_width=128, display_height=64, scale=1):
    """
    Calculate position to center text both horizontally and vertically.

    Args:
        text: String to center
        display_width: Display width in pixels (default: 128)
        display_height: Display height in pixels (default: 64)
        scale: Text scale factor (default: 1)

    Returns:
        tuple: (x, y) coordinates for centered text

    Example:
        >>> x, y = center_position("ПРИВІТ", 128, 64)
        >>> ua_text(oled, "ПРИВІТ", x, y)
    """
    if scale == 1:
        text_w, text_h = measure_text(text)
    else:
        text_w, text_h = measure_text_scaled(text, scale)

    x = (display_width - text_w) // 2
    y = (display_height - text_h) // 2

    # Ensure coordinates are not negative
    x = max(0, x)
    y = max(0, y)

    return (x, y)


def supports_ukrainian(text):
    """
    Check if text contains Ukrainian characters.

    Args:
        text: String to check

    Returns:
        bool: True if text contains Ukrainian characters

    Example:
        >>> if supports_ukrainian("ПРИВІТ"):
        >>>     print("Ukrainian text detected")
    """
    ukrainian_chars = set("АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯабвгґдеєжзиіїйклмнопрстуфхцчшщьюя")
    return any(char in ukrainian_chars for char in text)


def validate_text(text):
    """
    Validate if all characters in text are supported by the font.

    Args:
        text: String to validate

    Returns:
        tuple: (is_valid, unsupported_chars)

    Example:
        >>> valid, unsupported = validate_text("ПРИВІТ 123")
        >>> if not valid:
        >>>     print(f"Unsupported characters: {unsupported}")
    """
    unsupported = []
    for char in text:
        if font5x7.get_char_bitmap(char) is None:
            if char not in unsupported:
                unsupported.append(char)

    return (len(unsupported) == 0, unsupported)
