# VSCode Debugging Guide for uv Application

## Setup Complete! 🎉

Your VSCode debugging configuration has been set up for your uv application. Here's how to use it:

## Available Debug Configurations

### 1. **Debug Azure MCP Agent**
- **What it does**: Runs the Azure MCP agent server
- **How to use**: 
  1. Set breakpoints in `src/platform_eng_a2a_demo/azure_mcp/azure_agent.py`
  2. Press `F5` or go to Run → Start Debugging
  3. Select "Debug Azure MCP Agent"
- **Server**: Runs on `localhost:10001`

### 2. **Debug Planner Agent**
- **What it does**: Runs the planner agent server
- **How to use**: 
  1. Set breakpoints in `src/platform_eng_a2a_demo/planner/`
  2. Press `F5` and select "Debug Planner Agent"
- **Server**: Runs on `localhost:10002`

### 3. **Debug Currency Exchange Demo**
- **What it does**: Runs the currency exchange demo
- **How to use**: 
  1. Set breakpoints in `src/currency_exchange_demo/`
  2. Press `F5` and select "Debug Currency Exchange Demo"

### 4. **Debug Azure MCP Agent (uv run)**
- **What it does**: Uses `uv run` to execute the Azure MCP agent
- **How to use**: 
  1. Set breakpoints
  2. Press `F5` and select "Debug Azure MCP Agent (uv run)"
- **Advantage**: Uses uv's dependency management directly

### 5. **Debug Current File**
- **What it does**: Debugs whatever file you currently have open
- **How to use**: 
  1. Open any Python file
  2. Set breakpoints
  3. Press `F5` and select "Debug Current File"

## How to Debug

### Setting Breakpoints
1. Open any Python file in your project
2. Click in the left margin next to line numbers to set breakpoints
3. Red dots will appear indicating breakpoints

### Starting Debug Session
1. **Method 1**: Press `F5` and select your debug configuration
2. **Method 2**: Go to Run → Start Debugging
3. **Method 3**: Use the Run and Debug panel (Ctrl+Shift+D)

### Debug Controls
- **Continue (F5)**: Continue execution until next breakpoint
- **Step Over (F10)**: Execute current line and move to next
- **Step Into (F11)**: Step into function calls
- **Step Out (Shift+F11)**: Step out of current function
- **Restart (Ctrl+Shift+F5)**: Restart debugging session
- **Stop (Shift+F5)**: Stop debugging

### Debug Variables
- **Variables panel**: View local and global variables
- **Watch panel**: Add specific variables to watch
- **Call Stack**: See the function call hierarchy
- **Breakpoints**: Manage all breakpoints

## Environment Configuration

The debugger is configured to:
- ✅ Use your uv virtual environment (`.venv/bin/python`)
- ✅ Set `PYTHONPATH` to include your `src/` directory
- ✅ Run in the integrated terminal
- ✅ Include external library code in debugging (`justMyCode: false`)

## Troubleshooting

### If debugging doesn't work:
1. **Check Python interpreter**: Make sure VSCode is using `.venv/bin/python`
2. **Reload VSCode**: Sometimes needed after configuration changes
3. **Check PYTHONPATH**: Ensure `src/` is in your Python path
4. **Verify uv environment**: Run `uv run python --version` to test

### Common Issues:
- **Import errors**: Make sure `PYTHONPATH` includes `src/`
- **Module not found**: Check that you're running the correct module
- **Breakpoints not hitting**: Ensure you're using the right debug configuration

## Quick Test

To test your debugging setup:

1. Open `src/platform_eng_a2a_demo/azure_mcp/azure_agent.py`
2. Set a breakpoint on line 40 (in the `__init__` method)
3. Press `F5` and select "Debug Azure MCP Agent"
4. The debugger should stop at your breakpoint

## Tips

- **Use the Debug Console**: Execute Python code during debugging
- **Conditional Breakpoints**: Right-click breakpoints to add conditions
- **Logpoints**: Add logging without code changes
- **Hot Reload**: Some configurations support hot reloading

Happy Debugging! 🐛✨ 