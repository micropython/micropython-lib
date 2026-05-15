# BFU UA Display

Ukrainian text rendering library for MicroPython displays.

## Description

A lightweight library for rendering Ukrainian text on displays commonly used with ESP32 and MicroPython projects. Standard MicroPython display libraries do not include Ukrainian characters (А, Б, В, Г, Ґ, Д, Е, Є, Ж, З, И, І, Ї, Й, etc.), making it impossible to display Ukrainian text properly. This library solves that problem with a custom 5x7 bitmap font containing all 33 Ukrainian letters (uppercase and lowercase).

## Features

- **Full Ukrainian Alphabet Support** - All 33 Ukrainian letters (uppercase and lowercase)
- **Lightweight** - Optimized for ESP32 memory constraints (~2-3 KB)
- **Display Agnostic** - Works with any display supporting `pixel()` method
- **Simple API** - Three main functions for text rendering
- **5x7 Bitmap Font** - Compact and readable on small displays

## Installation

```python
import mip
mip.install("bfu_ua_display")
```

Or using mpremote:

```bash
mpremote connect COM3 mip install bfu_ua_display
```

## Quick Start

```python
from machine import I2C, Pin
from ssd1306 import SSD1306_I2C
from bfu_ua_display import ua_text, ua_text_center

# Initialize display
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = SSD1306_I2C(128, 64, i2c)

# Draw Ukrainian text
ua_text(oled, "ПРИВІТ УКРАЇНО!", 0, 0)
ua_text_center(oled, "BFU Electronics", 28)

# Update display
oled.show()
```

## API Reference

### ua_text(display, text, x, y, color=1, bg_color=0, clear_bg=False)

Render text at specified position with Ukrainian character support.

**Parameters:**
- `display` - Display object with `pixel()` method
- `text` - String to render (Ukrainian, English, numbers, symbols)
- `x` - X coordinate (left edge)
- `y` - Y coordinate (top edge)
- `color` - Foreground color (default: 1)
- `bg_color` - Background color (default: 0)
- `clear_bg` - Clear background behind text (default: False)

**Returns:** Total width of rendered text in pixels

**Example:**
```python
ua_text(oled, "Температура: 25°C", 0, 0)
```

---

### ua_text_center(display, text, y, color=1, bg_color=0, clear_bg=False, display_width=128)

Render text centered horizontally on the display.

**Parameters:**
- `display` - Display object
- `text` - String to render
- `y` - Y coordinate (top edge)
- `color` - Foreground color (default: 1)
- `bg_color` - Background color (default: 0)
- `clear_bg` - Clear background (default: False)
- `display_width` - Display width in pixels (default: 128)

**Returns:** X coordinate where text was rendered

**Example:**
```python
ua_text_center(oled, "УКРАЇНА", 28)
```

---

### ua_text_scaled(display, text, x, y, scale=2, color=1, bg_color=0, clear_bg=False)

Render text with scaling (2x, 3x, etc.).

**Parameters:**
- `display` - Display object
- `text` - String to render
- `x` - X coordinate (left edge)
- `y` - Y coordinate (top edge)
- `scale` - Scaling factor (1=normal, 2=double, etc.)
- `color` - Foreground color (default: 1)
- `bg_color` - Background color (default: 0)
- `clear_bg` - Clear background (default: False)

**Returns:** Total width of rendered text in pixels

**Example:**
```python
ua_text_scaled(oled, "ПРИВІТ", 0, 0, scale=2)
```

## Supported Characters

- **Ukrainian Alphabet**: А Б В Г Ґ Д Е Є Ж З И І Ї Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я (uppercase and lowercase)
- **English Alphabet**: A-Z, a-z
- **Numbers**: 0-9
- **Symbols**: Common punctuation and special characters

## Display Requirements

The library works with any display object that implements:

- `pixel(x, y, color)` - Set individual pixel (required)
- `show()` - Update display (optional, for buffered displays)
- `fill_rect(x, y, width, height, color)` - Fill rectangle (optional, for optimization)

## Compatibility

**Tested with:**
- ESP32 with MicroPython v1.19+
- SSD1306 OLED displays (128x64, 128x32) via I2C/SPI

**Compatible with:**
- Any MicroPython-compatible board
- Any display supporting the `pixel()` method

## Examples

### Multi-line Text

```python
oled.fill(0)
ua_text(oled, "Рядок 1", 0, 0)
ua_text(oled, "Рядок 2", 0, 10)
ua_text(oled, "Рядок 3", 0, 20)
oled.show()
```

### Scaled Text

```python
oled.fill(0)
ua_text_scaled(oled, "ВЕЛИКИЙ", 0, 0, scale=2)
oled.show()
```

### Centered Text

```python
oled.fill(0)
ua_text_center(oled, "УКРАЇНА", 10)
ua_text_center(oled, "2026", 28)
oled.show()
```

## License

MIT License

## Documentation

For complete documentation, examples, and troubleshooting, visit:

**https://github.com/BrainFromUkraine/bfu_ua_display**

## Author

BFU Electronics
