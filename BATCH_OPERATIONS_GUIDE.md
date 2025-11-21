# Batch Operations Tools - User Guide

## Overview

The Batch Operations tools allow you to perform automated tasks on multiple Access Points (APs) simultaneously, saving time and reducing repetitive work. All batch tools share a common interface and workflow.

## Accessing Batch Tools

From the main dashboard menu bar:
**Tools** → Select desired batch operation:
- **Batch Ping** - Test connectivity to multiple APs
- **Batch Browser Operations** - Automate web interface actions
- **Batch SSH Operations** - Execute SSH commands on multiple APs

## Common Workflow

All batch operations follow this workflow:

### 1. AP Selection

#### Search for APs
- Enter search term in the search box (AP ID, hostname, IP address, MAC address, or store ID)
- Click **Search** or press Enter
- Results appear in the tree view below

#### Multi-Search Selection
- You can search multiple times and accumulate results
- Previous search results are preserved when you search again
- This allows you to build a list of APs from different stores, IP ranges, etc.

#### Mark APs for Operation
- Select one or more APs from the search results (use Ctrl+Click for multiple)
- Click **Mark Selected** to add them to the operation list
- A checkmark (✓) appears in the first column for marked APs
- The status bar shows how many APs are marked

#### Managing Selections
- **Unmark Selected** - Remove selected APs from the marked list
- **Clear All Marks** - Remove all marks and start over
- You can mark/unmark as many times as needed before executing

### 2. Configure Operation

Each tool has specific settings:

#### Batch Ping Settings
- **Ping Count** - Number of ping packets to send (1-10)
- **Timeout** - Seconds to wait for response (1-10)
- **Max Parallel** - How many APs to ping simultaneously (1-50)

#### Batch Browser Settings
- **Operation Type** - Select from:
  - Enable SSH Server
  - Disable SSH Server
  - Reboot AP
  - Check AP Status
  - Read Configuration
  - Custom Action
- **Max Parallel Tabs** - How many browser tabs to open (1-10)
- **Timeout** - Page load timeout in seconds (10-120)

#### Batch SSH Settings
- **Quick Commands** - Pre-defined commands like uptime, ifconfig, etc.
- **Custom Command** - Enter any SSH command
- **Timeout** - Command execution timeout (10-300 seconds)
- **Max Parallel** - How many SSH connections to open (1-20)

### 3. Execute Operation

1. Click **Execute Operation**
2. A confirmation dialog appears showing:
   - Operation description
   - List of all marked APs
   - Warning about the operation
3. Review carefully and click **Execute** to proceed or **Cancel** to abort

### 4. Monitor Progress

During execution:

#### Progress Bar
- Shows overall completion percentage
- Updates as each AP is processed

#### APs in Operation (Left Panel)
- Lists all APs being processed
- Shows status for each AP:
  - **Pending** - Waiting to be processed
  - **Running** - Currently being processed
  - **Success** - Operation completed successfully (green)
  - **Failed** - Operation failed (red)
- Shows brief result message

#### Activity Log (Right Panel)
- Detailed log of all operations
- Color-coded messages:
  - **Black** - Informational messages
  - **Green** - Success messages
  - **Orange** - Warnings
  - **Red** - Errors
- Timestamps for all events
- Scrolls automatically to show latest

#### Controls
- **Stop** button - Abort the operation (stops after current batch completes)
- Operation completes automatically when all APs are processed

## Batch Ping Tool

### Purpose
Test network connectivity to multiple APs quickly.

### Use Cases
- Verify APs are online after network changes
- Find offline APs in a store or region
- Measure response times across multiple locations
- Update database status for many APs at once

### Features
- Parallel pinging for speed
- Automatic database status updates
- Packet loss detection
- Average ping time calculation

### Results
- **Success** - AP responded to pings
  - Shows packet loss percentage if any
  - Shows average ping time in milliseconds
  - Updates AP status to "online" in database
- **Failed** - AP did not respond
  - Shows reason (timeout, unreachable, etc.)
  - Updates AP status to "offline" in database

## Batch Browser Operations Tool

### Purpose
Automate web interface actions on multiple APs.

### Use Cases
- Enable SSH on multiple APs for troubleshooting
- Disable SSH after maintenance
- Reboot multiple APs after configuration changes
- Check status of many APs quickly
- Backup configurations from multiple APs

### Features
- Opens web interfaces automatically
- Handles login with stored credentials
- Processes Cato Networks warnings automatically
- Multiple parallel tabs for efficiency
- Keeps browser minimized to avoid distraction

### Available Operations

#### Enable SSH Server
- Navigates to SSH settings page
- Enables SSH server checkbox
- Applies configuration
- Verifies if already enabled

#### Disable SSH Server
- Navigates to SSH settings page
- Disables SSH server checkbox
- Applies configuration

#### Reboot AP
- Navigates to reboot page
- Initiates reboot
- Handles confirmation dialogs

#### Check AP Status
- Loads main page
- Extracts status information
- Reports if AP is responding

#### Read Configuration
- Placeholder for configuration backup
- Can be customized per AP model

#### Custom Action
- Allows custom automation
- Enter description in text box
- Implement specific actions per requirement

### Important Notes
- **Authentication Required** - APs must have passwords configured in database
- **Browser Visible** - Browser window opens but stays minimized
- **Timeout Handling** - Operations may timeout on slow connections
- **Parallel Limit** - Keep low (5-10) to avoid overwhelming network

### Troubleshooting
- If operations fail, check:
  - AP passwords are correct
  - APs are accessible (try Batch Ping first)
  - Network allows HTTP access
  - Timeout is sufficient for slow connections

## Batch SSH Operations Tool

### Purpose
Execute SSH commands on multiple APs simultaneously.

### Use Cases
- Check system status across multiple APs
- Collect diagnostic information
- Restart services on many APs
- Apply configuration changes
- Run maintenance scripts

### Features
- Parallel SSH connections
- Pre-defined quick commands
- Custom command execution
- Dangerous command detection
- Full output capture

### Quick Commands
- **Show Uptime** - `uptime`
- **Show IP Configuration** - `ifconfig`
- **Show Running Processes** - `ps aux`
- **Show Disk Usage** - `df -h`
- **Show Memory Info** - `free -m`
- **Check SSH Service** - `systemctl status ssh`
- **Restart Network** - `systemctl restart networking`

### Custom Commands
- Enter any SSH command
- Multi-line commands supported
- Command runs with user's privileges on AP
- Output captured and displayed

### Safety Features
- **Dangerous Command Detection** - Warns about:
  - `rm -rf` (recursive file deletion)
  - `dd if=` (disk operations)
  - `mkfs` (filesystem formatting)
  - `format` (formatting)
  - `> /dev/` (device writes)
  - `shutdown` / `halt` (system shutdown)
- **Confirmation Dialog** - Shows exactly what will execute
- **Per-AP Execution** - Each AP runs independently
- **Timeout Protection** - Commands killed if they run too long

### Results
- **Success** - Command executed with exit code 0
  - Shows command output
  - Output saved to activity log
- **Failed** - Command failed or error occurred
  - Shows error message or exit code
  - Common failures:
    - Authentication failed - Wrong password
    - Connection timeout - AP not reachable
    - SSH error - SSH service not running
    - Network error - Network issues

### Important Notes
- **SSH Access Required** - APs must have SSH enabled and credentials configured
- **Command Privileges** - Commands run as the configured SSH user
- **No Sudo Prompts** - Commands requiring sudo may fail or need password in command
- **Output Limits** - Very long output is truncated in status column (full output in log)
- **Parallel Connections** - Reduce if network becomes overloaded

### Best Practices
1. **Test First** - Run commands on 1-2 APs before batch execution
2. **Read-Only Commands** - Start with status/info commands
3. **Backup** - Always backup before making changes
4. **Appropriate Parallelism**:
   - Fast commands (uptime, status): 15-20 parallel
   - Medium commands (config reads): 10-15 parallel  
   - Slow commands (updates, restarts): 5-10 parallel
5. **Timeout Setting**:
   - Quick commands: 10-30 seconds
   - Config changes: 30-60 seconds
   - Service restarts: 60-120 seconds
   - System updates: 120-300 seconds

## Tips and Best Practices

### General
1. **Start Small** - Test on 2-3 APs before running on many
2. **Check Connectivity** - Run Batch Ping before other operations
3. **Peak Hours** - Avoid batch operations during busy hours if possible
4. **Monitor Progress** - Watch activity log for errors
5. **Document Results** - Copy activity log if needed for records

### Search Strategy
1. Use specific searches to reduce results:
   - Store ID for specific store
   - IP range for network segment
   - Hostname pattern for AP groups
2. Mark as you go - search, mark, search again, mark more
3. Double-check marked count before executing

### Parallelism Guidelines
- **Network Speed** affects optimal parallelism:
  - Fast network (LAN): Higher parallelism (20-50)
  - WAN/Internet: Lower parallelism (5-15)
  - Slow connections: Very low (2-5)
- **Operation Type** affects optimal parallelism:
  - Ping: Can be very high (50+)
  - Browser: Keep moderate (5-10)
  - SSH: Depends on command (5-20)
- **System Resources**:
  - Many parallel operations use more CPU/RAM
  - Reduce if system becomes slow

### Error Handling
- Review failed operations in the log
- Common issues:
  - Authentication failures - Update credentials
  - Timeouts - Increase timeout or reduce parallelism
  - Connection refused - Check if service is running
  - Network unreachable - Check network/firewall
- Re-run failed APs:
  - Clear all marks
  - Search for failed AP IDs
  - Mark them
  - Execute again with adjusted settings

## Troubleshooting

### Tool Won't Open
- Check if another instance is already open
- Close and reopen from Tools menu
- Check application logs for errors

### Search Returns No Results
- Verify search term is correct
- Check database connection
- Ensure APs are registered in database
- Try wildcard searches if supported

### Operation Fails Immediately
- Check if APs are marked (look for ✓)
- Verify operation settings are valid
- Check activity log for specific error

### All Operations Fail
- **Ping**: Network issue, firewall, APs offline
- **Browser**: Passwords missing, APs not accessible, wrong IP
- **SSH**: SSH not enabled, wrong credentials, firewall

### Some Operations Succeed, Some Fail
- Normal - APs may have different configurations
- Review failures individually in activity log
- Adjust settings or credentials for failed APs
- Re-run failed APs separately

### Performance Issues
- Reduce parallel operations
- Increase timeouts
- Close other applications
- Check network bandwidth usage

## Safety and Security

### Important Warnings
⚠ **Authentication** - Tools use stored credentials, ensure they're secure
⚠ **Destructive Operations** - Some operations (reboot, SSH commands) can affect AP availability
⚠ **Network Impact** - Many parallel operations can affect network performance
⚠ **Production Systems** - Test in lab environment first if possible

### Security Considerations
1. **Credentials** - Stored in database, ensure database is secure
2. **SSH Commands** - Can execute any command the user has privilege for
3. **Browser Operations** - Automate privileged actions, ensure authorization
4. **Audit Trail** - All operations logged, review regularly

### Best Practices
1. **Least Privilege** - Use accounts with minimum required privileges
2. **Change Windows** - Schedule batch operations during maintenance windows
3. **Approval Process** - Get approval for large-scale operations
4. **Rollback Plan** - Have plan to reverse changes if needed
5. **Documentation** - Document what operations were performed and why

## Advanced Features

### Keyboard Shortcuts
- **Enter** in search box - Execute search
- **Ctrl+Click** in tree - Multi-select APs
- **Shift+Click** in tree - Range select APs

### Status Colors
- **Green** - Success
- **Red** - Failure
- **Orange** - Warning
- **Blue** - In progress
- **Gray** - Pending/Inactive

### Export Results
- Activity log can be selected and copied
- Use Ctrl+C after selecting text
- Paste into documentation or tickets

## Support and Feedback

If you encounter issues or have suggestions:
1. Check this documentation first
2. Review activity log for error details
3. Contact support with:
   - Tool name (Ping/Browser/SSH)
   - Number of APs affected
   - Error messages from activity log
   - Steps to reproduce issue

---

**Version:** 1.0
**Last Updated:** 2025-11-20
