"""
Certificate Manager - Handles SSL/TLS certificate verification and caching
Provides certificate pinning functionality when CA bundles are not available
"""

import ssl
import socket
import hashlib
import os
import json
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse


class CertificateManager:
    """Manages SSL certificates for secure connections without CA bundles."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize certificate manager.
        
        Args:
            cache_dir: Directory to store cached certificates (default: user's app data)
        """
        if cache_dir is None:
            cache_dir = os.path.join(os.path.expanduser('~'), '.webautomation', 'certificates')
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cert_file = self.cache_dir / 'server_certificates.json'
        self.certificates = self._load_certificates()
    
    def _load_certificates(self) -> dict:
        """Load cached certificate fingerprints."""
        if self.cert_file.exists():
            try:
                with open(self.cert_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_certificates(self):
        """Save certificate fingerprints to cache."""
        try:
            with open(self.cert_file, 'w') as f:
                json.dump(self.certificates, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save certificates: {e}")
    
    def get_certificate_info(self, hostname: str, port: int = 443) -> Tuple[bool, Optional[dict], str]:
        """
        Retrieve certificate information from a server.
        
        Args:
            hostname: Server hostname
            port: Server port (default: 443)
            
        Returns:
            Tuple of (success: bool, cert_info: dict, message: str)
        """
        try:
            # Create unverified SSL context to fetch the certificate
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect and get certificate
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)
                    cert_dict = ssock.getpeercert()
                    
                    # Calculate fingerprint
                    fingerprint = hashlib.sha256(cert_der).hexdigest()
                    
                    # Extract useful info
                    cert_info = {
                        'fingerprint': fingerprint,
                        'subject': dict(x[0] for x in cert_dict.get('subject', [])),
                        'issuer': dict(x[0] for x in cert_dict.get('issuer', [])),
                        'version': cert_dict.get('version'),
                        'serialNumber': cert_dict.get('serialNumber'),
                        'notBefore': cert_dict.get('notBefore'),
                        'notAfter': cert_dict.get('notAfter'),
                        'subjectAltName': cert_dict.get('subjectAltName', [])
                    }
                    
                    return True, cert_info, "Certificate retrieved successfully"
                    
        except socket.timeout:
            return False, None, f"Connection timeout to {hostname}:{port}"
        except socket.gaierror:
            return False, None, f"Cannot resolve hostname: {hostname}"
        except ConnectionRefusedError:
            return False, None, f"Connection refused by {hostname}:{port}"
        except ssl.SSLError as e:
            return False, None, f"SSL error: {str(e)}"
        except Exception as e:
            return False, None, f"Error retrieving certificate: {str(e)}"
    
    def verify_certificate(self, hostname: str, port: int = 443) -> Tuple[bool, str, Optional[dict]]:
        """
        Verify certificate against cached fingerprint or prompt to trust.
        
        Args:
            hostname: Server hostname
            port: Server port
            
        Returns:
            Tuple of (trusted: bool, status: str, cert_info: dict)
            status can be: 'trusted', 'new', 'changed', 'error'
        """
        success, cert_info, message = self.get_certificate_info(hostname, port)
        
        if not success:
            return False, 'error', None
        
        fingerprint = cert_info['fingerprint']
        cache_key = f"{hostname}:{port}"
        
        # Check if we have a cached fingerprint
        if cache_key in self.certificates:
            cached_fingerprint = self.certificates[cache_key]['fingerprint']
            
            if fingerprint == cached_fingerprint:
                return True, 'trusted', cert_info
            else:
                # Certificate changed - potential MITM attack!
                return False, 'changed', cert_info
        else:
            # New certificate - needs to be trusted
            return False, 'new', cert_info
    
    def trust_certificate(self, hostname: str, port: int = 443, cert_info: dict = None) -> bool:
        """
        Trust a certificate by storing its fingerprint.
        
        Args:
            hostname: Server hostname
            port: Server port
            cert_info: Certificate information (if None, will fetch)
            
        Returns:
            bool: Success status
        """
        if cert_info is None:
            success, cert_info, _ = self.get_certificate_info(hostname, port)
            if not success:
                return False
        
        cache_key = f"{hostname}:{port}"
        self.certificates[cache_key] = {
            'fingerprint': cert_info['fingerprint'],
            'subject': cert_info['subject'],
            'issuer': cert_info['issuer'],
            'notAfter': cert_info['notAfter'],
            'trusted_date': str(Path(self.cert_file).stat().st_mtime if self.cert_file.exists() else 'now')
        }
        
        self._save_certificates()
        return True
    
    def remove_certificate(self, hostname: str, port: int = 443) -> bool:
        """
        Remove a trusted certificate from cache.
        
        Args:
            hostname: Server hostname
            port: Server port
            
        Returns:
            bool: True if certificate was removed
        """
        cache_key = f"{hostname}:{port}"
        if cache_key in self.certificates:
            del self.certificates[cache_key]
            self._save_certificates()
            return True
        return False
    
    def get_cached_certificate(self, hostname: str, port: int = 443) -> Optional[dict]:
        """Get cached certificate info if it exists."""
        cache_key = f"{hostname}:{port}"
        return self.certificates.get(cache_key)
    
    def format_fingerprint(self, fingerprint: str) -> str:
        """Format fingerprint in readable format (XX:XX:XX:...)."""
        return ':'.join(fingerprint[i:i+2] for i in range(0, len(fingerprint), 2))
    
    @staticmethod
    def extract_hostname_from_url(url: str) -> Tuple[str, int]:
        """
        Extract hostname and port from URL.
        
        Args:
            url: Full URL (e.g., 'https://example.com:8443/path')
            
        Returns:
            Tuple of (hostname: str, port: int)
        """
        parsed = urlparse(url)
        hostname = parsed.hostname or parsed.netloc.split(':')[0]
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        return hostname, port


def test_certificate_manager():
    """Test the certificate manager functionality."""
    manager = CertificateManager()
    
    print("Certificate Manager Test")
    print("=" * 50)
    
    # Test with a known good site
    test_host = "www.google.com"
    
    print(f"\n1. Getting certificate from {test_host}...")
    success, cert_info, message = manager.get_certificate_info(test_host)
    
    if success:
        print(f"✓ {message}")
        print(f"   Fingerprint: {manager.format_fingerprint(cert_info['fingerprint'])}")
        print(f"   Subject: {cert_info['subject'].get('commonName', 'N/A')}")
        print(f"   Issuer: {cert_info['issuer'].get('organizationName', 'N/A')}")
        print(f"   Valid until: {cert_info['notAfter']}")
    else:
        print(f"✗ {message}")
        return
    
    print(f"\n2. Verifying certificate...")
    trusted, status, _ = manager.verify_certificate(test_host)
    print(f"   Status: {status}")
    
    if status == 'new':
        print(f"\n3. Trusting certificate...")
        if manager.trust_certificate(test_host, cert_info=cert_info):
            print("   ✓ Certificate trusted")
        
        print(f"\n4. Verifying again...")
        trusted, status, _ = manager.verify_certificate(test_host)
        print(f"   Status: {status} - Trusted: {trusted}")
    
    print("\n" + "=" * 50)
    print("Test complete")


if __name__ == '__main__':
    test_certificate_manager()
