# Security Configuration Guide

## Transport Security Overview

This application handles sensitive credentials and connects to multiple systems. Understanding the security options is crucial for safe operation.

---

## 🔒 Security Layers

### 1. **Browser Automation (Chrome/Selenium)**

#### Why SSL Verification is Disabled
```python
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
```

**Purpose**: Automate access to Access Points (APs) with self-signed certificates

**Security Context**:
- ✅ **Acceptable Trade-off**: APs use self-signed certificates by design
- ✅ **Controlled Environment**: Connecting to known internal devices
- ✅ **No User Data**: Browser automation only for AP management
- ❌ **Cannot Be Changed**: Chrome's security interstitials cannot be programmatically bypassed

**Risk Mitigation**:
- Only used for internal AP devices
- Network should be trusted (corporate network)
- No external websites are visited
- Credentials are still encrypted in transit (HTTPS)

---

### 2. **Jira API Connection (HTTPS/REST)**

#### Three Security Modes

##### Mode 1: Standard SSL Verification (Most Secure) 🟢
```python
verify_ssl = True
use_cert_pinning = False
```

**Best For**: 
- Public Jira Cloud instances
- Properly configured corporate Jira with valid CA certificates

**Requirements**:
- Valid SSL certificate signed by trusted CA
- System has access to CA certificate bundle

**Security**: ✅ Full certificate chain validation

---

##### Mode 2: Certificate Pinning (Recommended Alternative) 🟡
```python
verify_ssl = False  # or True
use_cert_pinning = True
```

**Best For**:
- Corporate Jira with self-signed or internal CA certificates
- When you don't have access to corporate CA bundle
- Situations where you know the server but can't verify against CA

**How It Works**:
1. On first connection, retrieve server certificate
2. Calculate SHA-256 fingerprint
3. Store fingerprint locally
4. On subsequent connections, verify fingerprint matches
5. Alert if certificate changes (potential MITM attack)

**Security**: 🔒 Trust-on-First-Use (TOFU) model
- Similar to SSH host key verification
- Protects against MITM after initial trust
- Detects certificate changes

**Setup**:
1. Enable "Use Certificate Pinning" in Admin Settings
2. Click "View/Manage Trusted Certificates"
3. Review certificate details carefully
4. Click "Trust Certificate" to pin it

**Storage**: `~/.webautomation/certificates/server_certificates.json`

---

##### Mode 3: No Verification (Least Secure) 🔴
```python
verify_ssl = False
use_cert_pinning = False
```

**Only Use When**:
- Behind corporate proxy with SSL inspection
- Temporary testing in completely trusted environment
- You understand and accept the risks

**Security**: ⚠️ **Vulnerable to Man-in-the-Middle attacks**

**Warnings**:
- Application will display prominent security warnings
- Consider using certificate pinning instead
- Only acceptable in fully trusted networks

---

### 3. **Credential Storage**

#### Windows DPAPI Encryption (Current) 🟢

```python
# Encryption using Windows Data Protection API
import win32crypt
encrypted = win32crypt.CryptProtectData(data, description, entropy, reserved, prompt, flags)
```

**Security Features**:
- ✅ **Per-User Protection**: Credentials encrypted with your Windows login credentials
- ✅ **Hardware-Bound**: Tied to the specific Windows machine and user account
- ✅ **No Key Storage**: Encryption key is derived from Windows login, not stored anywhere
- ✅ **OS-Level Security**: Uses Windows security infrastructure

**How It Works**:
1. Application uses Windows DPAPI to encrypt credentials
2. DPAPI uses your Windows login credentials as encryption key
3. Encrypted data can ONLY be decrypted by:
   - Same Windows user account
   - On same Windows machine
   - With correct Windows password

**Storage Location**: `~/.webautomation/credentials/credentials.db`

**Protected Credentials**:
- ✅ Jira API credentials (username, API token)
- ✅ Vusion API keys (all countries and services)
- ✅ Any future API credentials

**Important Notes**:
- ⚠️ If you change your Windows password, credentials may need to be re-entered
- ⚠️ Copying the database to another machine won't expose credentials (can't be decrypted)
- ⚠️ Other Windows users on same machine cannot access your credentials
- ✅ Significantly more secure than storing encryption keys in database or files

#### Migration from Old System

If upgrading from the old Fernet-based encryption:

**For Jira credentials:**
```bash
python migrate_credentials.py
```

**For Vusion API keys:**
```bash
python migrate_vusion_credentials.py
```

The scripts will:
1. Decrypt credentials using old Fernet key
2. Re-encrypt using Windows DPAPI
3. Remove old encryption key files
4. Provide migration report

**After migration**, all credentials are protected by Windows DPAPI instead of file-stored keys.

---

### 4. **SSH Connections (Paramiko)**

#### Current Implementation
```python
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
```

**Status**: 🔴 **NEEDS IMPROVEMENT**

#### Recommended: Host Key Verification

**Future Implementation**:
```python
# Load known hosts
ssh_client.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))

# Or use custom known_hosts file
ssh_client.load_host_keys('~/.webautomation/ssh/known_hosts')

# For new hosts, prompt user
ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())
```

**Security Improvement**:
- Store SSH host keys on first connection
- Verify host key matches on subsequent connections
- Alert if host key changes (potential MITM)
- Similar to standard SSH behavior

---

## 📋 Security Best Practices

### General

1. **Use Strongest Available Security**
   - Enable certificate pinning for Jira if CA bundle unavailable
   - Only disable verification if absolutely necessary
   - Document security decisions for your environment

2. **Network Security**
   - Use VPN when connecting from untrusted networks
   - Ensure AP network is isolated from public internet
   - Use firewalls to restrict access to management interfaces

3. **Credential Management**
   - All credentials are encrypted at rest using Windows DPAPI
   - Stored in: `~/.webautomation/credentials/credentials.db`
   - Database file is useless if copied (credentials encrypted with your Windows login)
   - Use strong, unique passwords
   - Install pywin32 for DPAPI support: `pip install pywin32`

4. **Regular Updates**
   - Keep application updated
   - Update dependencies regularly for security patches
   - Review security logs periodically

### For Administrators

1. **Initial Setup**
   - Review all security settings before deployment
   - Test certificate pinning in staging environment
   - Document your security configuration
   - Train users on security warnings

2. **Certificate Management**
   - Set up certificate pinning for Jira
   - Review trusted certificates quarterly
   - Remove certificates for decommissioned servers
   - Monitor for certificate change alerts

3. **Incident Response**
   - If certificate change alert appears: INVESTIGATE before trusting
   - Could indicate legitimate certificate renewal OR MITM attack
   - Check with server administrator before proceeding
   - Review recent network changes

4. **Compliance**
   - Document reasons for SSL verification bypass
   - Maintain audit log of security decisions
   - Review security configuration during audits
   - Ensure compliance with corporate security policies

---

## 🔍 Understanding Certificate Pinning

### What is Certificate Pinning?

Certificate pinning is a security technique where you "pin" (store) a certificate's fingerprint and verify it on every connection. This provides security even when you can't verify against a Certificate Authority.

### How It Works

1. **First Connection**:
   ```
   User → Connect to server
   Server → Sends certificate
   Application → Calculates SHA-256 fingerprint
   Application → Shows certificate details to user
   User → Reviews and trusts certificate
   Application → Stores fingerprint
   ```

2. **Subsequent Connections**:
   ```
   User → Connect to server
   Server → Sends certificate
   Application → Calculates fingerprint
   Application → Compares with stored fingerprint
   Match? → Allow connection
   No match? → ALERT USER - Possible MITM!
   ```

### Benefits

- ✅ Works without CA certificate bundle
- ✅ Detects certificate changes
- ✅ Simple to implement and use
- ✅ Similar to SSH's trusted model
- ✅ User has control over trust decisions

### Limitations

- ❌ Requires user to make trust decision on first use
- ❌ User must understand certificate information
- ❌ Doesn't validate certificate chain
- ❌ Requires manual updates when legitimate certificates change

---

## 🚨 Security Warnings & What They Mean

### "SSL certificate verification is DISABLED"
**Meaning**: Application is not checking if the server's certificate is valid  
**Risk**: High - Vulnerable to MITM attacks  
**Action**: Enable certificate pinning or standard verification if possible

### "Certificate Changed!"
**Meaning**: Server's certificate is different from the trusted one  
**Risk**: Critical - Could be MITM attack  
**Action**: 
1. Do NOT trust immediately
2. Contact server administrator
3. Verify certificate renewal was legitimate
4. Only trust after confirmation

### "New Certificate Detected"
**Meaning**: First time connecting to this server  
**Risk**: Medium - Could be connecting to wrong server  
**Action**:
1. Verify you entered correct URL
2. Review certificate details (issuer, subject)
3. Confirm with administrator if unsure
4. Trust only if details match expectations

---

## 📝 Certificate Fingerprint Verification

When reviewing a certificate, check these details:

### Critical Fields

1. **Common Name (CN)**: Should match your Jira hostname
   ```
   Example: jira.yourcompany.com
   ```

2. **Fingerprint**: Ask administrator for expected fingerprint
   ```
   Format: AB:CD:EF:12:34:...
   ```

3. **Valid Until**: Certificate should not be expired

4. **Issuer**: Should be your company's CA or known provider

### How to Verify Out-of-Band

1. Get certificate fingerprint from another source:
   ```bash
   # On Linux/Mac with access to Jira server:
   openssl s_client -connect jira.company.com:443 < /dev/null 2>/dev/null | \
     openssl x509 -fingerprint -sha256 -noout
   ```

2. Compare with fingerprint shown in application

3. If they match, trust the certificate

---

## 🔧 Troubleshooting

### "Unable to connect - SSL error"
**Cause**: SSL verification enabled but certificate is invalid  
**Solution**: 
- Enable certificate pinning instead
- OR disable verification (least secure)

### "Certificate changed" on every connection
**Cause**: Using load balancer that presents different certificates  
**Solution**: Contact administrator - may need different approach

### "Certificate retrieval timeout"
**Cause**: Cannot connect to server  
**Solution**: Check URL, network connection, firewall rules

---

## 📚 Additional Resources

- [Paramiko Documentation](https://docs.paramiko.org/)
- [Requests SSL Verification](https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification)
- [OWASP Certificate Pinning](https://owasp.org/www-community/controls/Certificate_and_Public_Key_Pinning)
- [Python SSL Module](https://docs.python.org/3/library/ssl.html)

---

## 📞 Support

If you have security concerns or questions:

1. Review this documentation thoroughly
2. Consult with your IT security team
3. Check application logs for details
4. Contact your system administrator

**Remember**: When in doubt, choose more security, not less.
