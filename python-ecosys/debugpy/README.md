# MicroPython debugpy

A minimal implementation of debugpy for MicroPython, enabling remote debugging
such as VS Code debugging support.

## Features

- Debug Adapter Protocol (DAP) support for VS Code integration
- Basic debugging operations:
  - Breakpoints
  - Step over/into/out
  - Stack trace inspection
  - Variable inspection (globals, locals generally not supported)
  - Expression evaluation
  - Pause/continue execution

## Requirements

- MicroPython with `sys.settrace` support (enabled with `MICROPY_PY_SYS_SETTRACE`)
- Socket support for network communication
- JSON support for DAP message parsing

## Usage

### Basic Usage

```python
import debugpy

# Start listening for debugger connections
host, port = debugpy.listen()  # Default: 127.0.0.1:5678
print(f"Debugger listening on {host}:{port}")

# Enable debugging for current thread
debugpy.debug_this_thread()

# Your code here...
def my_function():
    x = 10
    y = 20
    result = x + y  # Set breakpoint here in VS Code
    return result

result = my_function()
print(f"Result: {result}")

# Manual breakpoint
debugpy.breakpoint()
```

### VS Code Configuration

Create a `.vscode/launch.json` file in your project:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Attach to MicroPython",
            "type": "python",
            "request": "attach",
            "connect": {
                "host": "127.0.0.1",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "."
                }
            ],
            "justMyCode": false
        }
    ]
}
```

### Testing

1. Build the MicroPython Unix coverage port:
   ```bash
   cd ports/unix
   make CFLAGS_EXTRA="-DMICROPY_PY_SYS_SETTRACE=1"
   ```

2. Run the test script:
   ```bash
   cd lib/micropython-lib/python-ecosys/debugpy
   ../../../../ports/unix/build-coverage/micropython test_debugpy.py
   ```

3. In VS Code, open the debugpy folder and press F5 to attach the debugger

4. Set breakpoints in the test script and observe debugging functionality

## API Reference

### `debugpy.listen(port=5678, host="127.0.0.1")`

Start listening for debugger connections.

**Parameters:**
- `port`: Port number to listen on (default: 5678)
- `host`: Host address to bind to (default: "127.0.0.1")

**Returns:** Tuple of (host, port) actually used

### `debugpy.debug_this_thread()`

Enable debugging for the current thread by installing the trace function.

### `debugpy.breakpoint()`

Trigger a manual breakpoint that will pause execution if a debugger is attached.

### `debugpy.wait_for_client()`

Wait for the debugger client to connect and initialize.

### `debugpy.is_client_connected()`

Check if a debugger client is currently connected.

**Returns:** Boolean indicating connection status

### `debugpy.disconnect()`

Disconnect from the debugger client and clean up resources.

## Architecture

The implementation consists of several key components:

1. **Public API** (`public_api.py`): Main entry points for users
2. **Debug Session** (`server/debug_session.py`): Handles DAP protocol communication
3. **PDB Adapter** (`server/pdb_adapter.py`): Bridges DAP and MicroPython's trace system
4. **Messaging** (`common/messaging.py`): JSON message handling for DAP
5. **Constants** (`common/constants.py`): DAP protocol constants

## Limitations

This is a minimal implementation with the following limitations:

- Single-threaded debugging only
- No conditional breakpoints
- No function breakpoints
- Limited variable inspection (no nested object expansion)
- No step back functionality
- No hot code reloading
- Simplified stepping implementation

## Compatibility

Tested with:
- MicroPython Unix port
- VS Code with Python/debugpy extension
- CPython 3.x (for comparison)

## Contributing

This implementation provides a foundation for MicroPython debugging. Contributions are welcome to add:

- Conditional breakpoint support
- Better variable inspection
- Multi-threading support
- Performance optimizations
- Additional DAP features

## License

MIT License - see the MicroPython project license for details.
