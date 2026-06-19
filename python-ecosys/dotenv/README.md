# dotenv

Lightweight .env file loader for MicroPython.

## Installation

```python
import mip
mip.install("dotenv")\
```

## Usage

```
from dotenv import load_dotenv, get_env

load_dotenv('.env')
wifi_ssid = get_env('WIFI_SSID')
```
Full documentation: https://github.com/Holdrulff/micropython-dotenv
