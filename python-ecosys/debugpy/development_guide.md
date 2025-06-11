# Debugging MicroPython debugpy with VS Code

## Method 1: Direct Connection with Enhanced Logging

1. **Start MicroPython with enhanced logging:**
   ```bash
   ~/micropython2/ports/unix/build-standard/micropython test_vscode.py
   ```
   
   This will now show detailed DAP protocol messages like:
   ```
   [DAP] RECV: request initialize (seq=1)
   [DAP]   args: {...}
   [DAP] SEND: response initialize (req_seq=1, success=True)
   ```

2. **Connect VS Code debugger:**
   - Use the launch configuration in `.vscode/launch.json`
   - Or manually attach to `127.0.0.1:5678`

3. **Look for issues in the terminal output** - you'll see all DAP message exchanges

## Method 2: Using DAP Monitor (Recommended for detailed analysis)

1. **Start MicroPython debugpy server:**
   ```bash
   ~/micropython2/ports/unix/build-standard/micropython test_vscode.py
   ```

2. **In another terminal, start the DAP monitor:**
   ```bash
   python3 dap_monitor.py
   ```
   
   The monitor listens on port 5679 and forwards to port 5678

3. **Connect VS Code to the monitor:**
   - Modify your VS Code launch config to connect to port `5679` instead of `5678`
   - Or create a new launch config:
   ```json
   {
       "name": "Debug via Monitor",
       "type": "python", 
       "request": "attach",
       "connect": {
           "host": "127.0.0.1",
           "port": 5679
       }
   }
   ```

4. **Analyze the complete DAP conversation** in the monitor terminal

## VS Code Debug Logging

Enable VS Code's built-in DAP logging:

1. **Open VS Code settings** (Ctrl+,)
2. **Search for:** `debug.console.verbosity`
3. **Set to:** `verbose`
4. **Also set:** `debug.allowBreakpointsEverywhere` to `true`

## Common Issues to Look For

1. **Missing required DAP capabilities** - check the `initialize` response
2. **Breakpoint verification failures** - look for `setBreakpoints` exchanges
3. **Thread/stack frame issues** - check `stackTrace` and `scopes` responses
4. **Evaluation problems** - monitor `evaluate` request/response pairs

## Expected DAP Sequence

A successful debug session should show this sequence:

1. `initialize` request → response with capabilities
2. `initialized` event 
3. `setBreakpoints` request → response with verified breakpoints
4. `configurationDone` request → response
5. `attach` request → response
6. When execution hits breakpoint: `stopped` event
7. `stackTrace` request → response with frames
8. `scopes` request → response with local/global scopes
9. `continue` request → response to resume

If any step fails or is missing, that's where the issue lies.