# Vusion Manager Pro Integration - Quick Start Guide

## Current Status: Testing Phase

### Objective
Integrate Vusion Manager Pro API to display AP online/offline status in the AP Panel search results, similar to the Jira integration.

### Implementation Files

1. **configure_vusion_se_lab.py** - Quick setup script to store API key
2. **test_elkjop_se_lab.py** - Test script to verify API connectivity
3. **vusion_api_config.py** - Updated with elkjop_se_lab store pattern
4. **vusion_api_helper.py** - Already has GET request methods

### Setup Steps

#### Step 1: Store API Key

Run the configuration script:
```powershell
python configure_vusion_se_lab.py
```

This will prompt you for your Vusion Manager Pro API key and store it securely.

**Store Details:**
- Store ID: `elkjop_se_lab.lab5`
- Country: `SE` (Sweden)
- Service: `vusion_pro` (Vusion Manager Pro)

#### Step 2: Test Connection

Run the test script:
```powershell
python test_elkjop_se_lab.py
```

This will:
1. Verify API key is configured
2. Test basic connectivity
3. Query store information (GET /stores/elkjop_se_lab)
4. Display gateway/AP data with online/offline status
5. Test dedicated gateways endpoint if available

#### Step 3: Review Results

The test script will show:
- Store basic information
- **Gateway/AP status** (🟢 online / 🔴 offline)
- IP addresses
- Full JSON response for analysis

### Expected API Response Structure

```json
{
  "id": "elkjop_se_lab.lab5",
  "name": "Elkjop SE Lab",
  "status": "active",
  "gateways": [
    {
      "id": "gateway-001",
      "name": "AP-001",
      "online": true,
      "status": "active",
      "ipAddress": "10.x.x.x"
    }
  ]
}
```

### Next Steps (After Testing)

Once the test script confirms the API is working:

#### 1. AP Panel Integration
   - Add Vusion API call to AP search function
   - Match AP IP addresses to Vusion gateway data
   - Display online/offline indicator (like Jira)

#### 2. Status Indicators
   - 🟢 Online (green)
   - 🔴 Offline (red)
   - ⚠️ Unknown (if Vusion data unavailable)

#### 3. Additional Information (Future)
   - Last seen timestamp
   - Signal strength
   - Number of connected labels
   - Gateway firmware version

### Files Modified

- `vusion_api_config.py` - Added `elkjop_se_lab` pattern for Sweden
- `configure_vusion_se_lab.py` - Created (API key setup)
- `test_elkjop_se_lab.py` - Created (testing)

### Security Notes

- API key is encrypted using Fernet (AES-256)
- Stored in: `~/.vera_vusion_config.json` (encrypted)
- Encryption key: `~/.vera_vusion_key` (permissions 0o600)
- Never commit these files to version control

### Troubleshooting

**Issue: API key not working**
- Verify key is correct
- Check if key has expired
- Confirm key has access to elkjop_se_lab.lab5 store

**Issue: Store not found (404)**
- Verify store ID format: `elkjop_se_lab.lab5`
- Check if store exists in Vusion system
- Try different store ID pattern if needed

**Issue: No gateway data**
- Some stores might not include gateways in main store endpoint
- Try dedicated `/stores/elkjop_se_lab.lab5/gateways` endpoint
- Check if API key has permission for gateway data

### Current Limitations

- **Read-only** - Only GET requests implemented
- Single store support for now
- No automatic refresh/polling
- Manual correlation between AP IP and Vusion gateway

### Future Enhancements

1. Batch query multiple stores
2. Real-time status monitoring
3. Automatic AP-to-Gateway mapping
4. Status history/trends
5. Alert on AP offline events
6. Integration with VERA dashboard
