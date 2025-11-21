"""
Vusion API Helper
Simplifies making requests to Vusion APIs with proper error handling and logging.
"""

import urllib.request
import json
from typing import Dict, Optional, Any, Tuple
from vusion_api_config import VusionAPIConfig, get_vusion_config


class VusionAPIHelper:
    """Helper class for making Vusion API requests."""
    
    def __init__(self, config: VusionAPIConfig = None):
        self.config = config if config else get_vusion_config()
    
    def get_store_info(self, country: str, chain: str, store_number: str) -> Tuple[bool, Any]:
        """
        Get store information from Vusion Manager PRO.
        
        Args:
            country: Country code (NO, SE, FI, DK, IS)
            chain: Chain name (elkjop, elgiganten, gigantti, etc.)
            store_number: Store number (e.g., '4010')
        
        Returns:
            Tuple of (success: bool, data: dict or error_message: str)
        
        Example:
            success, data = helper.get_store_info('FI', 'gigantti', '4010')
            if success:
                print(f"Store name: {data['name']}")
            else:
                print(f"Error: {data}")
        """
        try:
            # Build store ID
            store_id = self.config.build_store_id(country, chain, store_number)
            
            # Get URL
            url = self.config.get_endpoint_url('vusion_pro', 'stores', storeId=store_id)
            
            # Get headers with API key
            headers = self.config.get_request_headers(country, 'vusion_pro')
            
            # Make request
            req = urllib.request.Request(url, headers=headers)
            req.get_method = lambda: 'GET'
            
            with urllib.request.urlopen(req, timeout=30) as response:
                status_code = response.getcode()
                
                if status_code == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return True, data
                else:
                    return False, f"HTTP {status_code}: {response.read().decode('utf-8')}"
        
        except urllib.error.HTTPError as e:
            error_msg = f"HTTP {e.code}: {e.reason}"
            try:
                error_body = e.read().decode('utf-8')
                error_data = json.loads(error_body)
                error_msg = f"{error_msg} - {error_data}"
            except:
                pass
            return False, error_msg
        
        except urllib.error.URLError as e:
            return False, f"Network error: {str(e.reason)}"
        
        except ValueError as e:
            return False, f"Configuration error: {str(e)}"
        
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def get_store_labels(self, country: str, chain: str, store_number: str) -> Tuple[bool, Any]:
        """
        Get labels for a store from Vusion Manager PRO.
        
        Args:
            country: Country code
            chain: Chain name
            store_number: Store number
        
        Returns:
            Tuple of (success: bool, data: dict or error_message: str)
        """
        try:
            store_id = self.config.build_store_id(country, chain, store_number)
            url = self.config.get_endpoint_url('vusion_pro', 'labels', storeId=store_id)
            headers = self.config.get_request_headers(country, 'vusion_pro')
            
            req = urllib.request.Request(url, headers=headers)
            req.get_method = lambda: 'GET'
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return True, data
                else:
                    return False, f"HTTP {response.getcode()}"
        
        except Exception as e:
            return False, str(e)
    
    def get_store_gateways(self, country: str, chain: str, store_number: str) -> Tuple[bool, Any]:
        """
        Get gateways for a store from Vusion Manager PRO.
        Note: In Vusion API, APs are called 'transmitters'. Use get_transmitter_status() for AP data.
        
        Args:
            country: Country code
            chain: Chain name
            store_number: Store number
        
        Returns:
            Tuple of (success: bool, data: dict or error_message: str)
        """
        try:
            store_id = self.config.build_store_id(country, chain, store_number)
            url = self.config.get_endpoint_url('vusion_pro', 'gateways', storeId=store_id)
            headers = self.config.get_request_headers(country, 'vusion_pro')
            
            req = urllib.request.Request(url, headers=headers)
            req.get_method = lambda: 'GET'
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return True, data
                else:
                    return False, f"HTTP {response.getcode()}"
        
        except Exception as e:
            return False, str(e)
    
    def test_connection(self, country: str, service: str = 'vusion_pro') -> Tuple[bool, str]:
        """
        Test API connection for a country/service combination.
        
        Args:
            country: Country code
            service: Service name (default: vusion_pro)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            api_key = self.config.get_api_key(country, service)
            
            if not api_key:
                return False, f"No API key configured for {country}/{service}"
            
            # Try a simple request to test connectivity
            # We'll use a dummy store ID that should return 404 but proves API key works
            url = self.config.get_endpoint_url(service, 'stores', storeId='test_store.9999')
            headers = self.config.get_request_headers(country, service)
            
            req = urllib.request.Request(url, headers=headers)
            req.get_method = lambda: 'GET'
            
            try:
                urllib.request.urlopen(req, timeout=10)
                return True, "Connection successful"
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    # 404 means API key is valid but store doesn't exist - that's OK!
                    return True, "Connection successful (API key valid)"
                elif e.code == 401:
                    return False, "Authentication failed - Invalid API key"
                elif e.code == 403:
                    return False, "Access forbidden - Check API key permissions"
                else:
                    return False, f"HTTP {e.code}: {e.reason}"
        
        except urllib.error.URLError as e:
            return False, f"Network error: {str(e.reason)}"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def make_request(self, country: str, service: str, endpoint: str, 
                    method: str = 'GET', data: Dict = None, **url_params) -> Tuple[bool, Any]:
        """
        Generic method to make any Vusion API request.
        
        Args:
            country: Country code
            service: Service name
            endpoint: Endpoint name
            method: HTTP method (GET, POST, PUT, DELETE)
            data: Request body data (for POST/PUT)
            **url_params: URL path parameters
        
        Returns:
            Tuple of (success: bool, response_data or error_message)
        
        Example:
            success, data = helper.make_request(
                'FI', 'vusion_pro', 'stores', 
                method='GET',
                storeId='gigantti_fi.4010'
            )
        """
        try:
            url = self.config.get_endpoint_url(service, endpoint, **url_params)
            headers = self.config.get_request_headers(country, service)
            
            # Prepare request body if data provided
            body = None
            if data:
                body = json.dumps(data).encode('utf-8')
                headers['Content-Length'] = str(len(body))
            
            req = urllib.request.Request(url, data=body, headers=headers)
            req.get_method = lambda: method
            
            with urllib.request.urlopen(req, timeout=30) as response:
                status_code = response.getcode()
                
                # Read response
                response_body = response.read().decode('utf-8')
                
                # Try to parse as JSON
                try:
                    response_data = json.loads(response_body) if response_body else {}
                except json.JSONDecodeError:
                    response_data = response_body
                
                if 200 <= status_code < 300:
                    return True, response_data
                else:
                    return False, f"HTTP {status_code}: {response_data}"
        
        except urllib.error.HTTPError as e:
            error_msg = f"HTTP {e.code}: {e.reason}"
            try:
                error_body = e.read().decode('utf-8')
                error_data = json.loads(error_body)
                error_msg = f"{error_msg} - {error_data}"
            except:
                pass
            return False, error_msg
        
        except Exception as e:
            return False, str(e)
    
    def get_store_data(self, country: str, store_id: str) -> Tuple[bool, Any]:
        """
        Get full store data including transmitters from Vusion Manager PRO.
        
        Args:
            country: Country code (e.g., 'LAB', 'SE', 'NO')
            store_id: Store ID (e.g., 'elkjop_se_lab.lab5')
        
        Returns:
            Tuple of (success: bool, data: dict or error_message: str)
            
            The returned data includes transmitters at:
            data['transmissionSystems']['highFrequency']['transmitters']
        
        Example:
            success, data = helper.get_store_data('LAB', 'elkjop_se_lab.lab5')
            if success:
                transmitters = data.get('transmissionSystems', {}).get('highFrequency', {}).get('transmitters', [])
        """
        try:
            url = self.config.get_endpoint_url('vusion_pro', 'stores', storeId=store_id)
            headers = self.config.get_request_headers(country, 'vusion_pro')
            
            req = urllib.request.Request(url, headers=headers)
            req.get_method = lambda: 'GET'
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return True, data
                else:
                    return False, f"HTTP {response.getcode()}"
        
        except urllib.error.HTTPError as e:
            return False, f"HTTP {e.code}: {e.reason}"
        except Exception as e:
            return False, str(e)
    
    def get_transmitter_status(self, country: str, store_id: str, transmitter_id: str = None) -> Tuple[bool, Any]:
        """
        Get transmitter (AP) status from a store.
        
        Args:
            country: Country code (e.g., 'LAB', 'SE', 'NO')
            store_id: Store ID (e.g., 'elkjop_se_lab.lab5')
            transmitter_id: Optional - specific transmitter ID to look for
        
        Returns:
            Tuple of (success: bool, data: dict or list or error_message: str)
            
            If transmitter_id provided: Returns single transmitter dict or None
            If no transmitter_id: Returns list of all transmitters
        
        Example:
            # Get all transmitters
            success, transmitters = helper.get_transmitter_status('LAB', 'elkjop_se_lab.lab5')
            
            # Get specific transmitter
            success, transmitter = helper.get_transmitter_status('LAB', 'elkjop_se_lab.lab5', '201265')
            if success and transmitter:
                print(f"Status: {transmitter['connectivity']['status']}")
        """
        # Get store data
        success, data = self.get_store_data(country, store_id)
        
        if not success:
            return False, data
        
        # Extract transmitters from nested structure
        transmitters = data.get('transmissionSystems', {}).get('highFrequency', {}).get('transmitters', [])
        
        if not transmitters:
            return True, []
        
        # If specific transmitter requested
        if transmitter_id:
            for transmitter in transmitters:
                if str(transmitter.get('id')) == str(transmitter_id):
                    return True, transmitter
            return True, None  # Not found
        
        # Return all transmitters
        return True, transmitters
    
    def check_transmitter_online(self, country: str, store_id: str, transmitter_id: str) -> Tuple[bool, Optional[bool]]:
        """
        Quick check if a specific transmitter is online.
        
        Args:
            country: Country code (e.g., 'SE')
            store_id: Store ID (e.g., 'elkjop_se_lab.lab5')
            transmitter_id: Transmitter ID (AP ID)
        
        Returns:
            Tuple of (success: bool, online: bool or None)
            - (True, True) = Successfully checked, transmitter is online
            - (True, False) = Successfully checked, transmitter is offline
            - (True, None) = Successfully checked, but transmitter not found
            - (False, None) = API error
        
        Example:
            success, online = helper.check_transmitter_online('SE', 'elkjop_se_lab.lab5', '201265')
            
            if success:
                if online is True:
                    print("🟢 Transmitter is ONLINE")
                elif online is False:
                    print("🔴 Transmitter is OFFLINE")
                else:
                    print("⚠️ Transmitter not found")
        """
        success, transmitter = self.get_transmitter_status(country, store_id, transmitter_id)
        
        if not success:
            return False, None
        
        if transmitter is None or not isinstance(transmitter, dict):
            return True, None  # Not found or wrong type
        
        # Extract online status from connectivity
        connectivity = transmitter.get('connectivity', {})
        status = connectivity.get('status', '').upper()
        
        online = status == 'ONLINE'
        return True, online


if __name__ == '__main__':
    # Example usage
    helper = VusionAPIHelper()
    
    # Test connection
    success, msg = helper.test_connection('FI', 'vusion_pro')
    print(f"Connection test: {msg}")
    
    if success:
        # Get store info
        success, data = helper.get_store_info('FI', 'gigantti', '4010')
        
        if success:
            print(f"\nStore Information:")
            print(f"  Store ID: {data.get('id')}")
            print(f"  Name: {data.get('name')}")
            print(f"  Status: {data.get('status')}")
        else:
            print(f"\nError: {data}")
