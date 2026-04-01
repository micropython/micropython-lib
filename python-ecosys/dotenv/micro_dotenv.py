"""
MicroPython-dotenv
A lightweight .env file loader for MicroPython
~1KB, zero dependencies, memory efficient

Compatible with ESP32, ESP8266, RP2040, and other MicroPython boards.

Author: Wesley Fernandes (community contributions welcome)
License: MIT
Repository: https://github.com/holdrulff/micropython-dotenv
"""

__version__ = "1.0.0"
__all__ = ["get_env", "load_dotenv"]

# MicroPython doesn't have os.environ, create our own
_environ = {}


def load_dotenv(path=".env"):
    """
    Load .env file into environment. Returns dict.

    Args:
        path (str): Path to .env file. Default: '.env'

    Returns:
        dict: Dictionary of loaded variables (_environ)

    Example:
        >>> from dotenv import load_dotenv, get_env
        >>> env = load_dotenv('.env')
        >>> wifi_ssid = get_env('WIFI_SSID')
    """
    global _environ
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip()
                    # Remove quotes
                    if len(v) >= 2 and ((v[0] == '"' == v[-1]) or (v[0] == "'" == v[-1])):
                        v = v[1:-1]
                    _environ[k] = v
    except Exception as e:
        print("Warning: Could not load .env file:", e)
    return _environ


def get_env(key, default=None):
    """
    Get environment variable with default.

    Args:
        key (str): Environment variable name
        default: Default value if not found. Default: None

    Returns:
        Value of environment variable or default

    Example:
        >>> wifi_ssid = get_env('WIFI_SSID', 'default_network')
    """
    return _environ.get(key, default)
