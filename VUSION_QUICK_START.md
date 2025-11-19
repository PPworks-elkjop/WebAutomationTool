# Vusion API Integration - Quick Start

## ✅ What's Been Created

I've built a complete, production-ready system for managing multiple Vusion API keys across different countries and services:

### 📁 Files Created

1. **vusion_api_config.py** (350 lines)
   - Encrypted API key storage
   - Multi-country, multi-service support
   - URL and store ID builders
   - Security with AES-256 encryption

2. **vusion_api_helper.py** (250 lines)
   - Simplified API request methods
   - Error handling and logging
   - Common operations ready to use
   - Test connection functionality

3. **vusion_config_dialog.py** (550 lines)
   - Professional GUI for managing keys
   - 3 tabs: Manage Keys, Test Connections, View Configured Keys
   - Integrated into dashboard menu
   - Test before you deploy

4. **VUSION_API_README.md** - Complete documentation
5. **test_vusion_api.py** - Automated test suite

### 🔧 Dashboard Integration

Added to **Admin Menu**:
- "Manage Vusion API Keys" → Opens configuration dialog

## 🚀 How To Use

### Step 1: Open Configuration

From VERA dashboard:
```
Admin → Manage Vusion API Keys
```

### Step 2: Add API Key

1. Select **Country** (NO, SE, FI, DK, IS)
2. Select **Service** (Vusion Manager PRO, Cloud, or Retail)
3. Paste your **API Subscription Key**
4. Click **Save API Key**

### Step 3: Test Connection

1. Go to **Test Connections** tab
2. Select country and service
3. Click **Test Connection**
4. Verify ✓ SUCCESS message

### Step 4: Query a Store

Still in Test Connections tab:
1. Enter store number (e.g., "4010")
2. Click **Query Store**
3. View store information

## 💡 Key Features

### 🔒 Security
- **AES-256 encryption** for all API keys
- Separate encryption from AP credentials
- Keys never exposed in plain text
- Secure file permissions

### 🌍 Multi-Country Support
- **NO** - Elkjøp, Lefdal
- **SE** - Elgiganten
- **FI** - Gigantti
- **DK** - Elgiganten
- **IS** - Elko

### 🔌 Multi-Service Support
- **Vusion Manager PRO** - Stores, labels, gateways, templates
- **Vusion Cloud** - Devices, templates
- **Vusion Retail** - Products, prices

### 🏗️ Smart Store ID Builder
```python
config.build_store_id('FI', 'gigantti', '4010')
# Returns: 'gigantti_fi.4010'
```

### 🔗 Automatic URL Building
```python
config.get_endpoint_url('vusion_pro', 'stores', storeId='gigantti_fi.4010')
# Returns: 'https://api-eu.vusion.io/vusion-pro/v1/stores/gigantti_fi.4010'
```

## 📖 Usage Examples

### Simple Store Query

```python
from vusion_api_helper import VusionAPIHelper

helper = VusionAPIHelper()

# Get store info
success, data = helper.get_store_info('FI', 'gigantti', '4010')

if success:
    print(f"Store: {data['name']}")
    print(f"Status: {data['status']}")
else:
    print(f"Error: {data}")
```

### Get Store Labels

```python
helper = VusionAPIHelper()

success, data = helper.get_store_labels('FI', 'gigantti', '4010')

if success:
    for label in data.get('labels', []):
        print(f"Label {label['id']}: {label['status']}")
```

### Test Connection

```python
helper = VusionAPIHelper()

success, msg = helper.test_connection('FI', 'vusion_pro')
print(f"Connection: {msg}")
```

## 🗂️ File Storage

Configuration stored securely:
- **Config**: `~/.vera_vusion_config.json` (encrypted)
- **Key**: `~/.vera_vusion_key`
- Automatic creation on first use
- Restricted file permissions

## 🎯 Real-World Example

Your original request was for store gigantti_fi.4010:

```python
from vusion_api_helper import VusionAPIHelper

helper = VusionAPIHelper()

# Query the store
success, data = helper.get_store_info('FI', 'gigantti', '4010')

if success:
    print(f"""
    Store Information:
    - ID: {data.get('id')}
    - Name: {data.get('name')}
    - Status: {data.get('status')}
    - Address: {data.get('address')}
    """)
```

## 🔄 Scaling to 10-15 Keys

The system is designed for exactly this:

### Example Setup
```
Norway:
  - Vusion Manager PRO: key-norway-pro
  - Vusion Cloud: key-norway-cloud
  - Vusion Retail: key-norway-retail

Sweden:
  - Vusion Manager PRO: key-sweden-pro
  - Vusion Cloud: key-sweden-cloud

Finland:
  - Vusion Manager PRO: key-finland-pro
  - Vusion Cloud: key-finland-cloud

Denmark:
  - Vusion Manager PRO: key-denmark-pro

Iceland:
  - Vusion Manager PRO: key-iceland-pro
```

Each key is:
- ✅ Encrypted separately
- ✅ Testable independently
- ✅ Easy to update
- ✅ Managed via GUI

## 🛠️ Advanced Usage

### Custom API Request

```python
from vusion_api_helper import VusionAPIHelper

helper = VusionAPIHelper()

# Make custom request
success, data = helper.make_request(
    country='FI',
    service='vusion_pro',
    endpoint='labels',
    method='GET',
    storeId='gigantti_fi.4010'
)
```

### Low-Level Configuration

```python
from vusion_api_config import VusionAPIConfig

config = VusionAPIConfig()

# Get all configured keys
all_keys = config.get_all_keys()
for country, services in all_keys.items():
    for service, key in services.items():
        print(f"{country}/{service}: {key[:10]}...")

# Get request headers
headers = config.get_request_headers('FI', 'vusion_pro')
# Includes API key automatically
```

## 🎨 Integration Ideas

### Add to AP Panel

Show Vusion store status in AP overview:

```python
# In ap_panel.py _populate_overview_tab()

from vusion_api_helper import VusionAPIHelper

helper = VusionAPIHelper()
store_number = ap_data.get('store_number')
country = ap_data.get('country')
chain = ap_data.get('chain')

success, data = helper.get_store_info(country, chain, store_number)

if success:
    # Add to overview
    self._create_info_field(overview, "Vusion Store Status", 
                           data.get('status', 'Unknown'))
```

### Add Vusion Tab to AP Panel

Create dedicated Vusion tab showing:
- Store status
- Label count
- Gateway status
- Recent updates

## 🧪 Testing

Run the test suite:

```bash
cd WebAutomationTool
python test_vusion_api.py
```

Tests:
- ✅ Store ID building
- ✅ URL construction
- ✅ Configuration loading
- ✅ API connections (if keys configured)
- ✅ GUI functionality

## 📝 Next Steps

1. **Add your first API key**
   - Open VERA dashboard
   - Admin → Manage Vusion API Keys
   - Add key for your main country

2. **Test connection**
   - Use Test Connections tab
   - Verify key works

3. **Query a test store**
   - Use a known working store number
   - Verify data retrieval

4. **Expand to other countries**
   - Add keys one by one
   - Test each before moving to next

5. **Integrate with AP Panel**
   - Show Vusion status in overview
   - Add quick actions for common tasks

## 🆘 Troubleshooting

### "No API keys configured"
→ Add keys via Admin → Manage Vusion API Keys

### "401 Unauthorized"
→ API key is invalid or expired

### "404 Not Found"
→ Store ID doesn't exist or wrong format

### "Network Error"
→ Check internet connection or firewall

## 🎉 Summary

You now have:
- ✅ Secure storage for 10-15 API keys
- ✅ Support for 5 countries
- ✅ Support for 3 Vusion services
- ✅ GUI management interface
- ✅ Simple Python API
- ✅ Automatic URL building
- ✅ Connection testing
- ✅ Complete documentation
- ✅ Test suite

**All encrypted, all secure, all ready to use!**
