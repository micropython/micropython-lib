# unittest-expectedfailure

An optional add-on for the MicroPython [`unittest`](../unittest) package that
adds CPython-compatible tracking of **expected failures** and **unexpected
successes**.

## Background

The base `unittest` package is intentionally small. Its
`@unittest.expectedFailure` decorator swallows a failing test and raises
`AssertionError` on an unexpected pass, but it does not track those two cases as
separate result categories the way CPython does.

This package layers that behaviour on top of the base package without modifying
it, in the same "overlay" style as `unittest-discover`: installing it adds a
single module, `unittest/expectedfailure.py`, next to the base
`unittest/__init__.py`, and importing that module patches `unittest` at runtime.

## What it adds

Once activated, results are reported like CPython:

| Case                       | Counter                 | `wasSuccessful()` | Runner summary                   |
| -------------------------- | ----------------------- | ----------------- | -------------------------------- |
| Decorated test that fails  | `expectedFailuresNum`   | stays `True`      | `OK (expected failures=N)`       |
| Decorated test that passes | `unexpectedSuccessesNum`| becomes `False`   | `FAILED (unexpected successes=N)`|

Matching CPython, an unexpected success is **not** counted as a failure or
error — it has its own counter — but it still makes the overall run
unsuccessful.

`TestResult` gains `expectedFailuresNum` and `unexpectedSuccessesNum` counters,
aggregated across modules by `TestResult.__add__` (as used by
`unittest-discover`). They are class-level defaults, so a `TestResult` allocates
no extra memory until a test is actually recorded.

## Installation

Using `mip`:

```
mip install unittest-expectedfailure
```

or add `require("unittest-expectedfailure")` to your `manifest.py`. It pulls in
`unittest` automatically.

## Usage

Activate the add-on by importing it once, before your tests run, then use the
decorator through the `unittest` namespace:

```python
import unittest
import unittest.expectedfailure  # activates the add-on (import for its side effect)


class MyTests(unittest.TestCase):
    @unittest.expectedFailure
    def test_known_bug(self):
        self.assertEqual(buggy(), 42)  # currently fails; that's expected


if __name__ == "__main__":
    unittest.main()
```

Notes:

- Reference the decorator as `@unittest.expectedFailure` (looked up at call
  time) and make sure `import unittest.expectedfailure` runs first. Binding the
  name early with `from unittest import expectedFailure` would capture the
  un-patched decorator.
- The module is safe to import more than once (for example under
  `unittest-discover`, which re-imports test modules); it patches the base
  package only once.
- Like the base package since its size optimisation, this module avoids `assert`
  so it keeps working when compiled with `-O3`.

## `unittest-discover` exit code

`unittest-discover` (>= 0.1.4) includes unexpected successes in its process exit
code, so `micropython -m unittest` returns non-zero when a decorated test
unexpectedly passes — even though such a test is tracked separately and is not
counted as a `failure`. Older versions considered only `failuresNum + errorsNum`
and would exit `0` for an unexpected-success-only run.
