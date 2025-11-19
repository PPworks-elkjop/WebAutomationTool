# xterm.js SSH Terminal Integration

## Overview
This module replaces the basic Tkinter Text widget SSH terminal with a professional xterm.js-based terminal that provides full terminal emulation, ANSI colors, proper cursor control, and better user experience.

## Architecture

### Components

1. **ssh_terminal_server.py** - Flask-SocketIO backend
   - Manages SSH connections via Paramiko
   - Bridges WebSocket to SSH I/O
   - Handles multiple simultaneous sessions
   - Auto-detects service mode and runs status command
   - Parses and reports Java Version

2. **templates/ssh_terminal.html** - xterm.js frontend
   - Full terminal emulation (VT100/xterm)
   - ANSI color support
   - Copy/paste with Ctrl+C/V
   - Search with Ctrl+F
   - Responsive terminal sizing
   - Professional terminal themes

3. **xterm_integration.py** - Tkinter integration layer
   - Embeds xterm.js via pywebview
   - Provides API for Tkinter to control terminal
   - Manages quick command buttons
   - Handles connection lifecycle

4. **dashboard_components/content_panel.py** - Updated to use xterm.js
   - Simplified SSH terminal display
   - Delegates to XTermSSHPanel

## Installation

### 1. Install Python dependencies:
```bash
pip install -r xterm_requirements.txt
```

Required packages:
- flask==3.0.0 (Web framework)
- flask-socketio==5.3.5 (WebSocket support)
- flask-cors==4.0.0 (Cross-origin requests)
- pywebview==4.4.1 (Embed browser in Tkinter)
- python-socketio==5.10.0 (Socket.IO client)
- eventlet==0.35.1 (Async networking)

### 2. Verify existing dependencies:
- paramiko (already installed for SSH)
- tkinter (comes with Python)

## Features

### Terminal Emulation
✅ Full xterm/VT100 emulation
✅ ANSI color support (256 colors)
✅ Proper cursor control
✅ Scrollback buffer
✅ Mouse support

### User Experience
✅ Copy/paste (Ctrl+C/V)
✅ Search (Ctrl+F)
✅ Clickable links
✅ Professional themes
✅ Responsive sizing

### Automation
✅ Auto-detect Service Mode
✅ Auto-run status command
✅ Parse Java Version
✅ Quick command buttons
✅ Command sequences (exit service mode)

### Quick Commands
- **Exit Service**: Runs full sequence (extended matex2010 → enableshell true → exit → exit)
- **Start Service**: Enters service mode
- **Check DNS**: Shows DNS configuration
- **Disk Space**: Shows filesystem usage
- **List Logs**: Lists log files
- **System Info**: Shows system information

## Usage

### Starting the Terminal
1. Click on an AP tab in the dashboard
2. Go to "SSH Terminal" tab
3. Click "Open SSH Terminal" button
4. Terminal opens in new window with xterm.js

### Manual Commands
- Type directly into terminal (just like a real terminal)
- Use arrow keys, tab completion, etc.
- Interactive programs (vim, htop, top) work properly

### Quick Commands
- Click any quick command button
- Command executes immediately
- Output appears in terminal with proper formatting

### Service Mode Detection
When connected to an AP:
1. Terminal detects "servicemode>" prompt automatically
2. Runs `status` command
3. Parses Java Version from output
4. Saves Java Version to database
5. Sends notification to parent window

## Technical Details

### Communication Flow
```
Tkinter (UI) 
    ↓
pywebview (Browser)
    ↓
xterm.js (Terminal Display)
    ↓ WebSocket
Flask-SocketIO Server
    ↓ Paramiko
SSH Server (AP)
```

### Port Configuration
- Flask server: `127.0.0.1:5555`
- Only accessible locally (security)
- WebSocket endpoint: `ws://127.0.0.1:5555/socket.io`

### Session Management
- Each AP gets unique session ID
- Multiple terminals supported simultaneously
- Sessions persist during tab switches
- Clean disconnect on window close

## Advantages Over Old Implementation

### Before (Tkinter Text Widget + Paramiko)
❌ No terminal emulation
❌ No ANSI colors
❌ Manual output buffering
❌ Complex threading
❌ Limited features
❌ Can't handle interactive programs

### After (xterm.js + Flask + Paramiko)
✅ Full terminal emulation
✅ ANSI colors and formatting
✅ Professional terminal features
✅ Industry-standard (same as VS Code)
✅ Better performance
✅ Handles all terminal programs

## Troubleshooting

### Server won't start
- Check if port 5555 is available
- Look for Flask startup message in console
- Verify all dependencies installed

### Terminal window blank
- Wait 2-3 seconds for server to start
- Check browser console for JavaScript errors
- Verify Flask server is running

### SSH connection fails
- Check AP IP address, username, password
- Verify network connectivity
- Check SSH credentials in database

### Quick commands not working
- Ensure terminal is connected
- Check terminal output for errors
- Verify command syntax

## Future Enhancements

### Possible Additions
- Terminal themes selector
- Font size control
- Export session logs
- Multi-tab terminals in one window
- SSH key authentication
- Connection history
- Bookmark commands

## Testing

### Manual Test Steps
1. Open AP tab with valid SSH credentials
2. Click "Open SSH Terminal"
3. Verify terminal opens with xterm.js
4. Verify connection to AP succeeds
5. Test manual command input (e.g., `ls -la`)
6. Test quick command buttons
7. Test service mode auto-detection
8. Verify Java Version captured
9. Test exit service mode sequence
10. Close and reopen terminal

### Expected Results
- ✅ Terminal displays with professional look
- ✅ Connection shows green status bar
- ✅ Manual commands work properly
- ✅ Colors and formatting display correctly
- ✅ Quick commands execute successfully
- ✅ Service mode detected and status runs
- ✅ Java Version appears in database
- ✅ Exit service mode completes full sequence

## Files Modified

- `dashboard_components/content_panel.py` - Updated to use xterm.js
- `ssh_terminal_server.py` - New Flask backend
- `templates/ssh_terminal.html` - New xterm.js frontend
- `xterm_integration.py` - New Tkinter integration
- `xterm_requirements.txt` - New dependencies

## Rollback Plan

If issues occur, you can revert to old implementation:
1. Restore `dashboard_components/content_panel.py` from git
2. Remove xterm imports
3. Uninstall new dependencies (optional)
4. Old Paramiko-based terminal will work again

## Support

For issues or questions:
1. Check Flask server console output
2. Check browser JavaScript console
3. Verify all dependencies installed
4. Test with simple SSH connection first
5. Check network connectivity
