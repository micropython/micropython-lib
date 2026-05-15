"""
Text Rendering Engine for Ukrainian Display Library
====================================================

Core rendering functions for drawing text on displays.
Optimized for MicroPython and ESP32 memory constraints.

The engine is designed to work with any display object that supports:
- pixel(x, y, color) - Set individual pixel
- fill_rect(x, y, width, height, color) - Fill rectangle (optional, for optimization)
- show() - Update display (optional, for buffered displays)
"""

from . import font5x7


def ua_text(display, text, x, y, color=1, bg_color=0, clear_bg=False):
    """
    Render text at specified position with Ukrainian character support.

    This is the core rendering function that draws text pixel-by-pixel
    using the bitmap font data.

    Args:
        display: Display object with pixel() method
        text: String to render (supports English, numbers, symbols, Ukrainian)
        x: X coordinate (left edge)
        y: Y coordinate (top edge)
        color: Foreground color (default: 1 for white/on)
        bg_color: Background color (default: 0 for black/off)
        clear_bg: If True, clear background behind text (default: False)

    Returns:
        int: Total width of rendered text in pixels

    Example:
        >>> from machine import I2C, Pin
        >>> from ssd1306 import SSD1306_I2C
        >>> from bfu_ua_display import ua_text
        >>>
        >>> i2c = I2C(0, scl=Pin(22), sda=Pin(21))
        >>> oled = SSD1306_I2C(128, 64, i2c)
        >>>
        >>> ua_text(oled, "ПРИВІТ", 0, 0)
        >>> oled.show()
    """
    if not text:
        return 0

    cursor_x = x
    total_width = 0

    for char in text:
        bitmap = font5x7.get_char_bitmap(char)

        if bitmap is None:
            # Character not found, skip it
            continue

        # Clear background if requested
        if clear_bg and hasattr(display, "fill_rect"):
            display.fill_rect(cursor_x, y, font5x7.FONT_WIDTH, font5x7.FONT_HEIGHT, bg_color)

        # Render character bitmap
        for col in range(font5x7.FONT_WIDTH):
            column_data = bitmap[col]
            for row in range(font5x7.FONT_HEIGHT):
                # Check if pixel should be set (bit is 1)
                if column_data & (1 << row):
                    display.pixel(cursor_x + col, y + row, color)
                elif clear_bg:
                    # Clear pixel if background clearing is enabled
                    display.pixel(cursor_x + col, y + row, bg_color)

        # Move cursor to next character position (with 1px spacing)
        cursor_x += font5x7.FONT_WIDTH + 1
        total_width += font5x7.FONT_WIDTH + 1

    # Remove trailing spacing from total width
    if total_width > 0:
        total_width -= 1

    return total_width


def ua_text_center(display, text, y, color=1, bg_color=0, clear_bg=False, display_width=128):
    """
    Render text centered horizontally on the display.

    Calculates the text width and centers it automatically.

    Args:
        display: Display object with pixel() method
        text: String to render
        y: Y coordinate (top edge)
        color: Foreground color (default: 1)
        bg_color: Background color (default: 0)
        clear_bg: If True, clear background behind text (default: False)
        display_width: Display width in pixels (default: 128 for SSD1306)

    Returns:
        int: X coordinate where text was rendered

    Example:
        >>> ua_text_center(oled, "УКРАЇНА", 28)
        >>> oled.show()
    """
    text_w = font5x7.text_width(text)
    x = (display_width - text_w) // 2

    # Ensure x is not negative
    x = max(x, 0)

    ua_text(display, text, x, y, color, bg_color, clear_bg)
    return x


def ua_text_scaled(display, text, x, y, scale=2, color=1, bg_color=0, clear_bg=False):
    """
    Render text with scaling (2x, 3x, etc.).

    Each pixel in the original font is rendered as a scale x scale block.
    Note: This is memory-intensive for large scale values.

    Args:
        display: Display object with pixel() or fill_rect() method
        text: String to render
        x: X coordinate (left edge)
        y: Y coordinate (top edge)
        scale: Scaling factor (1=normal, 2=double size, etc.)
        color: Foreground color (default: 1)
        bg_color: Background color (default: 0)
        clear_bg: If True, clear background behind text (default: False)

    Returns:
        int: Total width of rendered text in pixels

    Example:
        >>> ua_text_scaled(oled, "ПРИВІТ", 0, 0, scale=2)
        >>> oled.show()
    """
    if not text or scale < 1:
        return 0

    # For scale=1, use regular rendering for efficiency
    if scale == 1:
        return ua_text(display, text, x, y, color, bg_color, clear_bg)

    cursor_x = x
    total_width = 0
    scaled_width = font5x7.FONT_WIDTH * scale
    scaled_height = font5x7.FONT_HEIGHT * scale
    spacing = scale  # Scaled spacing between characters

    # Check if display supports fill_rect for optimization
    has_fill_rect = hasattr(display, "fill_rect")

    for char in text:
        bitmap = font5x7.get_char_bitmap(char)

        if bitmap is None:
            continue

        # Clear background if requested
        if clear_bg and has_fill_rect:
            display.fill_rect(cursor_x, y, scaled_width, scaled_height, bg_color)

        # Render scaled character
        for col in range(font5x7.FONT_WIDTH):
            column_data = bitmap[col]
            for row in range(font5x7.FONT_HEIGHT):
                pixel_on = column_data & (1 << row)

                # Draw scaled pixel as a block
                if pixel_on or clear_bg:
                    pixel_color = color if pixel_on else bg_color

                    if has_fill_rect:
                        # Use fill_rect for efficiency
                        display.fill_rect(
                            cursor_x + col * scale, y + row * scale, scale, scale, pixel_color
                        )
                    else:
                        # Fall back to individual pixels
                        for sx in range(scale):
                            for sy in range(scale):
                                display.pixel(
                                    cursor_x + col * scale + sx, y + row * scale + sy, pixel_color
                                )

        # Move cursor
        cursor_x += scaled_width + spacing
        total_width += scaled_width + spacing

    # Remove trailing spacing
    if total_width > 0:
        total_width -= spacing

    return total_width


def ua_text_right(display, text, x, y, color=1, bg_color=0, clear_bg=False):
    """
    Render text right-aligned at specified position.

    The x coordinate represents the right edge of the text.

    Args:
        display: Display object with pixel() method
        text: String to render
        x: X coordinate (right edge)
        y: Y coordinate (top edge)
        color: Foreground color (default: 1)
        bg_color: Background color (default: 0)
        clear_bg: If True, clear background behind text (default: False)

    Returns:
        int: X coordinate where text starts (left edge)

    Example:
        >>> ua_text_right(oled, "100%", 127, 0)
        >>> oled.show()
    """
    text_w = font5x7.text_width(text)
    start_x = x - text_w

    # Ensure start_x is not negative
    start_x = max(start_x, 0)

    ua_text(display, text, start_x, y, color, bg_color, clear_bg)
    return start_x


def clear_text_area(display, x, y, width, height, color=0):
    """
    Clear a rectangular area on the display.

    Useful for clearing text before redrawing.

    Args:
        display: Display object
        x: X coordinate (left edge)
        y: Y coordinate (top edge)
        width: Width in pixels
        height: Height in pixels
        color: Fill color (default: 0 for black)

    Example:
        >>> # Clear area before updating text
        >>> clear_text_area(oled, 0, 0, 128, 8)
        >>> ua_text(oled, "Updated", 0, 0)
        >>> oled.show()
    """
    if hasattr(display, "fill_rect"):
        display.fill_rect(x, y, width, height, color)
    else:
        # Fall back to pixel-by-pixel clearing
        for px in range(x, x + width):
            for py in range(y, y + height):
                display.pixel(px, py, color)
