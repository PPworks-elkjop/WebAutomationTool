# Batch Operations Quick Reference

## Access
**Dashboard → Tools Menu** → Select batch operation

## Quick Start (All Tools)

### 1. Search & Mark APs
```
1. Enter search term (AP ID, hostname, IP, MAC, store)
2. Click [Search] or press Enter
3. Select APs in results (Ctrl+Click for multiple)
4. Click [Mark Selected]
5. Repeat steps 1-4 to add more APs
```

### 2. Configure Operation
- Set operation type and parameters
- Adjust timeout and parallelism

### 3. Execute
```
1. Click [Execute Operation]
2. Review confirmation dialog
3. Click [Execute] to confirm
4. Monitor progress
```

## Tool-Specific Quick Reference

### 🔍 Batch Ping
**Purpose:** Test connectivity on multiple APs

**Settings:**
- Ping Count: 4 (default)
- Timeout: 2s (default)
- Max Parallel: 20 (default)

**Best For:**
- Quick connectivity checks
- Finding offline APs
- Updating database status

**Speed:** ⚡⚡⚡ Very Fast (20-50 APs per minute)

---

### 🌐 Batch Browser Operations
**Purpose:** Automate web interface tasks

**Operations:**
- ✓ Enable/Disable SSH Server
- ✓ Reboot AP
- ✓ Check Status
- ✓ Read Configuration
- ✓ Custom Actions

**Settings:**
- Max Parallel Tabs: 5 (default)
- Timeout: 30s (default)

**Best For:**
- Enabling SSH for troubleshooting
- Mass reboots
- Configuration changes

**Speed:** ⚡⚡ Medium (5-10 APs per minute)

**Note:** Requires stored passwords

---

### 💻 Batch SSH Operations
**Purpose:** Execute SSH commands on multiple APs

**Quick Commands:**
- Show Uptime
- Show IP Configuration
- Show Running Processes
- Show Disk Usage
- Show Memory Info
- Check SSH Service
- Restart Network

**Settings:**
- Timeout: 30s (default)
- Max Parallel: 10 (default)

**Best For:**
- System diagnostics
- Service management
- Configuration changes
- Log collection

**Speed:** ⚡⚡ Medium (10-15 APs per minute)

**Note:** Requires SSH access enabled

---

## Parallelism Guide

### How Many Parallel Operations?

| Network Speed | Ping | Browser | SSH |
|---------------|------|---------|-----|
| Fast LAN      | 50   | 10      | 20  |
| WAN/Internet  | 20   | 5       | 10  |
| Slow/Remote   | 10   | 3       | 5   |

### Operation Speed Guide

| Command Type      | Parallel | Timeout |
|-------------------|----------|---------|
| Info/Status       | 15-20    | 10-30s  |
| Config Read       | 10-15    | 30-60s  |
| Service Restart   | 5-10     | 60-120s |
| System Update     | 2-5      | 120s+   |

---

## Common Workflows

### Workflow 1: Store Maintenance
```
Purpose: Enable SSH on all APs in a store

1. Open: Batch Browser Operations
2. Search: "store:9001"
3. Mark: All results
4. Operation: Enable SSH Server
5. Max Tabs: 5
6. Execute & Monitor
```

### Workflow 2: Find Offline APs
```
Purpose: Identify offline APs across multiple stores

1. Open: Batch Ping
2. Search: "store:9001" → Mark results
3. Search: "store:9002" → Mark results
4. Search: "store:9003" → Mark results
5. Execute
6. Review: APs marked as "Failed" are offline
```

### Workflow 3: Collect Diagnostics
```
Purpose: Get uptime from all APs in a region

1. Open: Batch SSH Operations
2. Search: "ip:10.50" → Mark all
3. Search: "ip:10.51" → Mark all
4. Click: [Show Uptime] button
5. Parallel: 15, Timeout: 30s
6. Execute
7. Copy activity log for report
```

### Workflow 4: Emergency Reboot
```
Purpose: Reboot multiple problematic APs

1. Open: Batch Browser Operations
2. Search for problem APs by ID or hostname
3. Mark affected APs
4. Operation: Reboot AP
5. Max Tabs: 3 (to avoid overwhelming network)
6. Execute with confirmation
7. Wait 5 minutes
8. Use Batch Ping to verify they're back online
```

---

## Troubleshooting Quick Fixes

### Problem: No Search Results
**Fix:** Check search term, try wildcards or partial matches

### Problem: All Operations Fail
**Fix:** 
- Ping: Check network connectivity
- Browser: Verify passwords in database
- SSH: Ensure SSH is enabled on APs

### Problem: Some Fail, Some Succeed
**Fix:** Normal - review failed ones individually, adjust credentials or settings

### Problem: Operations Too Slow
**Fix:** Reduce parallelism, increase timeout

### Problem: Browser Hangs
**Fix:** 
- Reduce parallel tabs to 2-3
- Increase timeout to 60s
- Check network speed

### Problem: SSH Authentication Fails
**Fix:**
- Verify SSH credentials in database
- Ensure SSH service is running on AP
- Try enabling SSH via Browser tool first

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Execute search | Enter (in search box) |
| Multi-select | Ctrl+Click |
| Range select | Shift+Click |
| Copy log text | Ctrl+C (after selecting) |

---

## Progress Indicators

### Colors
- 🟢 **Green** = Success
- 🔴 **Red** = Failed
- 🟠 **Orange** = Warning
- 🔵 **Blue** = In Progress
- ⚪ **Gray** = Pending

### Status Terms
- **Pending** - Waiting in queue
- **Running** - Currently processing
- **Success** - Completed successfully
- **Failed** - Operation failed (see details)

---

## Safety Reminders

⚠ **Before Executing:**
1. Double-check marked AP count
2. Review operation description
3. Verify settings are appropriate
4. Consider impact on production
5. Have rollback plan if needed

⚠ **Dangerous SSH Commands:**
- System will warn about: `rm -rf`, `dd`, `mkfs`, `format`, `shutdown`
- Always confirm these carefully
- Test on one AP first

⚠ **Production Impact:**
- Reboots cause brief outage
- Service restarts may interrupt connections
- Plan during maintenance windows when possible

---

## Quick Tips

💡 **Multi-Search Selection**
- Search multiple times without clearing
- Build comprehensive AP list from different criteria
- Mark as you go

💡 **Test Small First**
- Always test on 2-3 APs before large batches
- Verify settings and credentials work
- Adjust based on results

💡 **Monitor Progress**
- Watch activity log for errors
- Stop operation if seeing widespread failures
- Adjust settings and retry

💡 **Save Log Output**
- Select and copy activity log
- Keep records of batch operations
- Use for troubleshooting or documentation

💡 **Optimize Performance**
- Fast operations: Higher parallelism
- Slow operations: Lower parallelism
- Network issues: Reduce and increase timeout

---

## Support

**Need Help?**
- See: `BATCH_OPERATIONS_GUIDE.md` for detailed documentation
- Check activity log for specific error messages
- Review AP credentials in database
- Contact support with log excerpts

---

**Version:** 1.0 | **Last Updated:** 2025-11-20
