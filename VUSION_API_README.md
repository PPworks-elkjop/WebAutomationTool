# Vusion API Integration

## Overview

The Vusion API integration allows VERA to interact with multiple Vusion services across different countries. The system securely stores API keys and provides an easy-to-use interface for making API calls.

## Architecture

### Components

1. **vusion_api_config.py** - Configuration manager
   - Stores API keys encrypted
   - Manages multiple countries and services
   - Builds proper URLs and store IDs

2. **vusion_api_helper.py** - Request helper
   - Simplified API request methods
   - Error handling and logging
   - Common operations (get store info, labels, gateways)

3. **vusion_config_dialog.py** - GUI management
   - Add/edit/delete API keys
   - Test connections
   - Query stores

## Supported Countries

- **NO** - Norway (Elkjøp, Lefdal)
- **SE** - Sweden (Elgiganten)
- **FI** - Finland (Gigantti)
- **DK** - Denmark (Elgiganten)
- **IS** - Iceland (Elko)

## Supported Services

### Vusion Manager PRO
Base URL: `https://api-eu.vusion.io/vusion-pro/v1`

Endpoints:
- `/stores/{storeId}` - Get store information
- `/stores/{storeId}/labels` - Get store labels
- `/stores/{storeId}/gateways` - Get store gateways
- `/stores/{storeId}/templates` - Get store templates

### Vusion Cloud
Base URL: `https://api-eu.vusion.io/vusion-cloud/v1`

Endpoints:
- `/devices` - Get devices
- `/templates` - Get templates

### Vusion Retail
Base URL: `https://api-eu.vusion.io/vusion-retail/v1`

Endpoints:
- `/products` - Get products
- `/prices` - Get prices

## Setup

### 1. Configure API Keys

From the VERA dashboard:
1. Go to **Admin** → **Manage Vusion API Keys**
2. Select country (NO, SE, FI, DK, IS)
3. Select service (Vusion Manager PRO, Vusion Cloud, Vusion Retail)
4. Enter API subscription key
5. Click **Save API Key**

### 2. Test Connection

1. Go to **Test Connections** tab
2. Select country and service
3. Click **Test Connection**
4. Verify successful connection

### 3. Query Store

1. Stay in **Test Connections** tab
2. Enter store number (e.g., "4010")
3. Click **Query Store**
4. View store information

## Usage Examples

### Python Code

#### Basic Store Query

```python
from vusion_api_helper import VusionAPIHelper

helper = VusionAPIHelper()

# Get store info for Gigantti Finland store 4010
success, data = helper.get_store_info('FI', 'gigantti', '4010')

if success:
    print(f"Store Name: {data['name']}")
    print(f"Store ID: {data['id']}")
    print(f"Status: {data['status']}")
else:
    print(f"Error: {data}")
```

#### Get Store Labels

```python
helper = VusionAPIHelper()

success, data = helper.get_store_labels('FI', 'gigantti', '4010')

if success:
    print(f"Found {len(data.get('labels', []))} labels")
    for label in data.get('labels', []):
        print(f"  - {label['id']}: {label['status']}")
```

#### Custom API Request

```python
helper = VusionAPIHelper()

# Make a custom GET request
success, data = helper.make_request(
    country='FI',
    service='vusion_pro',
    endpoint='stores',
    method='GET',
    storeId='gigantti_fi.4010'
)
```

### Low-Level Configuration API

```python
from vusion_api_config import VusionAPIConfig

config = VusionAPIConfig()

# Set API key
config.set_api_key('FI', 'vusion_pro', 'your-api-key-here')

# Get API key (decrypted)
api_key = config.get_api_key('FI', 'vusion_pro')

# Build store ID
store_id = config.build_store_id('FI', 'gigantti', '4010')
# Returns: 'gigantti_fi.4010'

# Get full endpoint URL
url = config.get_endpoint_url('vusion_pro', 'stores', storeId=store_id)
# Returns: 'https://api-eu.vusion.io/vusion-pro/v1/stores/gigantti_fi.4010'

# Get request headers with API key
headers = config.get_request_headers('FI', 'vusion_pro')
# Returns: {
#     'Cache-Control': 'no-cache',
#     'Ocp-Apim-Subscription-Key': 'your-api-key-here',
#     'Content-Type': 'application/json'
# }
```

## Store ID Format

Store IDs follow this pattern: `{chain}_{country}.{store_number}`

Examples:
- `gigantti_fi.4010` - Gigantti Finland store 4010
- `elkjop_no.1234` - Elkjøp Norway store 1234
- `elgiganten_se.5678` - Elgiganten Sweden store 5678
- `elgiganten_dk.9012` - Elgiganten Denmark store 9012
- `elko_is.3456` - Elko Iceland store 3456

## Security

### Encryption

- API keys are encrypted using AES-256 (Fernet)
- Keys stored in `~/.vera_vusion_config.json` (encrypted)
- Encryption key stored in `~/.vera_vusion_key`
- Files have restricted permissions (0o600)

### Key Separation

- Separate encryption from AP credentials
- Independent key files
- Can be backed up separately

## File Locations

- **Config**: `~/.vera_vusion_config.json`
- **Encryption Key**: `~/.vera_vusion_key`
- **Backup**: Copy both files to backup location

## Integration with AP Panel

To add Vusion API calls to the AP Panel:

```python
# In ap_panel.py

def _show_vusion_info(self, ap_data):
    """Show Vusion store information."""
    from vusion_api_helper import VusionAPIHelper
    
    helper = VusionAPIHelper()
    
    # Determine country and chain from AP data
    country = ap_data.get('country', 'NO')
    chain = ap_data.get('chain', 'elkjop')
    store_number = ap_data.get('store_number', '0000')
    
    # Get store info
    success, data = helper.get_store_info(country, chain, store_number)
    
    if success:
        # Display store information
        self._log(f"Store: {data.get('name')}")
        self._log(f"Status: {data.get('status')}")
    else:
        self._log(f"Error: {data}")
```

## Error Handling

### Common Errors

1. **401 Unauthorized** - Invalid API key
   - Check key in configuration
   - Verify key hasn't expired
   - Contact Vusion support for new key

2. **403 Forbidden** - Permission denied
   - API key doesn't have required permissions
   - Check subscription level

3. **404 Not Found** - Store doesn't exist
   - Verify store ID format
   - Check store number is correct

4. **Network Error** - Connection timeout
   - Check internet connection
   - Verify firewall isn't blocking API
   - Check VPN if required

### Test Connection First

Always test connection before querying:

```python
helper = VusionAPIHelper()

success, msg = helper.test_connection('FI', 'vusion_pro')

if success:
    # Proceed with queries
    success, data = helper.get_store_info('FI', 'gigantti', '4010')
else:
    print(f"Connection failed: {msg}")
```

## Best Practices

1. **Test First** - Always test connection before making queries
2. **Handle Errors** - Check success before accessing data
3. **Log Activity** - Log API calls for debugging
4. **Rate Limiting** - Be mindful of API rate limits
5. **Secure Keys** - Never commit API keys to version control
6. **Backup Config** - Backup configuration files regularly

## Troubleshooting

### API Key Not Working

1. Open **Manage Vusion API Keys**
2. Go to **Test Connections** tab
3. Select country and service
4. Click **Test Connection**
5. Check error message

### Store Not Found

1. Verify store number is correct
2. Check country/chain combination
3. Test with known working store first

### Network Issues

1. Check internet connection
2. Verify firewall settings
3. Test from different network
4. Check VPN requirements

## Future Enhancements

Potential additions:
- Batch store queries
- Label management
- Gateway monitoring
- Template management
- Product/price updates
- Automated alerts
- Store health dashboard

## Support

For issues or questions:
1. Check error messages in Test Connections tab
2. Verify API key is configured correctly
3. Test with simple query first
4. Check logs for detailed errors
5. Contact Vusion support for API issues
