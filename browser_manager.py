"""
Browser Manager - Handles multi-AP browser automation
"""
import time
import os
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Suppress all console windows and logging on Windows
if sys.platform == 'win32':
    os.environ['WDM_LOG_LEVEL'] = '0'
    os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
    os.environ['WDM_PROGRESS_BAR'] = str(False)
    
    # Suppress Python logging for webdriver_manager
    import logging
    logging.getLogger('WDM').setLevel(logging.NOTSET)

from webdriver_manager.chrome import ChromeDriverManager


class BrowserManager:
    """Manages browser automation for multiple APs"""
    
    def __init__(self, log_callback=None, progress_callback=None, extract_xml_callback=None, 
                 handle_cato_callback=None):
        """
        Initialize the browser manager
        
        Args:
            log_callback: Function to call for logging messages
            progress_callback: Function to call for progress updates (message, percentage)
            extract_xml_callback: Function to extract values from XML/HTML
            handle_cato_callback: Function to handle Cato Networks warning
        """
        self.driver = None
        self.ap_tabs = []
        self.log_callback = log_callback or print
        self.progress_callback = progress_callback
        self.extract_xml_callback = extract_xml_callback
        self.handle_cato_callback = handle_cato_callback
        self.db = None  # Database reference for updates
    
    def log(self, message):
        """Log a message"""
        if self.log_callback:
            self.log_callback(message)
    
    def progress(self, message, percentage):
        """Update progress"""
        if self.progress_callback:
            self.progress_callback(message, percentage)
    
    def initialize_browser(self):
        """Initialize Chrome browser with appropriate options"""
        self.log("Initializing Chrome driver...")
        
        import os
        import subprocess
        import sys
        
        chrome_options = Options()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--allow-insecure-localhost')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.set_capability('acceptInsecureCerts', True)
        
        # Suppress all console windows on Windows
        creation_flags = 0
        if sys.platform == 'win32':
            # CREATE_NO_WINDOW flag to prevent console window
            creation_flags = subprocess.CREATE_NO_WINDOW
            # Also set environment to suppress webdriver_manager console output
            os.environ['WDM_LOG_LEVEL'] = '0'
            os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
        
        # Create service with hidden console window
        service = Service(
            ChromeDriverManager().install(),
            creationflags=creation_flags
        )
        
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set page load timeout to 60 seconds (increased for slower connections)
        self.driver.set_page_load_timeout(60)
        self.driver.implicitly_wait(15)
        
        # Minimize the browser window immediately
        try:
            self.driver.minimize_window()
            self.log("✓ Browser window minimized")
        except:
            self.log("⚠ Could not minimize browser window")
        
        self.log("✓ Chrome driver initialized")
    
    def open_multiple_aps(self, ap_list, status_dialog=None, is_reconnect=False):
        """
        Open browser with multiple AP tabs
        
        Args:
            ap_list: List of AP credential dictionaries
            status_dialog: Optional ConnectionStatusDialog for status updates
            is_reconnect: If True, append to existing tabs instead of replacing them
            
        Returns:
            dict: Result with status and message
        """
        try:
            total_aps = len(ap_list)
            self.log(f"=== Opening browser with {total_aps} APs ===")
            
            # Only reset ap_tabs if not reconnecting
            if not is_reconnect:
                self.ap_tabs = []
            
            # Check if browser is still valid (not closed)
            browser_valid = False
            if self.driver:
                try:
                    # Try to get current window handle to check if session is valid
                    _ = self.driver.current_window_handle
                    browser_valid = True
                except:
                    self.log("Browser session is invalid (browser was closed), reinitializing...")
                    self.driver = None
            
            # Initialize browser if not already open or if session is invalid
            if not self.driver:
                self.progress("Initializing browser...", 5)
                self.initialize_browser()
            
            # PHASE 1: Open all tabs quickly
            self.log(f"\n=== Phase 1: Opening {total_aps} tabs ===")
            self.progress("Opening browser tabs...", 10)
            
            tab_handles = []
            for index, ap in enumerate(ap_list):
                ap_id = ap.get('ap_id', 'Unknown')
                
                # For reconnect, always open new tabs
                if is_reconnect or index > 0:
                    self.driver.execute_script("window.open('');")
                    tab_handle = self.driver.window_handles[-1]
                    self.log(f"Opened new tab for AP: {ap_id}")
                else:
                    # First AP in initial connection uses current tab
                    tab_handle = self.driver.current_window_handle
                    self.log(f"Using main tab for AP: {ap_id}")
                
                tab_handles.append(tab_handle)
            
            self.log(f"✓ All {total_aps} tabs opened")
            
            # PHASE 2: Start navigation on all tabs
            self.log(f"\n=== Phase 2: Starting navigation on all tabs ===")
            self.progress("Starting navigation on all tabs...", 20)
            
            for index, (ap, tab_handle) in enumerate(zip(ap_list, tab_handles)):
                ap_id = ap.get('ap_id', 'Unknown')
                ip_address = ap.get('ip_address', '')
                username = ap.get('username_webui', '')
                password = ap.get('password_webui', '')
                
                if status_dialog:
                    status_dialog.update_status(ap_id, "connecting", "Starting navigation...")
                
                # Parse IP address and build URL
                ip_address = ip_address.strip()
                if ip_address.startswith('http://'):
                    protocol = 'http'
                    ip_address = ip_address[7:]
                elif ip_address.startswith('https://'):
                    protocol = 'https'
                    ip_address = ip_address[8:]
                else:
                    protocol = 'https'
                
                if '@' in ip_address:
                    ip_address = ip_address.split('@')[1]
                
                url = f"{protocol}://{ip_address}"
                
                try:
                    self.log(f"Starting navigation for AP {index + 1}/{total_aps}: {ap_id}")
                    
                    self.driver.switch_to.window(tab_handle)
                    
                    # Set authentication via CDP
                    self.log(f"  Setting CDP authentication for {ap_id} (user: {username})")
                    self.driver.execute_cdp_cmd('Network.enable', {})
                    import base64
                    auth_header = 'Basic ' + base64.b64encode(f'{username}:{password}'.encode()).decode()
                    self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {'Authorization': auth_header}})
                    self.log(f"  ✓ CDP authentication headers set")
                    
                    # Try to navigate with timeout handling
                    from selenium.common.exceptions import TimeoutException
                    try:
                        self.driver.get(url)
                    except TimeoutException:
                        self.log(f"⚠ Navigation timeout for {ap_id}, but continuing...")
                        # Page is still loading, we'll check the result in verification phase
                    
                    # Wait for initial page load
                    time.sleep(3)
                    
                    # Check for and handle Cato warning immediately after navigation
                    if self.handle_cato_callback:
                        try:
                            cato_detected = self.handle_cato_callback(self.driver)
                            if cato_detected:
                                self.log(f"✓ Cato warning handled for {ap_id}")
                                # Wait additional time after CATO click for page to reload
                                time.sleep(4)
                        except Exception as e:
                            self.log(f"⚠ Error checking Cato warning for {ap_id}: {str(e)}")
                    
                    self.ap_tabs.append({
                        'handle': tab_handle,
                        'ap_info': ap,
                        'ap_id': ap_id,
                        'ip_address': ip_address,
                        'url': url,
                        'status': 'loading'
                    })
                    
                except Exception as e:
                    self.log(f"✗ Failed to start navigation for {ap_id}: {str(e)}")
                    
                    # Still add to ap_tabs so we can show failure in status
                    self.ap_tabs.append({
                        'handle': tab_handle,
                        'ap_info': ap,
                        'ap_id': ap_id,
                        'ip_address': ip_address,
                        'url': url,
                        'status': 'failed',
                        'error': str(e)
                    })
                    
                    if status_dialog:
                        status_dialog.update_status(ap_id, "failed", f"Navigation error: {str(e)}")
            
            self.log(f"✓ All {total_aps} tabs are now loading")
            
            # Give pages more time to fully load (especially after CATO handling)
            self.log("Waiting for pages to fully load...")
            time.sleep(5)
            
            # PHASE 3: Verify connections
            self.log(f"\n=== Phase 3: Verifying connections ===")
            self.progress("Verifying all connections...", 60)
            
            success_count = 0
            failed_aps = []
            
            for index, tab_info in enumerate(self.ap_tabs):
                ap_id = tab_info['ap_id']
                tab_handle = tab_info['handle']
                url = tab_info['url']
                
                # Check if this tab already failed in Phase 2
                if tab_info.get('status') == 'failed':
                    failed_aps.append(tab_info.get('error', 'Navigation error'))
                    if status_dialog:
                        error_msg = tab_info.get('error', 'Connection failed')
                        status_dialog.update_status(ap_id, "failed", error_msg)
                    continue
                
                try:
                    from selenium.common.exceptions import TimeoutException
                    
                    self.driver.switch_to.window(tab_handle)
                    
                    # Get page info with timeout protection
                    try:
                        current_url = self.driver.current_url
                        page_title = self.driver.title
                        page_source = self.driver.page_source
                    except TimeoutException:
                        self.log(f"  - Timeout getting page info for {ap_id}, marking as failed")
                        tab_info['status'] = 'failed'
                        failed_aps.append(f"Timeout verifying {ap_id}")
                        if status_dialog:
                            status_dialog.update_status(ap_id, "failed", "Timeout during verification")
                        continue
                    
                    # Check for Chrome error pages
                    is_error_page = False
                    error_message = "Connection failed"
                    
                    # Common Chrome error indicators
                    error_indicators = [
                        ("ERR_CONNECTION_TIMED_OUT", "Connection timed out"),
                        ("ERR_CONNECTION_REFUSED", "Connection refused"),
                        ("ERR_NAME_NOT_RESOLVED", "Cannot resolve hostname"),
                        ("ERR_ADDRESS_UNREACHABLE", "Address unreachable"),
                        ("ERR_CONNECTION_RESET", "Connection reset"),
                        ("ERR_NETWORK_CHANGED", "Network changed"),
                        ("ERR_TIMED_OUT", "Request timed out"),
                        ("ERR_FAILED", "Request failed"),
                        ("This site can't be reached", "Site cannot be reached"),
                        ("took too long to respond", "No response from server"),
                        ("refused to connect", "Connection refused"),
                        ("is not available", "Server not available")
                    ]
                    
                    for indicator, message in error_indicators:
                        if indicator in page_source or indicator in page_title:
                            is_error_page = True
                            error_message = message
                            break
                    
                    # Also check if we're stuck on data:text/html or about:blank
                    if current_url.startswith(('data:text/html', 'about:blank', 'chrome-error://')):
                        is_error_page = True
                        error_message = "Failed to load page"
                    
                    if is_error_page:
                        tab_info['status'] = 'failed'
                        error_msg = f"Failed to connect to {ap_id}: {error_message}"
                        failed_aps.append(error_msg)
                        self.log(f"✗ {error_msg}")
                        
                        if status_dialog:
                            status_dialog.update_status(ap_id, "failed", error_message)
                    elif tab_info['ip_address'] in current_url or page_title:
                        tab_info['status'] = 'connected'
                        success_count += 1
                        self.log(f"✓ {ap_id} connected successfully")
                        
                        if status_dialog:
                            status_dialog.update_status(ap_id, "connected", f"Connected to {url}")
                    else:
                        tab_info['status'] = 'failed'
                        error_msg = f"Failed to connect to {ap_id}"
                        failed_aps.append(error_msg)
                        self.log(f"✗ {error_msg}")
                        
                        if status_dialog:
                            status_dialog.update_status(ap_id, "failed", "Connection failed")
                        
                except Exception as e:
                    tab_info['status'] = 'failed'
                    error_msg = f"Failed to verify {ap_id}: {str(e)}"
                    failed_aps.append(error_msg)
                    self.log(f"✗ {error_msg}")
                    
                    if status_dialog:
                        status_dialog.update_status(ap_id, "failed", str(e))
            
            # PHASE 4: Collect AP information
            self.log(f"\n=== Phase 4: Collecting AP information ===")
            self.progress("Collecting AP information...", 85)
            
            from credential_manager_v2 import CredentialManager
            creds_manager = CredentialManager()
            updated_count = 0
            
            for index, tab_info in enumerate(self.ap_tabs):
                if tab_info['status'] != 'connected':
                    continue
                    
                ap_id = tab_info['ap_id']
                tab_handle = tab_info['handle']
                
                try:
                    self.driver.switch_to.window(tab_handle)
                    
                    status_url = f"{tab_info['url']}/service/status.xml"
                    self.log(f"Collecting info from {ap_id}: {status_url}")
                    
                    # Navigate to status.xml (same as Quick Connect - no Cato check needed here)
                    self.driver.get(status_url)
                    time.sleep(3)
                    
                    page_source = self.driver.page_source
                    
                    if self.extract_xml_callback:
                        # Extract basic info
                        extracted_ap_id = self.extract_xml_callback(page_source, "AP ID")
                        transmitter = self.extract_xml_callback(page_source, "Transmitter")
                        store_id = self.extract_xml_callback(page_source, "Store ID")
                        ip_address = self.extract_xml_callback(page_source, "IP Address") or tab_info['ip_address']
                        
                        # Extract hardware/software info
                        serial_number = self.extract_xml_callback(page_source, "Serial Number")
                        software_version = self.extract_xml_callback(page_source, "Software Version")
                        firmware_version = self.extract_xml_callback(page_source, "Firmware Version")
                        hardware_revision = self.extract_xml_callback(page_source, "Hardware Revision")
                        build = self.extract_xml_callback(page_source, "Build")
                        configuration_mode = self.extract_xml_callback(page_source, "Configuration mode")
                        uptime = self.extract_xml_callback(page_source, "Uptime")
                        mac_address = self.extract_xml_callback(page_source, "MAC Address")
                        
                        # Extract status fields (need special handling for duplicate "Status" fields)
                        service_status = self._extract_status_field(page_source, "service")
                        communication_daemon_status = self._extract_status_field(page_source, "daemon")
                        
                        # Extract connectivity status
                        connectivity_internet = self.extract_xml_callback(page_source, "Internet")
                        connectivity_provisioning = self.extract_xml_callback(page_source, "Provisioning")
                        connectivity_ntp_server = self.extract_xml_callback(page_source, "NTP Server")
                        connectivity_apc_address = self.extract_xml_callback(page_source, "APC Address")
                        
                        self.log(f"  AP ID: {extracted_ap_id}, Type: {transmitter}, Store: {store_id}")
                        self.log(f"  Serial: {serial_number}, SW: {software_version}, FW: {firmware_version}")
                        self.log(f"  Service: {service_status}, Daemon: {communication_daemon_status}")
                        
                        if extracted_ap_id:
                            existing_ap = creds_manager.find_by_ap_id(extracted_ap_id)
                            
                            if existing_ap:
                                # Prepare update data with all fields
                                update_data = {}
                                
                                # Check and update all fields
                                fields_to_update = [
                                    ('ip_address', ip_address),
                                    ('store_id', store_id),
                                    ('type', transmitter),
                                    ('serial_number', serial_number),
                                    ('software_version', software_version),
                                    ('firmware_version', firmware_version),
                                    ('hardware_revision', hardware_revision),
                                    ('build', build),
                                    ('configuration_mode', configuration_mode),
                                    ('service_status', service_status),
                                    ('uptime', uptime),
                                    ('communication_daemon_status', communication_daemon_status),
                                    ('mac_address', mac_address),
                                    ('connectivity_internet', connectivity_internet),
                                    ('connectivity_provisioning', connectivity_provisioning),
                                    ('connectivity_ntp_server', connectivity_ntp_server),
                                    ('connectivity_apc_address', connectivity_apc_address)
                                ]
                                
                                for field_name, new_value in fields_to_update:
                                    if new_value and existing_ap.get(field_name) != new_value:
                                        update_data[field_name] = new_value
                                
                                if update_data:
                                    success, msg = creds_manager.update_credential(
                                        existing_ap.get('store_id', ''), 
                                        extracted_ap_id, 
                                        update_data
                                    )
                                    if success:
                                        updated_count += 1
                                        self.log(f"  ✓ Updated {len(update_data)} fields for AP {extracted_ap_id}")
                                    else:
                                        self.log(f"  ✗ Failed to update AP {extracted_ap_id}: {msg}")
                            else:
                                self.log(f"  AP {extracted_ap_id} not found in credentials database")
                    
                    # Navigate back to main page
                    self.driver.get(tab_info['url'])
                    
                except Exception as e:
                    self.log(f"  Error collecting info for {ap_id}: {str(e)}")
            
            if updated_count > 0:
                self.log(f"✓ Updated {updated_count} AP records in credentials database")
            
            self.progress(f"Connected to {success_count}/{total_aps} APs", 100)
            
            # Switch back to first tab
            if self.ap_tabs:
                self.driver.switch_to.window(self.ap_tabs[0]['handle'])
            
            self.log(f"\n=== Connection Summary ===")
            self.log(f"✓ Successfully connected: {success_count}")
            if failed_aps:
                self.log(f"✗ Failed connections: {len(failed_aps)}")
                for failed in failed_aps:
                    self.log(f"  - {failed}")
            
            # Update status dialog summary
            if status_dialog:
                if success_count == total_aps:
                    status_dialog.update_summary(f"✓ All {total_aps} APs connected successfully!")
                elif success_count > 0:
                    status_dialog.update_summary(f"Connected to {success_count}/{total_aps} APs. {len(failed_aps)} failed.")
                else:
                    status_dialog.update_summary(f"✗ Failed to connect to all APs")
                status_dialog.enable_close()
            
            # Build result
            result = {
                "connected_ap_ids": [tab['ap_id'] for tab in self.ap_tabs if tab['status'] == 'connected'],
                "failed_ap_ids": [tab['ap_id'] for tab in self.ap_tabs if tab['status'] == 'failed']
            }
            
            if success_count == total_aps:
                result["status"] = "success"
                result["message"] = f"Successfully connected to all {total_aps} APs"
            elif success_count > 0:
                result["status"] = "warning"
                result["message"] = f"Connected to {success_count}/{total_aps} APs. Some connections failed."
            else:
                result["status"] = "error"
                result["message"] = "Failed to connect to any APs"
            
            return result
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to open multi-AP browser: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            self.log(traceback.format_exc())
            
            if status_dialog:
                status_dialog.update_summary(f"✗ Error: {str(e)}")
                status_dialog.enable_close()
            
            return {"status": "error", "message": error_msg}
    
    def _extract_status_field(self, html_text, context):
        """Extract Status field based on context (service or daemon).
        Service status appears first, daemon status appears later.
        """
        import re
        
        if context == "service":
            # Service status is the first Status field
            pattern = r'<th>Status:</th>\s*<td[^>]*>([^<]*)</td>'
            match = re.search(pattern, html_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        elif context == "daemon":
            # Daemon status is the second Status field
            pattern = r'<th>Status:</th>\s*<td[^>]*>([^<]*)</td>'
            matches = re.findall(pattern, html_text, re.IGNORECASE)
            if len(matches) >= 2:
                return matches[1].strip()
        
        return None
    
    def collect_current_page_data(self, ap_id):
        """Collect data from the current status.xml page and update database.
        
        Args:
            ap_id: The AP ID to collect data for
            
        Returns:
            dict: Result with status and message
        """
        if not self.driver:
            return {'status': 'error', 'message': 'Browser not initialized'}
        
        if not self.extract_xml_callback:
            return {'status': 'error', 'message': 'Extract callback not configured'}
        
        if not self.db:
            return {'status': 'error', 'message': 'Database not configured'}
        
        try:
            from credential_manager_v2 import CredentialManager
            creds_manager = CredentialManager()
            
            page_source = self.driver.page_source
            
            # Check if this is a status.xml page
            if 'status.xml' not in self.driver.current_url:
                return {'status': 'error', 'message': 'Not on status.xml page'}
            
            # Extract all fields
            extracted_ap_id = self.extract_xml_callback(page_source, "AP ID")
            transmitter = self.extract_xml_callback(page_source, "Transmitter")
            store_id = self.extract_xml_callback(page_source, "Store ID")
            ip_address = self.extract_xml_callback(page_source, "IP Address")
            serial_number = self.extract_xml_callback(page_source, "Serial Number")
            software_version = self.extract_xml_callback(page_source, "Software Version")
            firmware_version = self.extract_xml_callback(page_source, "Firmware Version")
            hardware_revision = self.extract_xml_callback(page_source, "Hardware Revision")
            build = self.extract_xml_callback(page_source, "Build")
            configuration_mode = self.extract_xml_callback(page_source, "Configuration mode")
            uptime = self.extract_xml_callback(page_source, "Uptime")
            mac_address = self.extract_xml_callback(page_source, "MAC Address")
            
            # Extract status fields
            service_status = self._extract_status_field(page_source, "service")
            communication_daemon_status = self._extract_status_field(page_source, "daemon")
            
            # Extract connectivity status
            connectivity_internet = self.extract_xml_callback(page_source, "Internet")
            connectivity_provisioning = self.extract_xml_callback(page_source, "Provisioning")
            connectivity_ntp_server = self.extract_xml_callback(page_source, "NTP Server")
            connectivity_apc_address = self.extract_xml_callback(page_source, "APC Address")
            
            self.log(f"Collected data - AP ID: {extracted_ap_id}, Type: {transmitter}, Store: {store_id}")
            self.log(f"  Serial: {serial_number}, SW: {software_version}, FW: {firmware_version}")
            self.log(f"  Service: {service_status}, Daemon: {communication_daemon_status}")
            
            if extracted_ap_id:
                existing_ap = creds_manager.find_by_ap_id(extracted_ap_id)
                
                if existing_ap:
                    # Prepare update data
                    update_data = {}
                    fields_to_update = [
                        ('ip_address', ip_address),
                        ('store_id', store_id),
                        ('type', transmitter),
                        ('serial_number', serial_number),
                        ('software_version', software_version),
                        ('firmware_version', firmware_version),
                        ('hardware_revision', hardware_revision),
                        ('build', build),
                        ('configuration_mode', configuration_mode),
                        ('service_status', service_status),
                        ('uptime', uptime),
                        ('communication_daemon_status', communication_daemon_status),
                        ('mac_address', mac_address),
                        ('connectivity_internet', connectivity_internet),
                        ('connectivity_provisioning', connectivity_provisioning),
                        ('connectivity_ntp_server', connectivity_ntp_server),
                        ('connectivity_apc_address', connectivity_apc_address)
                    ]
                    
                    for field_name, new_value in fields_to_update:
                        if new_value and existing_ap.get(field_name) != new_value:
                            update_data[field_name] = new_value
                    
                    if update_data:
                        success, msg = creds_manager.update_credential(
                            existing_ap.get('store_id', ''), 
                            extracted_ap_id, 
                            update_data
                        )
                        
                        if success:
                            self.log(f"✓ Updated {len(update_data)} fields for AP {extracted_ap_id}")
                            return {'status': 'success', 'message': f'Updated {len(update_data)} fields', 'ap_id': extracted_ap_id}
                        else:
                            self.log(f"✗ Failed to update database: {msg}")
                            return {'status': 'error', 'message': msg}
                    else:
                        self.log(f"No changes detected for AP {extracted_ap_id}")
                        return {'status': 'success', 'message': 'No changes needed', 'ap_id': extracted_ap_id}
                else:
                    return {'status': 'error', 'message': f'AP {extracted_ap_id} not found in database'}
            else:
                return {'status': 'error', 'message': 'Could not extract AP ID from page'}
                
        except Exception as e:
            error_msg = f"Error collecting data: {str(e)}"
            self.log(error_msg)
            return {'status': 'error', 'message': error_msg}
    
    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.ap_tabs = []
                self.log("Browser closed")
            except Exception as e:
                self.log(f"Error closing browser: {str(e)}")
