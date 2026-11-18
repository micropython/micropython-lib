# BFU UA Display

**Professional Ukrainian Text Rendering Library for MicroPython**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MicroPython](https://img.shields.io/badge/MicroPython-1.19+-blue.svg)](https://micropython.org/)
[![ESP32](https://img.shields.io/badge/Platform-ESP32-green.svg)](https://www.espressif.com/en/products/socs/esp32)

A lightweight, optimized library for rendering Ukrainian text on displays commonly used with ESP32 and MicroPython projects. Solves the problem of missing Ukrainian character support in standard display libraries.

## 🌟 Features

- ✅ **Full Ukrainian Alphabet Support** - All 33 Ukrainian letters (uppercase and lowercase)
- ✅ **Lightweight & Optimized** - Designed for ESP32 memory constraints
- ✅ **Easy to Use** - Simple, intuitive API
- ✅ **Multiple Text Functions** - Basic, centered, scaled, and right-aligned text
- ✅ **Display Agnostic** - Works with any display supporting `pixel()` method
- ✅ **5x7 Bitmap Font** - Compact and readable on small displays
- ✅ **Production Ready** - Clean, modular, professional code
- ✅ **Extensible Architecture** - Easy to add new display drivers and fonts

## 📦 Installation

### ⭐ Official Method: Using mip (Recommended)

**Note:** This package is prepared for submission to the official MicroPython package index. Once accepted, you will be able to install it directly using:

```python
import mip
mip.install("bfu_ua_display")
```

Or using mpremote from your PC:

```bash
mpremote connect COM3 mip install bfu_ua_display
```

**Status:** Pending submission to micropython-lib. Until then, use one of the alternative methods below.

---

### Alternative Method 1: Using mpremote (Most Reliable)

**mpremote** is the official MicroPython tool that works reliably across all firmware versions and avoids network/TLS issues.

#### Step 1: Install mpremote on your PC

```bash
pip install mpremote
```

#### Step 2: Download the library

```bash
git clone https://github.com/BrainFromUkraine/bfu_ua_display.git
cd bfu_ua_display
```

Or download ZIP from GitHub and extract it.

#### Step 3: Install to ESP32

**Windows:**
```bash
mpremote connect COM3 fs mkdir :/lib/bfu_ua_display
mpremote connect COM3 fs cp bfu_ua_display/__init__.py :/lib/bfu_ua_display/__init__.py
mpremote connect COM3 fs cp bfu_ua_display/font5x7.py :/lib/bfu_ua_display/font5x7.py
mpremote connect COM3 fs cp bfu_ua_display/text_engine.py :/lib/bfu_ua_display/text_engine.py
mpremote connect COM3 fs cp bfu_ua_display/utils.py :/lib/bfu_ua_display/utils.py
```

**Linux/Mac:**
```bash
mpremote connect /dev/ttyUSB0 fs mkdir :/lib/bfu_ua_display
mpremote connect /dev/ttyUSB0 fs cp bfu_ua_display/__init__.py :/lib/bfu_ua_display/__init__.py
mpremote connect /dev/ttyUSB0 fs cp bfu_ua_display/font5x7.py :/lib/bfu_ua_display/font5x7.py
mpremote connect /dev/ttyUSB0 fs cp bfu_ua_display/text_engine.py :/lib/bfu_ua_display/text_engine.py
mpremote connect /dev/ttyUSB0 fs cp bfu_ua_display/utils.py :/lib/bfu_ua_display/utils.py
```

**Note:** Replace `COM3` or `/dev/ttyUSB0` with your actual port.

### Alternative Method 1: Using Thonny IDE (Easiest for Beginners)

1. Download the library from GitHub:
   - Go to https://github.com/BrainFromUkraine/bfu_ua_display
   - Click "Code" → "Download ZIP"
   - Extract the ZIP file

2. Install using Thonny:
   - Open Thonny IDE
   - Connect your ESP32
   - View → Files
   - On your ESP32, create a `lib` folder if it doesn't exist
   - Drag the `bfu_ua_display` folder into the `lib` folder

### Alternative Method 2: GitHub mip Installation (Experimental - May Fail)

**⚠️ WARNING:** This method is **experimental** and **frequently fails** on many ESP32 MicroPython firmware versions due to HTTPS/TLS/DNS limitations. **Use mpremote or Thonny instead** for reliable installation.

If you want to try on-device installation (not recommended):

```python
import os
import mip

# Create directories
try:
    os.mkdir("/lib")
except:
    pass

try:
    os.mkdir("/lib/bfu_ua_display")
except:
    pass

# Attempt to install files (may fail with OSError: -202)
files = [
    "__init__.py",
    "font5x7.py",
    "text_engine.py",
    "utils.py"
]

base = "https://raw.githubusercontent.com/BrainFromUkraine/bfu_ua_display/main/bfu_ua_display/"

for file in files:
    print(f"Installing {file}...")
    try:
        mip.install(base + file, target="/lib/bfu_ua_display")
    except OSError as e:
        print(f"Failed: {e}")
        print("Use mpremote or Thonny installation instead!")
        break

print("✓ BFU UA Display installed successfully!")
```

**Common Failure:** `OSError: -202` when downloading from raw.githubusercontent.com means the ESP32 MicroPython firmware cannot complete HTTPS/TLS/DNS requests. This is a **firmware limitation**, not a library issue. **Use mpremote or Thonny instead.**

### Alternative Method 3: GitHub Package mip (Experimental)

```python
import mip
mip.install("github:BrainFromUkraine/bfu_ua_display")
```

**⚠️ Warning:** This method is experimental and may fail on some ESP32 firmware versions due to GitHub HTTPS/chunked transfer limitations. Use the mpremote method for reliable installation.

### Verify Installation

Test that the library is installed correctly:

```python
# Test import
from bfu_ua_display import ua_text, ua_text_center, ua_text_scaled
print("✓ BFU UA Display imported successfully!")

# Check version
import bfu_ua_display
print(f"Version: {bfu_ua_display.__version__}")
```

### Troubleshooting

**Problem:** `ImportError: no module named 'bfu_ua_display'`

**Solution:** 
1. Verify the library is in `/lib/bfu_ua_display/` on your ESP32
2. Check that the folder contains `__init__.py`
3. List files using mpremote: `mpremote connect COM3 fs ls :/lib/bfu_ua_display`
4. Try resetting your ESP32: `import machine; machine.reset()`

**Problem:** `OSError: -202` when using mip

**Solution:** This is a network/DNS error on ESP32. The on-device mip installation is failing due to TLS or network issues. Use the **mpremote method** (recommended) or **Thonny IDE method** instead.

**Problem:** `ValueError: Unsupported Transfer-Encoding: chunked`

**Solution:** This error occurs with some MicroPython firmware versions when using on-device mip. Use the **mpremote method** (recommended) or **Thonny IDE method** instead.

**Problem:** Nested folders like `bfu_ua_display/font5x7.py/font5x7.py`

**Solution:** This was caused by an older installation method. Clean up and reinstall:

```bash
# Remove incorrect installation
mpremote connect COM3 fs rm -r :/lib/bfu_ua_display

# Reinstall using mpremote method above
```

**Problem:** How do I find my COM port?

**Solution:**
- **Windows:** Check Device Manager → Ports (COM & LPT) → Look for "USB-SERIAL CH340" or similar
- **Linux:** Run `ls /dev/ttyUSB*` or `ls /dev/ttyACM*`
- **Mac:** Run `ls /dev/tty.usb*` or `ls /dev/cu.usb*`
- **Thonny:** Bottom-right corner shows the port when connected

## 🚀 Quick Start

### Basic Example

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

oled.show()
```

### Scaled Text

```python
from bfu_ua_display import ua_text_scaled

# Draw 2x scaled text
ua_text_scaled(oled, "ПРИВІТ", 10, 10, scale=2)
oled.show()
```

## 📖 API Reference

### Core Functions

#### `ua_text(display, text, x, y, color=1, bg_color=0, clear_bg=False)`

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

---

#### `ua_text_center(display, text, y, color=1, bg_color=0, clear_bg=False, display_width=128)`

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

---

#### `ua_text_scaled(display, text, x, y, scale=2, color=1, bg_color=0, clear_bg=False)`

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

---

### Utility Functions

The library also includes utility functions in `bfu_ua_display.utils`:

- `measure_text(text)` - Get text dimensions
- `wrap_text(text, max_width)` - Wrap text to fit width
- `truncate_text(text, max_width)` - Truncate with ellipsis
- `center_position(text, display_width, display_height)` - Calculate center position
- `supports_ukrainian(text)` - Check if text contains Ukrainian characters
- `validate_text(text)` - Validate character support

## 🎯 Supported Characters

### Ukrainian Alphabet

**Uppercase:** А Б В Г Ґ Д Е Є Ж З И І Ї Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я

**Lowercase:** а б в г ґ д е є ж з и і ї й к л м н о п р с т у ф х ц ч ш щ ь ю я

### Additional Characters

- English alphabet (A-Z, a-z)
- Numbers (0-9)
- Common symbols (!, @, #, $, %, etc.)
- Punctuation marks

## 🖥️ Supported Displays

Currently tested and working with:

- **SSD1306** - OLED 128x64, 128x32 (I2C/SPI)

The library is designed to work with any display that supports:
- `pixel(x, y, color)` - Set individual pixel
- `fill_rect(x, y, width, height, color)` - Fill rectangle (optional, for optimization)
- `show()` - Update display (optional, for buffered displays)

## 🔬 Tested on Real Hardware

All Ukrainian glyphs have been **manually refined and tested on real SSD1306 OLED hardware** to ensure optimal readability and visual quality.

### Hardware Testing Setup

- **Display:** SSD1306 128x64 OLED (I2C)
- **Controller:** ESP32 DevKit
- **Testing:** Full Ukrainian alphabet + scaled rendering + variable-width glyphs

### Gallery

<div align="center">

![Ukrainian Alphabet on SSD1306](assets/ukrainian-alphabet-oled.jpg)
*Complete Ukrainian alphabet displayed on real SSD1306 OLED hardware*

</div>

**Key Features Verified:**
- ✅ All 33 Ukrainian letters render correctly
- ✅ Variable-width glyph rendering works properly
- ✅ Scaled text (2x, 3x) displays clearly
- ✅ Mixed Ukrainian/English text alignment
- ✅ Proper spacing and kerning
- ✅ Readable at standard 5x7 pixel size

> **Note:** Glyphs were iteratively refined directly on hardware, not just simulated. This ensures real-world readability on actual OLED displays.

## 🎨 Demo & Screenshots

### Full Alphabet Display

The library supports the complete Ukrainian alphabet with carefully designed glyphs:

```python
# Display full Ukrainian alphabet
from bfu_ua_display import ua_text

ua_text(oled, "АБВГҐДЕЄЖЗИІЇЙКЛМН", 0, 0)
ua_text(oled, "ОПРСТУФХЦЧШЩЬЮЯ", 0, 10)
ua_text(oled, "абвгґдеєжзиіїйклмн", 0, 20)
ua_text(oled, "опрстуфхцчшщьюя", 0, 30)
oled.show()
```

### Scaled Text Example

```python
# Large 2x scaled Ukrainian text
ua_text_scaled(oled, "УКРАЇНА", 10, 10, scale=2)
oled.show()
```

## 📁 Project Structure

```
bfu_ua_display/
│
├── bfu_ua_display/
│   ├── __init__.py          # Package initialization
│   ├── font5x7.py           # 5x7 bitmap font with Ukrainian characters
│   ├── text_engine.py       # Core rendering functions
│   └── utils.py             # Utility functions
│
├── examples/
│   └── oled_i2c_example.py  # Complete usage examples
│
├── README.md                # This file
├── LICENSE                  # MIT License
├── package.json             # MicroPython package metadata
└── .gitignore              # Git ignore rules
```

## 💡 Examples

See the `examples/` folder for complete working examples:

- **oled_i2c_example.py** - Comprehensive examples including:
  - Basic text rendering
  - Centered text
  - Scaled text
  - Full alphabet display
  - Mixed Ukrainian/English content
  - Scrolling text animation
  - Multi-line text
  - Background clearing

## 🛠️ Hardware Requirements

- **ESP32** board (or compatible MicroPython device)
- **Display** (SSD1306 OLED recommended for testing)
- **I2C or SPI connection** (depending on display)

### Typical Wiring (SSD1306 I2C)

```
ESP32          SSD1306
-----          -------
GPIO 22  --->  SCL
GPIO 21  --->  SDA
3.3V     --->  VCC
GND      --->  GND
```

## 🔮 Future Roadmap

### Version 0.2.0
- ST7789 TFT display support
- GC9A01 round display support
- Additional font sizes (8x8, 10x14)

### Version 0.3.0
- ILI9341 display support
- Font scaling improvements
- Word wrapping helper

### Version 1.0.0
- UI widgets (buttons, progress bars)
- Menu system
- Notification system
- Animation helpers

## 🤝 Contributing

Contributions are welcome! This is an open-source project aimed at improving Ukrainian language support in MicroPython projects.

### How to Contribute

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on real hardware
5. Submit a pull request

### Areas for Contribution

- Additional display driver support
- New font sizes and styles
- Performance optimizations
- Documentation improvements
- Example projects
- Bug fixes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

**BFU Electronics**

- GitHub: [@BFU-Electronics](https://github.com/BFU-Electronics)

## 🙏 Acknowledgments

- MicroPython community
- Ukrainian maker community
- All contributors and testers

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/BFU-Electronics/bfu_ua_display/issues)
- **Discussions:** [GitHub Discussions](https://github.com/BFU-Electronics/bfu_ua_display/discussions)

## 🎓 Community & Tutorials

**🇺🇦 Ukrainian Educational Content:**

This library is actively used in educational YouTube lessons and tutorials about ESP32, MicroPython, and embedded systems.

**YouTube Channel:** [Brain From Ukraine](https://www.youtube.com/@BrainFromUkraine)

Watch tutorials covering:
- Getting started with BFU UA Display
- ESP32 and MicroPython projects
- Display programming
- Ukrainian language support in embedded systems
- Real-world IoT projects

##  Links

- [MicroPython Official Site](https://micropython.org/)
- [ESP32 Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/)
- [SSD1306 Driver](https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py)
- [Brain From Ukraine YouTube](https://www.youtube.com/@BrainFromUkraine)

---

**Made with ❤️ in Ukraine 🇺🇦**

*Зроблено з любов'ю в Україні*
