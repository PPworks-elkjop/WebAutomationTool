"""
Vusion API Configuration Manager
Handles multiple API keys and endpoints across different countries and services.
Uses Windows DPAPI for secure credential storage.
"""

import json
from pathlib import Path
from typing import Dict, Optional, List


class VusionAPIConfig:
    """Manages Vusion API configurations with DPAPI-encrypted API keys."""
    
    # Supported countries
    COUNTRIES = ['NO', 'SE', 'FI', 'DK', 'IS', 'LAB']
    
    # API Services
    SERVICES = {
        'vusion_pro': {
            'name': 'Vusion Manager PRO',
            'base_url': 'https://api-eu.vusion.io/vusion-pro/v1',
            'endpoints': {
                'stores': '/stores/{storeId}',
                'labels': '/stores/{storeId}/labels',
                'gateways': '/stores/{storeId}/gateways',
                'templates': '/stores/{storeId}/templates',
                'transmitters': '/stores/{storeId}/transmitters',
            }
        },
        'vusion_cloud': {
            'name': 'Vusion Cloud',
            'base_url': 'https://api-eu.vusion.io/vusion-cloud/v1',
            'endpoints': {
                'devices': '/devices',
                'templates': '/templates',
            }
        },
        'vusion_retail': {
            'name': 'Vusion Retail',
            'base_url': 'https://api-eu.vusion.io/vusion-retail/v1',
            'endpoints': {
                'products': '/products',
                'prices': '/prices',
            }
        }
    }
    
    # Store ID patterns by country and chain
    STORE_PATTERNS = {
        'NO': {
            'elkjop': 'elkjop_no.{store_number}',
            'lefdal': 'lefdal_no.{store_number}',
        },
        'SE': {
            'elgiganten': 'elgiganten_se.{store_number}',
            'elkjop': 'elkjop_se_lab.{store_number}',  # Lab environment
        },
        'FI': {
            'gigantti': 'gigantti_fi.{store_number}',
        },
        'DK': {
            'elgiganten': 'elgiganten_dk.{store_number}',
        },
        'IS': {
            'elko': 'elko_is.{store_number}',
        },
        'LAB': {
            'elkjop': 'elkjop_se_lab.{store_number}',
        }
    }
    
    def __init__(self, credentials_manager=None):
        """
        Initialize Vusion API Config with DPAPI-based credential storage.
        
        Args:
            credentials_manager: CredentialsManager instance (will create if None)
        """
        if credentials_manager is None:
            from database_manager import DatabaseManager
            from credentials_manager import CredentialsManager
            db = DatabaseManager()
            self.credentials_manager = CredentialsManager(db)
        else:
            self.credentials_manager = credentials_manager
    
    def _get_service_key(self, country: str, service: str) -> str:
        """Generate credential service key for storage."""
        return f"vusion_{country}_{service}"
    
    def set_api_key(self, country: str, service: str, api_key: str) -> bool:
        """
        Set API key for a country and service (DPAPI-encrypted).
        
        Args:
            country: Country code (NO, SE, FI, DK, IS, LAB)
            service: Service name (vusion_pro, vusion_cloud, vusion_retail)
            api_key: The API subscription key
        
        Returns:
            True if successful
        """
        if country not in self.COUNTRIES:
            raise ValueError(f"Invalid country: {country}. Must be one of {self.COUNTRIES}")
        
        if service not in self.SERVICES:
            raise ValueError(f"Invalid service: {service}. Must be one of {list(self.SERVICES.keys())}")
        
        # Store using CredentialsManager with DPAPI
        service_key = self._get_service_key(country, service)
        self.credentials_manager.store_credentials(service_key, {
            'api_key': api_key,
            'country': country,
            'service': service
        })
        
        return True
    
    def get_api_key(self, country: str, service: str) -> Optional[str]:
        """
        Get DPAPI-decrypted API key for a country and service.
        
        Args:
            country: Country code
            service: Service name
        
        Returns:
            Decrypted API key or None if not found
        """
        service_key = self._get_service_key(country, service)
        credentials = self.credentials_manager.get_credentials(service_key)
        
        if credentials and 'api_key' in credentials:
            return credentials['api_key']
        
        return None
    
    def get_all_keys(self) -> Dict[str, Dict[str, str]]:
        """
        Get all API keys (DPAPI-decrypted) organized by country and service.
        
        Returns:
            Dict of {country: {service: api_key}}
        """
        result = {}
        
        # Get all Vusion-related credentials
        all_services = self.credentials_manager.get_all_services()
        
        for service_info in all_services:
            service_name = service_info['service_name']
            
            # Only process Vusion credentials
            if service_name.startswith('vusion_'):
                credentials = self.credentials_manager.get_credentials(service_name)
                
                if credentials and 'country' in credentials and 'service' in credentials:
                    country = credentials['country']
                    service = credentials['service']
                    api_key = credentials.get('api_key')
                    
                    if country not in result:
                        result[country] = {}
                    
                    result[country][service] = api_key
        
        return result
    
    def delete_api_key(self, country: str, service: str) -> bool:
        """Delete an API key from DPAPI storage."""
        service_key = self._get_service_key(country, service)
        self.credentials_manager.delete_credentials(service_key)
        return True
    
    def get_endpoint_url(self, service: str, endpoint: str, **kwargs) -> str:
        """
        Build full endpoint URL with parameters.
        
        Args:
            service: Service name (e.g., 'vusion_pro')
            endpoint: Endpoint name (e.g., 'stores')
            **kwargs: URL parameters (e.g., storeId='gigantti_fi.4010')
        
        Returns:
            Full URL string
        
        Example:
            url = config.get_endpoint_url('vusion_pro', 'stores', storeId='gigantti_fi.4010')
        """
        if service not in self.SERVICES:
            raise ValueError(f"Unknown service: {service}")
        
        service_config = self.SERVICES[service]
        
        if endpoint not in service_config['endpoints']:
            raise ValueError(f"Unknown endpoint: {endpoint} for service {service}")
        
        base_url = service_config['base_url']
        endpoint_path = service_config['endpoints'][endpoint]
        
        # Replace URL parameters
        full_path = endpoint_path.format(**kwargs)
        
        return f"{base_url}{full_path}"
    
    def build_store_id(self, country: str, chain: str, store_number: str) -> str:
        """
        Build store ID from country, chain, and store number.
        
        Args:
            country: Country code (NO, SE, FI, DK, IS)
            chain: Chain name (elkjop, elgiganten, gigantti, etc.)
            store_number: Store number (e.g., '4010')
        
        Returns:
            Store ID string (e.g., 'gigantti_fi.4010')
        
        Example:
            store_id = config.build_store_id('FI', 'gigantti', '4010')
            # Returns: 'gigantti_fi.4010'
        """
        if country not in self.STORE_PATTERNS:
            raise ValueError(f"Unknown country: {country}")
        
        if chain not in self.STORE_PATTERNS[country]:
            raise ValueError(f"Unknown chain: {chain} for country {country}")
        
        pattern = self.STORE_PATTERNS[country][chain]
        return pattern.format(store_number=store_number)
    
    def get_request_headers(self, country: str, service: str) -> Dict[str, str]:
        """
        Get request headers with API key for a specific country and service.
        
        Args:
            country: Country code
            service: Service name
        
        Returns:
            Dict of HTTP headers
        """
        api_key = self.get_api_key(country, service)
        
        if not api_key:
            raise ValueError(f"No API key configured for {country}/{service}")
        
        return {
            'Cache-Control': 'no-cache',
            'Ocp-Apim-Subscription-Key': api_key,
            'Content-Type': 'application/json',
        }
    
    def list_configured_keys(self) -> List[Dict[str, str]]:
        """
        List all configured API keys (without showing the actual keys).
        
        Returns:
            List of dicts with country, service, and status
        """
        result = []
        all_keys = self.get_all_keys()
        
        for country in all_keys:
            for service in all_keys[country]:
                if service in self.SERVICES:
                    result.append({
                        'country': country,
                        'service': service,
                        'service_name': self.SERVICES[service]['name'],
                        'configured': True
                    })
        
        return result


# Convenience function for quick access
_global_config = None

def get_vusion_config() -> VusionAPIConfig:
    """Get or create global Vusion API configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = VusionAPIConfig()
    return _global_config


if __name__ == '__main__':
    # Example usage
    config = VusionAPIConfig()
    
    # Set API keys
    config.set_api_key('FI', 'vusion_pro', 'your-api-key-here')
    config.set_api_key('NO', 'vusion_pro', 'norway-api-key-here')
    
    # Build store ID
    store_id = config.build_store_id('FI', 'gigantti', '4010')
    print(f"Store ID: {store_id}")
    
    # Get full endpoint URL
    url = config.get_endpoint_url('vusion_pro', 'stores', storeId=store_id)
    print(f"URL: {url}")
    
    # Get headers
    headers = config.get_request_headers('FI', 'vusion_pro')
    print(f"Headers: {headers}")
    
    # List configured keys
    print("\nConfigured API keys:")
    for key_info in config.list_configured_keys():
        print(f"  {key_info['country']} - {key_info['service_name']}")
