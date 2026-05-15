"""
BFU UA Display - Ukrainian Text Rendering Library for MicroPython
==================================================================

A professional, lightweight library for rendering Ukrainian text on displays
commonly used with ESP32 and MicroPython projects.

Features:
- Full Ukrainian alphabet support (33 letters)
- Optimized for ESP32 memory constraints
- Clean, modular architecture
- Easy to use API
- Extensible for multiple display types

Author: BFU Electronics
License: MIT
Version: 0.1.0
"""

from .text_engine import ua_text, ua_text_center, ua_text_scaled

__version__ = "0.1.0"
__author__ = "BFU Electronics"
__all__ = ["ua_text", "ua_text_center", "ua_text_scaled"]
