# ruff: noqa: RUF002
"""
BFU UA Display - Ukrainian Text Rendering Library for MicroPython
==================================================================
Бібліотека для відображення українського тексту на дисплеях MicroPython

A professional, lightweight library for rendering Ukrainian text on displays
commonly used with ESP32 and MicroPython projects.

Професійна, легка бібліотека для відображення українського тексту на дисплеях,
які зазвичай використовуються з ESP32 та MicroPython проєктами.

Features / Можливості:
- Full Ukrainian alphabet support / Повна підтримка української абетки
- Optimized for ESP32 memory constraints / Оптимізовано для обмежень пам'яті ESP32
- Clean, modular architecture / Чиста, модульна архітектура
- Easy to use API / Простий у використанні API
- Extensible for multiple display types / Розширюваний для різних типів дисплеїв

Author / Автор: BFU Electronics
License / Ліцензія: MIT
Version / Версія: 0.1.0
"""

from .text_engine import ua_text, ua_text_center, ua_text_scaled

__version__ = "0.1.0"
__author__ = "BFU Electronics"
__all__ = ["ua_text", "ua_text_center", "ua_text_scaled"]
