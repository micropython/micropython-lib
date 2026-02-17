# Test tab completion logic used by aiorepl.
import sys
import micropython

try:
    micropython.repl_autocomplete
except AttributeError:
    print("SKIP")
    raise SystemExit

# Test the autocomplete API contract that aiorepl depends on.

# Single completion: keyword "import"
result = micropython.repl_autocomplete("impo")
print(repr(result))

# No match: returns empty string
result = micropython.repl_autocomplete("xyz_no_match_zzz")
print(repr(result))

# Multiple matches: returns None (candidates printed to stdout by C code).
# Create two globals sharing a prefix so autocomplete finds multiple matches.
import __main__

__main__.tvar_alpha = 1
__main__.tvar_beta = 2
result = micropython.repl_autocomplete("tvar_")
del __main__.tvar_alpha
del __main__.tvar_beta
print("multiple:", repr(result))

# Test the whitespace-before-cursor logic used for tab-as-indentation.
# This validates the condition: cursor_pos > 0 and cmd[cursor_pos - 1] <= " "
test_cases = [
    ("x ", True),  # space before cursor
    ("x", False),  # non-whitespace before cursor
    ("\n", True),  # newline counts as whitespace
    ("", False),  # empty line (cursor_pos == 0)
]
for cmd, expected in test_cases:
    cursor_pos = len(cmd)
    is_whitespace = cursor_pos > 0 and cmd[cursor_pos - 1] <= " "
    print(cmd.encode(), is_whitespace == expected)
