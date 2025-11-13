"""
Browser Manager - Handles multi-AP browser automation
"""
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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
        
        chrome_options = Options()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--allow-insecure-localhost')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.set_capability('acceptInsecureCerts', True)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        self.log("✓ Chrome driver initialized")
    
    def open_multiple_aps(self, ap_list, status_dialog=None):
        """
        Open browser with multiple AP tabs
        
        Args:
            ap_list: List of AP credential dictionaries
            status_dialog: Optional ConnectionStatusDialog for status updates
            
        Returns:
            dict: Result with status and message
        """
        try:
            total_aps = len(ap_list)
            self.log(f"=== Opening browser with {total_aps} APs ===")
            self.ap_tabs = []
            
            # Initialize browser if not already open
            if not self.driver:
                self.progress("Initializing browser...", 5)
                self.initialize_browser()
            
            # PHASE 1: Open all tabs quickly
            self.log(f"\n=== Phase 1: Opening {total_aps} tabs ===")
            self.progress("Opening browser tabs...", 10)
            
            tab_handles = []
            for index, ap in enumerate(ap_list):
                ap_id = ap.get('ap_id', 'Unknown')
                
                if index == 0:
                    tab_handle = self.driver.current_window_handle
                    self.log(f"Using main tab for AP: {ap_id}")
                else:
                    self.driver.execute_script("window.open('');")
                    tab_handle = self.driver.window_handles[-1]
                    self.log(f"Opened tab {index + 1} for AP: {ap_id}")
                
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
                    self.driver.execute_cdp_cmd('Network.enable', {})
                    import base64
                    auth_header = 'Basic ' + base64.b64encode(f'{username}:{password}'.encode()).decode()
                    self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {'Authorization': auth_header}})
                    
                    self.driver.get(url)
                    
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
                    if status_dialog:
                        status_dialog.update_status(ap_id, "failed", str(e))
            
            self.log(f"✓ All {total_aps} tabs are now loading")
            
            # PHASE 3: Handle Cato warnings
            self.log(f"\n=== Phase 3: Handling Cato warnings on all tabs ===")
            self.progress("Checking for Cato warnings...", 50)
            
            for index, tab_info in enumerate(self.ap_tabs):
                ap_id = tab_info['ap_id']
                tab_handle = tab_info['handle']
                
                try:
                    self.log(f"Checking tab {index + 1}/{total_aps} for Cato warning: {ap_id}")
                    self.driver.switch_to.window(tab_handle)
                    time.sleep(2)
                    
                    if self.handle_cato_callback and self.handle_cato_callback():
                        self.log(f"Handled Cato warning for {ap_id}")
                    
                except Exception as e:
                    self.log(f"Error checking Cato warning for {ap_id}: {str(e)}")
            
            self.log(f"✓ Finished checking all tabs for Cato warnings")
            
            # PHASE 4: Verify connections
            self.log(f"\n=== Phase 4: Verifying connections ===")
            self.progress("Verifying all connections...", 80)
            
            success_count = 0
            failed_aps = []
            
            for index, tab_info in enumerate(self.ap_tabs):
                ap_id = tab_info['ap_id']
                tab_handle = tab_info['handle']
                url = tab_info['url']
                
                try:
                    self.driver.switch_to.window(tab_handle)
                    current_url = self.driver.current_url
                    page_title = self.driver.title
                    
                    if tab_info['ip_address'] in current_url or page_title:
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
            
            # PHASE 5: Collect AP information
            self.log(f"\n=== Phase 5: Collecting AP information ===")
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
                    self.driver.get(status_url)
                    time.sleep(2)
                    
                    page_source = self.driver.page_source
                    
                    if self.extract_xml_callback:
                        extracted_ap_id = self.extract_xml_callback(page_source, "AP ID")
                        transmitter = self.extract_xml_callback(page_source, "Transmitter")
                        store_id = self.extract_xml_callback(page_source, "Store ID")
                        ip_address = self.extract_xml_callback(page_source, "IP Address") or tab_info['ip_address']
                        
                        self.log(f"  AP ID: {extracted_ap_id}, Type: {transmitter}, Store: {store_id}, IP: {ip_address}")
                        
                        if extracted_ap_id:
                            existing_ap = creds_manager.find_by_ap_id(extracted_ap_id)
                            
                            if existing_ap:
                                changes_made = False
                                if existing_ap.get("ip_address") != ip_address:
                                    self.log(f"  Updating IP: {existing_ap.get('ip_address')} → {ip_address}")
                                    existing_ap["ip_address"] = ip_address
                                    changes_made = True
                                if store_id and existing_ap.get("store_id") != store_id:
                                    self.log(f"  Updating Store ID: {existing_ap.get('store_id')} → {store_id}")
                                    existing_ap["store_id"] = store_id
                                    changes_made = True
                                if transmitter and existing_ap.get("type") != transmitter:
                                    self.log(f"  Updating Type: {existing_ap.get('type')} → {transmitter}")
                                    existing_ap["type"] = transmitter
                                    changes_made = True
                                
                                if changes_made:
                                    existing_ap["last_modified"] = datetime.now().isoformat()
                                    updated_count += 1
                                    self.log(f"  ✓ Updated AP {extracted_ap_id} information")
                            else:
                                self.log(f"  AP {extracted_ap_id} not found in credentials database")
                    
                    # Navigate back to main page
                    self.driver.get(tab_info['url'])
                    
                except Exception as e:
                    self.log(f"  Error collecting info for {ap_id}: {str(e)}")
            
            if updated_count > 0:
                creds_manager.save()
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
