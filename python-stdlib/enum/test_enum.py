# version="1.2.1"

import unittest
from enum import Enum, EnumValue, enum


class TestEnum(unittest.TestCase):
    def setUp(self):
        # Створюємо базовий клас для тестів
        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        self.ColorClass = Color
        self.color = Color()

    def test_class_attributes(self):
        """Тест статичних атрибутів, визначених у класі"""
        self.assertEqual(self.color.RED.value, 1)
        self.assertEqual(self.color.RED.name, 'RED')
        self.assertIsInstance(self.color.RED, EnumValue)

    def test_init_kwargs(self):
        """Тест додавання значень через конструктор __init__(**kwargs)"""
        c = self.ColorClass(YELLOW=4, BLACK=0)
        self.assertEqual(c.YELLOW.value, 4)
        self.assertEqual(c.BLACK.name, 'BLACK')

    def test_append(self):
        """Тест методу append(**kwargs) та ланцюжкового виклику"""
        self.color.append(MAGENTA=5).append(CYAN=6)
        self.assertEqual(self.color.MAGENTA.value, 5)
        self.assertEqual(self.color.CYAN.name, 'CYAN')

    def test_comparison(self):
        """Тест порівняння EnumValue з числами та іншими об'єктами"""
        self.assertTrue(self.color.RED == 1)
        self.assertFalse(self.color.RED == 2)
        self.assertEqual(self.color.RED, self.color.RED)
        # Перевірка, що об'єкт не дорівнює значенню іншого типу
        self.assertFalse(self.color.RED == "1")

    def test_call_reverse_lookup(self):
        """Тест зворотного пошуку Color(1) -> RED"""
        # У вашій реалізації __call__ повертає об'єкт EnumValue
        result = self.color(1)
        self.assertEqual(result.name, 'RED')
        self.assertEqual(result.value, 1)

        # Перевірка виключення для неіснуючого значення
        with self.assertRaises(ValueError):
            self.color(999)

    def test_is_value(self):
        """Тест методу перевірки наявності значення is_value()"""
        self.assertTrue(self.color.is_value(1))
        self.assertTrue(self.color.is_value(3))
        self.assertFalse(self.color.is_value(5))

    def test_iteration(self):
        """Тест ітерабельності Enum (магічний метод __iter__)"""
        # Створюємо список імен через ітерацію
        members = list(self.color)
        names = [m.name for m in members]

        self.assertIn('RED', names)
        self.assertIn('GREEN', names)
        self.assertIn('BLUE', names)
        self.assertEqual(len(members), 3)

    def test_enum_value_immutability(self):
        """Тест захисту від зміни значень EnumValue"""
        with self.assertRaises(AttributeError):
            self.color.RED.value = 10

        with self.assertRaises(AttributeError):
            self.color.RED.name = "NEW_NAME"

    def test_len(self):
        """Тест магічного методу __len__"""
        self.assertEqual(len(self.color), 3)
        self.color.append(WHITE=7)
        self.assertEqual(len(self.color), 4)

    def test_backwards_compatible_function(self):
        """Тест глобальної функції enum(**kwargs)"""
        e = enum(A=10, B=20)
        self.assertEqual(e.A.value, 10)
        self.assertEqual(e.B.name, 'B')

    def test_call_method(self):
        """Тест виклику об'єкта як функції c.RED() -> 1"""
        self.assertEqual(self.color.RED(), 1)
        self.assertEqual(self.color.GREEN(), 2)


if __name__ == '__main__':
    unittest.main()
