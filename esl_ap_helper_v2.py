"""
ESL AP Helper - Web automation tool for ESL AP management (Step-by-step version)

Requirements:
    python -m pip install selenium webdriver-manager
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from pathlib import Path
import json
import time
from datetime import datetime
from datetime import datetime

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("Selenium not installed. Please run: pip install selenium webdriver-manager")
    webdriver = None

# Import custom dialogs
from connection_status_dialog import ConnectionStatusDialog

APP_NAME = "ESL AP Helper"
APP_VERSION = "0.3"
APP_RELEASE_DATE = "2025-11-12"
SETTINGS_FILE = Path.home() / f".{APP_NAME.replace(' ', '_').lower()}_settings.json"

def load_settings():
    """Load saved settings from file."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_settings(settings):
    """Save settings to file."""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
    except:
        pass

class WebAutomationWorker:
    """Worker for web automation tasks - maintains persistent browser."""
    def __init__(self, progress_callback, log_callback, parent_window=None):
        self.progress = progress_callback
        self.log = log_callback
        self.parent_window = parent_window
        self.driver = None
        self.is_logged_in = False
        self.recording = False
        self.recorded_events = []
        self.status_dialog = None
    
    def handle_cato_warning(self):
        """Check for and handle Cato Networks warning page.
        Returns True if warning was detected and handled, False otherwise.
        """
        try:
            if not self.driver:
                return False
                
            page_source = self.driver.page_source
            
            # Check if Cato Networks warning page is present
            if ('Warning - Restricted Website' in page_source or 
                'Invalid SSL/TLS certificate - IP address mismatch' in page_source):
                
                self.log("Cato Networks warning detected, clicking PROCEED button...")
                
                # Find and click the PROCEED button
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                try:
                    # Wait for and click the proceed button
                    proceed_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.proceed.prompt"))
                    )
                    proceed_btn.click()
                    self.log("✓ Clicked PROCEED button")
                    
                    # Wait 2 seconds then refresh
                    time.sleep(2)
                    self.driver.refresh()
                    self.log("✓ Page refreshed after Cato warning")
                    time.sleep(2)  # Wait for page to reload
                    
                    return True
                except Exception as e:
                    self.log(f"Could not click PROCEED button: {str(e)}")
                    return False
            
            return False
        except Exception as e:
            self.log(f"Error checking for Cato warning: {str(e)}")
            return False
        
    def open_browser_with_auth(self, ip_address, username, password):
        """Open browser and navigate with credentials embedded (bypasses HTTP Basic Auth dialog)."""
        try:
            self.log("=== Opening browser with authentication ===")
            
            # Validate inputs
            if not ip_address or ip_address.strip() == "":
                raise Exception("IP address is required. Please enter an IP address.")
            if not username or not password:
                raise Exception("Username and password are required.")
            
            self.progress("Initializing browser...", 10)
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Ignore SSL certificate errors
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--allow-insecure-localhost')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.set_capability('acceptInsecureCerts', True)
            
            self.log("Starting Chrome driver...")
            self.progress("Starting Chrome driver...", 30)
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
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
            
            # Remove any existing credentials from IP
            if '@' in ip_address:
                ip_address = ip_address.split('@')[1]
            
            url = f"{protocol}://{ip_address}"
            
            # Register authentication handler using Chrome DevTools Protocol (CDP)
            # This intercepts the HTTP Basic Auth dialog and provides credentials automatically
            self.log("Registering authentication handler via CDP...")
            self.driver.execute_cdp_cmd('Network.enable', {})
            self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {'Authorization': 'Basic ' + __import__('base64').b64encode(f'{username}:{password}'.encode()).decode()}})
            
            self.log(f"Navigating to {url}...")
            self.log("Authentication handler is registered - should handle HTTP Basic Auth automatically")
            self.progress(f"Logging in to {ip_address}...", 60)
            self.driver.get(url)
            
            # Wait longer for page to load
            self.log("Waiting for page to load...")
            time.sleep(5)
            
            # Check page source
            page_text = self.driver.page_source.lower()
            page_length = len(self.driver.page_source)
            self.log(f"Page source length: {page_length} characters")
            
            # Check for lockout
            if "too many login attempts" in page_text or "connection blocked" in page_text:
                self.log("WARNING: Account is currently locked out!")
                
                screenshot_path = Path(__file__).parent / "login_locked_out.png"
                self.driver.save_screenshot(str(screenshot_path))
                self.log(f"Lockout screenshot saved: {screenshot_path.name}")
                
                return {
                    "status": "warning",
                    "message": "Account is locked. Please wait before attempting login."
                }
            
            # Check if page is blank/minimal
            if page_length < 500:
                self.log("WARNING: Page appears blank or minimal")
                self.log("Trying to wait for JavaScript to load...")
                time.sleep(5)
                page_length = len(self.driver.page_source)
                self.log(f"Page source length after additional wait: {page_length} characters")
            
            # Save screenshot
            screenshot_path = Path(__file__).parent / "login_success.png"
            self.driver.save_screenshot(str(screenshot_path))
            self.log(f"Screenshot saved: {screenshot_path.name}")
            
            self.is_logged_in = True
            self.progress("Login complete - check browser", 100)
            self.log("✓ Login process completed")
            self.log(f"Current URL: {self.driver.current_url}")
            self.log(f"Page title: {self.driver.title}")
            
            if page_length < 500:
                self.log("NOTE: Page content is minimal - may need manual intervention")
                return {
                    "status": "warning",
                    "message": "Login completed but page appears blank. Check the browser window."
                }
            
            return {"status": "success", "message": "Successfully logged in to AP"}
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to login: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            self.log(traceback.format_exc())
            return {"status": "error", "message": error_msg}
    
    def open_browser_with_multiple_aps(self, ap_list, max_parallel=5):
        """Open browser with multiple APs in separate tabs (parallel connection).
        
        Args:
            ap_list: List of AP credential dictionaries
            max_parallel: Maximum number of simultaneous connections (default: 5)
        """
        try:
            total_aps = len(ap_list)
            self.log(f"=== Opening browser with {total_aps} APs (MAX {max_parallel} PARALLEL) ===")
            
            # Store AP info for each tab
            self.ap_tabs = []  # List of dicts: {handle, ap_info, status}
            
            # Create status dialog
            if self.parent_window:
                self.status_dialog = ConnectionStatusDialog(self.parent_window, ap_list)
            
            self.progress("Initializing browser...", 5)
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--allow-insecure-localhost')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.set_capability('acceptInsecureCerts', True)
            
            self.log("Starting Chrome driver...")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
            total_aps = len(ap_list)
            
            # PHASE 1: Open all tabs quickly
            self.log(f"\n=== Phase 1: Opening {total_aps} tabs ===")
            self.progress("Opening browser tabs...", 10)
            
            tab_handles = []
            for index, ap in enumerate(ap_list):
                ap_id = ap.get('ap_id', 'Unknown')
                
                if index == 0:
                    # First tab - use current window
                    tab_handle = self.driver.current_window_handle
                    self.log(f"Using main tab for AP: {ap_id}")
                else:
                    # Open new tab
                    self.driver.execute_script("window.open('');")
                    tab_handle = self.driver.window_handles[-1]
                    self.log(f"Opened tab {index + 1} for AP: {ap_id}")
                
                tab_handles.append(tab_handle)
            
            self.log(f"✓ All {total_aps} tabs opened")
            
            # PHASE 2: Start navigation on all tabs sequentially (don't wait for each to finish)
            self.log(f"\n=== Phase 2: Starting navigation on all tabs ===")
            self.progress("Starting navigation on all tabs...", 20)
            
            for index, (ap, tab_handle) in enumerate(zip(ap_list, tab_handles)):
                ap_id = ap.get('ap_id', 'Unknown')
                ip_address = ap.get('ip_address', '')
                username = ap.get('username_webui', '')
                password = ap.get('password_webui', '')
                
                # Update status: connecting
                if self.status_dialog:
                    self.status_dialog.update_status(ap_id, "connecting", "Starting navigation...")
                
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
                    
                    # Switch to this tab
                    self.driver.switch_to.window(tab_handle)
                    
                    # Set authentication via CDP
                    self.driver.execute_cdp_cmd('Network.enable', {})
                    auth_header = 'Basic ' + __import__('base64').b64encode(f'{username}:{password}'.encode()).decode()
                    self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {'Authorization': auth_header}})
                    
                    # Navigate to URL (start loading but don't wait)
                    self.driver.get(url)
                    
                    # Store tab info immediately
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
                    if self.status_dialog:
                        self.status_dialog.update_status(ap_id, "failed", str(e))
            
            self.log(f"✓ All {total_aps} tabs are now loading")
            
            # PHASE 3: Handle Cato warnings on all tabs sequentially
            self.log(f"\n=== Phase 3: Handling Cato warnings on all tabs ===")
            self.progress("Checking for Cato warnings...", 50)
            
            for index, tab_info in enumerate(self.ap_tabs):
                ap_id = tab_info['ap_id']
                tab_handle = tab_info['handle']
                
                try:
                    self.log(f"Checking tab {index + 1}/{total_aps} for Cato warning: {ap_id}")
                    
                    # Switch to this tab
                    self.driver.switch_to.window(tab_handle)
                    
                    # Wait 2 seconds for page to start loading
                    time.sleep(2)
                    
                    # Check for and handle Cato warning
                    if self.handle_cato_warning():
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
                    # Switch to tab
                    self.driver.switch_to.window(tab_handle)
                    
                    # Check if we got a valid page (not an error page)
                    current_url = self.driver.current_url
                    page_title = self.driver.title
                    
                    # Simple check - if we're on the URL we tried to reach, consider it successful
                    if tab_info['ip_address'] in current_url or page_title:
                        tab_info['status'] = 'connected'
                        success_count += 1
                        self.log(f"✓ {ap_id} connected successfully")
                        
                        if self.status_dialog:
                            self.status_dialog.update_status(ap_id, "connected", f"Connected to {url}")
                    else:
                        tab_info['status'] = 'failed'
                        error_msg = f"Failed to connect to {ap_id}"
                        failed_aps.append(error_msg)
                        self.log(f"✗ {error_msg}")
                        
                        if self.status_dialog:
                            self.status_dialog.update_status(ap_id, "failed", "Connection failed")
                        
                except Exception as e:
                    tab_info['status'] = 'failed'
                    error_msg = f"Failed to verify {ap_id}: {str(e)}"
                    failed_aps.append(error_msg)
                    self.log(f"✗ {error_msg}")
                    
                    if self.status_dialog:
                        self.status_dialog.update_status(ap_id, "failed", str(e))
            
            self.is_logged_in = True
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
            
            # Update status dialog summary and enable close button
            if self.status_dialog:
                if success_count == total_aps:
                    self.status_dialog.update_summary(f"✓ All {total_aps} APs connected successfully!")
                elif success_count > 0:
                    self.status_dialog.update_summary(f"Connected to {success_count}/{total_aps} APs. {len(failed_aps)} failed.")
                else:
                    self.status_dialog.update_summary(f"✗ Failed to connect to all APs")
                self.status_dialog.enable_close()
            
            # Build result message
            if success_count == total_aps:
                return {
                    "status": "success",
                    "message": f"Successfully connected to all {total_aps} APs"
                }
            elif success_count > 0:
                return {
                    "status": "warning",
                    "message": f"Connected to {success_count}/{total_aps} APs. Some connections failed."
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to connect to any APs"
                }
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to open multi-AP browser: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            self.log(traceback.format_exc())
            
            # Update status dialog on error
            if self.status_dialog:
                self.status_dialog.update_summary(f"✗ Error: {str(e)}")
                self.status_dialog.enable_close()
            
            return {"status": "error", "message": error_msg}
    
    def manage_ssh_batch(self, action):
        """Execute SSH management on all connected APs (all tabs) in parallel."""
        try:
            if not hasattr(self, 'ap_tabs') or not self.ap_tabs:
                # Single AP mode - use original method
                return self.manage_ssh(action)
            
            self.log(f"\n=== Batch SSH Management ({action}) on {len(self.ap_tabs)} APs (PARALLEL) ===")
            
            # Show status dialog if available
            if self.status_dialog:
                self.status_dialog.show_window()
                self.status_dialog.update_summary(f"Processing SSH {action} on {len(self.ap_tabs)} APs...")
            
            import threading
            import queue
            
            results_queue = queue.Queue()
            threads = []
            driver_lock = threading.Lock()
            
            def process_ap(tab_info, index):
                """Process a single AP in a thread."""
                ap_id = tab_info['ap_id']
                try:
                    # Update status dialog: processing
                    if self.status_dialog:
                        self.status_dialog.update_status(ap_id, "connecting", f"Processing SSH {action}...")
                    
                    # Thread-safe driver operations
                    with driver_lock:
                        self.log(f"Starting AP {index + 1}/{len(self.ap_tabs)}: {ap_id}")
                        
                        # Switch to this tab
                        self.driver.switch_to.window(tab_info['handle'])
                        
                        # Execute SSH operation
                        result = self.manage_ssh(action)
                        
                        if result['status'] == 'success':
                            self.log(f"✓ {ap_id}: {result['message']}")
                            # Update status dialog: success
                            if self.status_dialog:
                                self.status_dialog.update_status(ap_id, "connected", f"SSH {action}: {result['message']}")
                        else:
                            self.log(f"✗ {ap_id}: {result['message']}")
                            # Update status dialog: failed
                            if self.status_dialog:
                                self.status_dialog.update_status(ap_id, "failed", f"SSH {action}: {result['message']}")
                    
                    results_queue.put({
                        'ap_id': ap_id,
                        'result': result,
                        'success': result['status'] == 'success'
                    })
                    
                except Exception as e:
                    error_msg = f"Error processing {ap_id}: {str(e)}"
                    self.log(f"✗ {error_msg}")
                    # Update status dialog: failed
                    if self.status_dialog:
                        self.status_dialog.update_status(ap_id, "failed", f"SSH error: {str(e)}")
                    results_queue.put({
                        'ap_id': ap_id,
                        'result': {'status': 'error', 'message': str(e)},
                        'success': False
                    })
            
            # Start all threads
            self.log(f"Starting {len(self.ap_tabs)} parallel operations...")
            self.progress(f"Processing all {len(self.ap_tabs)} APs in parallel...", 10)
            
            for index, tab_info in enumerate(self.ap_tabs):
                thread = threading.Thread(target=process_ap, args=(tab_info, index))
                thread.start()
                threads.append(thread)
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            self.progress(f"All APs processed", 90)
            
            # Collect results
            results = []
            success_count = 0
            failed_count = 0
            
            while not results_queue.empty():
                result_item = results_queue.get()
                results.append(result_item)
                if result_item['success']:
                    success_count += 1
                else:
                    failed_count += 1
            
            # Build summary
            self.log(f"\n=== SSH Management Summary ===")
            self.log(f"Action: {action}")
            self.log(f"✓ Successful: {success_count}/{len(self.ap_tabs)}")
            self.log(f"✗ Failed: {failed_count}/{len(self.ap_tabs)}")
            
            # Update status dialog summary
            if self.status_dialog:
                if success_count == len(self.ap_tabs):
                    self.status_dialog.update_summary(f"✓ SSH {action} completed on all {len(self.ap_tabs)} APs!")
                elif success_count > 0:
                    self.status_dialog.update_summary(f"SSH {action} completed: {success_count} succeeded, {failed_count} failed")
                else:
                    self.status_dialog.update_summary(f"✗ SSH {action} failed on all APs")
            
            # Switch back to first tab
            self.driver.switch_to.window(self.ap_tabs[0]['handle'])
            
            if success_count == len(self.ap_tabs):
                return {
                    "status": "success",
                    "message": f"SSH {action} completed successfully on all {len(self.ap_tabs)} APs (parallel execution)",
                    "results": results
                }
            elif success_count > 0:
                return {
                    "status": "warning",
                    "message": f"SSH {action} completed on {success_count}/{len(self.ap_tabs)} APs. {failed_count} failed. (parallel execution)",
                    "results": results
                }
            else:
                return {
                    "status": "error",
                    "message": f"SSH {action} failed on all APs (parallel execution)",
                    "results": results
                }
                
        except Exception as e:
            import traceback
            error_msg = f"Batch SSH operation failed: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            self.log(traceback.format_exc())
            if self.status_dialog:
                self.status_dialog.update_summary(f"✗ Error: {str(e)}")
            return {"status": "error", "message": error_msg}
    
    def manage_provisioning_batch(self, action):
        """Execute provisioning management on all connected APs (all tabs) in parallel."""
        try:
            if not hasattr(self, 'ap_tabs') or not self.ap_tabs:
                # Single AP mode - use original method
                return self.manage_provisioning(action)
            
            self.log(f"\n=== Batch Provisioning Management ({action}) on {len(self.ap_tabs)} APs (PARALLEL) ===")
            
            # Show status dialog if available
            if self.status_dialog:
                self.status_dialog.show_window()
                self.status_dialog.update_summary(f"Processing Provisioning {action} on {len(self.ap_tabs)} APs...")
            
            import threading
            import queue
            
            results_queue = queue.Queue()
            threads = []
            driver_lock = threading.Lock()
            
            def process_ap(tab_info, index):
                """Process a single AP in a thread."""
                ap_id = tab_info['ap_id']
                try:
                    # Update status dialog: processing
                    if self.status_dialog:
                        self.status_dialog.update_status(ap_id, "connecting", f"Processing Provisioning {action}...")
                    
                    # Thread-safe driver operations
                    with driver_lock:
                        self.log(f"Starting AP {index + 1}/{len(self.ap_tabs)}: {ap_id}")
                        
                        # Switch to this tab
                        self.driver.switch_to.window(tab_info['handle'])
                        
                        # Execute provisioning operation
                        result = self.manage_provisioning(action)
                        
                        if result['status'] == 'success':
                            self.log(f"✓ {ap_id}: {result['message']}")
                            # Update status dialog: success
                            if self.status_dialog:
                                self.status_dialog.update_status(ap_id, "connected", f"Provisioning {action}: {result['message']}")
                        else:
                            self.log(f"✗ {ap_id}: {result['message']}")
                            # Update status dialog: failed
                            if self.status_dialog:
                                self.status_dialog.update_status(ap_id, "failed", f"Provisioning {action}: {result['message']}")
                    
                    results_queue.put({
                        'ap_id': ap_id,
                        'result': result,
                        'success': result['status'] == 'success'
                    })
                    
                except Exception as e:
                    error_msg = f"Error processing {ap_id}: {str(e)}"
                    self.log(f"✗ {error_msg}")
                    # Update status dialog: failed
                    if self.status_dialog:
                        self.status_dialog.update_status(ap_id, "failed", f"Provisioning error: {str(e)}")
                    results_queue.put({
                        'ap_id': ap_id,
                        'result': {'status': 'error', 'message': str(e)},
                        'success': False
                    })
            
            # Start all threads
            self.log(f"Starting {len(self.ap_tabs)} parallel operations...")
            self.progress(f"Processing all {len(self.ap_tabs)} APs in parallel...", 10)
            
            for index, tab_info in enumerate(self.ap_tabs):
                thread = threading.Thread(target=process_ap, args=(tab_info, index))
                thread.start()
                threads.append(thread)
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            self.progress(f"All APs processed", 90)
            
            # Collect results
            results = []
            success_count = 0
            failed_count = 0
            
            while not results_queue.empty():
                result_item = results_queue.get()
                results.append(result_item)
                if result_item['success']:
                    success_count += 1
                else:
                    failed_count += 1
            
            # Build summary
            self.log(f"\n=== Provisioning Management Summary ===")
            self.log(f"Action: {action}")
            self.log(f"✓ Successful: {success_count}/{len(self.ap_tabs)}")
            self.log(f"✗ Failed: {failed_count}/{len(self.ap_tabs)}")
            
            # Update status dialog summary
            if self.status_dialog:
                if success_count == len(self.ap_tabs):
                    self.status_dialog.update_summary(f"✓ Provisioning {action} completed on all {len(self.ap_tabs)} APs!")
                elif success_count > 0:
                    self.status_dialog.update_summary(f"Provisioning {action} completed: {success_count} succeeded, {failed_count} failed")
                else:
                    self.status_dialog.update_summary(f"✗ Provisioning {action} failed on all APs")
            
            # Switch back to first tab
            self.driver.switch_to.window(self.ap_tabs[0]['handle'])
            
            if success_count == len(self.ap_tabs):
                return {
                    "status": "success",
                    "message": f"Provisioning {action} completed successfully on all {len(self.ap_tabs)} APs (parallel execution)",
                    "results": results
                }
            elif success_count > 0:
                return {
                    "status": "warning",
                    "message": f"Provisioning {action} completed on {success_count}/{len(self.ap_tabs)} APs. {failed_count} failed. (parallel execution)",
                    "results": results
                }
            else:
                return {
                    "status": "error",
                    "message": f"Provisioning {action} failed on all APs (parallel execution)",
                    "results": results
                }
                
        except Exception as e:
            import traceback
            error_msg = f"Batch provisioning operation failed: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            self.log(traceback.format_exc())
            if self.status_dialog:
                self.status_dialog.update_summary(f"✗ Error: {str(e)}")
            return {"status": "error", "message": error_msg}
    
    def open_browser(self, ip_address):
        """Step 1: Open browser and navigate to IP address (WITHOUT credentials to avoid login attempt)."""
        try:
            self.log("=== Step 1: Opening browser ===")
            
            # Validate IP address
            if not ip_address or ip_address.strip() == "":
                raise Exception("IP address is required. Please enter an IP address.")
            
            self.progress("Initializing browser...", 10)
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Ignore SSL certificate errors
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--allow-insecure-localhost')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.set_capability('acceptInsecureCerts', True)
            
            self.log("Starting Chrome driver...")
            self.progress("Starting Chrome driver...", 30)
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
            # Build URL WITHOUT credentials (to avoid triggering login attempt)
            ip_address = ip_address.strip()
            if not ip_address.startswith(('http://', 'https://')):
                url = f"https://{ip_address}"
            else:
                url = ip_address
            
            self.log(f"Navigating to {url} (without credentials)...")
            self.log("NOTE: This will show the login dialog but won't submit anything yet")
            self.progress(f"Navigating to {url}...", 60)
            self.driver.get(url)
            
            time.sleep(3)
            
            # Check if we see lockout message
            page_text = self.driver.page_source.lower()
            if "too many login attempts" in page_text or "connection blocked" in page_text:
                self.log("WARNING: Account is currently locked out!")
                
                screenshot_path = Path(__file__).parent / "step1_locked_out.png"
                self.driver.save_screenshot(str(screenshot_path))
                self.log(f"Lockout screenshot saved: {screenshot_path.name}")
                
                return {
                    "status": "warning",
                    "message": "Account is locked. Please wait before attempting login."
                }
            
            # Save screenshot
            screenshot_path = Path(__file__).parent / "step1_opened.png"
            self.driver.save_screenshot(str(screenshot_path))
            self.log(f"Screenshot saved: {screenshot_path.name}")
            
            self.progress("Browser opened successfully", 100)
            self.log("Step 1 completed successfully!")
            self.log("Ready for Step 2 (Login) when account lockout has expired")
            return {"status": "success", "message": "Browser opened - ready for login"}
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to open browser: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            self.log(traceback.format_exc())
            return {"status": "error", "message": error_msg}
    
    def login(self, username, password):
        """Step 2: Submit login credentials via HTTP Basic Auth or form."""
        try:
            self.log("=== Step 2: Submitting login credentials ===")
            
            if not self.driver:
                raise Exception("Browser not opened. Please run Step 1 first.")
            
            self.progress("Analyzing login method...", 10)
            
            current_url = self.driver.current_url
            self.log(f"Current URL: {current_url}")
            
            # Check if we're facing an HTTP Basic Auth dialog (not an HTML form)
            # If title contains "Sign in" or page_source is minimal, it's likely Basic Auth
            page_source = self.driver.page_source
            self.log(f"Page source length: {len(page_source)} characters")
            
            # If page is nearly empty or we see the auth dialog, use Basic Auth
            if len(page_source) < 1000 or "401" in self.driver.title:
                self.log("Detected HTTP Basic Auth - navigating with credentials in URL...")
                self.progress("Submitting via HTTP Basic Auth...", 30)
                
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(current_url)
                
                # Build URL with credentials: https://user:pass@host/path
                netloc_with_auth = f"{username}:{password}@{parsed.netloc}"
                url_with_auth = urlunparse((
                    parsed.scheme,
                    netloc_with_auth,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment
                ))
                
                self.log(f"Navigating to URL with embedded credentials...")
                self.driver.get(url_with_auth)
                time.sleep(3)
                
                self.log("✓ Credentials submitted via HTTP Basic Auth")
                screenshot_path = Path(__file__).parent / "step2_authenticated.png"
                self.driver.save_screenshot(str(screenshot_path))
                self.log(f"Screenshot saved: {screenshot_path.name}")
                
                self.is_logged_in = True
                self.progress("Authentication successful", 100)
                
                return {
                    "status": "success",
                    "message": "Successfully authenticated via HTTP Basic Auth"
                }
            
            # Otherwise, try to find and populate HTML form fields
            try:
                self.log("Searching for HTML login form fields...")
                
                # Wait a bit for page to be ready
                time.sleep(1)
                
                # Try different common selectors for username field
                username_field = None
                username_selectors = [
                    (By.ID, "username"),
                    (By.NAME, "username"),
                    (By.ID, "user"),
                    (By.NAME, "user"),
                    (By.CSS_SELECTOR, "input[type='text']"),
                    (By.CSS_SELECTOR, "input[type='email']")
                ]
                
                for by, selector in username_selectors:
                    try:
                        username_field = self.driver.find_element(by, selector)
                        self.log(f"Found username field using {by}={selector}")
                        break
                    except:
                        continue
                
                # Try different common selectors for password field
                password_field = None
                password_selectors = [
                    (By.ID, "password"),
                    (By.NAME, "password"),
                    (By.ID, "passwd"),
                    (By.NAME, "passwd"),
                    (By.CSS_SELECTOR, "input[type='password']")
                ]
                
                for by, selector in password_selectors:
                    try:
                        password_field = self.driver.find_element(by, selector)
                        self.log(f"Found password field using {by}={selector}")
                        break
                    except:
                        continue
                
                if username_field and password_field:
                    self.log("Populating username field...")
                    username_field.clear()
                    username_field.send_keys(username)
                    
                    self.log("Populating password field...")
                    password_field.clear()
                    password_field.send_keys(password)
                    
                    self.log("✓ Credentials populated in form fields")
                    self.log("NOTE: Form NOT submitted - please review and submit manually")
                    
                    screenshot_path = Path(__file__).parent / "step2_populated.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    self.log(f"Screenshot saved: {screenshot_path.name}")
                    
                    self.is_logged_in = True
                    self.progress("Credentials populated - ready for manual submission", 100)
                    
                    return {
                        "status": "success",
                        "message": "Credentials populated. Please review and click the login button manually."
                    }
                else:
                    raise Exception("Could not find login form fields")
                    
            except Exception as form_error:
                self.log(f"No form fields found: {form_error}")
                self.log("Attempting HTTP Basic Auth instead...")
                
                # Fall back to HTTP Basic Auth
                from urllib.parse import urlparse
                parsed = urlparse(current_url)
                
                if parsed.scheme and parsed.netloc:
                    netloc = parsed.netloc.split('@')[-1]
                    url_with_auth = f"{parsed.scheme}://{username}:{password}@{netloc}{parsed.path}"
                else:
                    raise Exception("Could not parse current URL")
                
                self.log(f"Navigating with HTTP Basic Auth credentials...")
                self.progress("Submitting credentials via HTTP Basic Auth...", 50)
                self.driver.get(url_with_auth)
            
            # Wait for page to start loading
            self.log("Waiting for initial page load...")
            time.sleep(2)
            
            # Check current URL - might have redirected
            new_url = self.driver.current_url
            self.log(f"Current URL after auth attempt: {new_url}")
            
            # Wait longer for page to fully load
            self.log("Waiting for page to fully load...")
            time.sleep(5)
            
            self.progress("Checking login status...", 70)
            
            # Check if page is blank (might indicate auth failure)
            page_length = len(self.driver.page_source)
            self.log(f"Page source length: {page_length} characters")
            
            if page_length < 100:
                self.log("WARNING: Page appears to be blank or has minimal content")
                self.log("This usually means:")
                self.log("  1. Account is locked due to too many attempts")
                self.log("  2. HTTP Basic Auth failed")
                self.log("  3. Page requires JavaScript to load")
                
                # Try to refresh and see if that helps
                self.log("Attempting to refresh page...")
                self.driver.refresh()
                time.sleep(3)
                
                page_length_after_refresh = len(self.driver.page_source)
                self.log(f"Page source length after refresh: {page_length_after_refresh} characters")
                
                if page_length_after_refresh < 100:
                    self.log("ERROR: Page still blank after refresh - likely account lockout")
                    
                    screenshot_path = Path(__file__).parent / "step2_blank_page.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    self.log(f"Blank page screenshot saved: {screenshot_path.name}")
                    
                    return {
                        "status": "error",
                        "message": "Page is blank after login. Account likely locked. Wait 5-10 minutes before trying again."
                    }
            
            # Check for lockout message in page text
            page_text = self.driver.page_source.lower()
            if "too many login attempts" in page_text or "connection blocked" in page_text or "locked" in page_text:
                self.log("WARNING: Detected lockout message in page!")
                
                screenshot_path = Path(__file__).parent / "step2_locked_out.png"
                self.driver.save_screenshot(str(screenshot_path))
                self.log(f"Lockout screenshot saved: {screenshot_path.name}")
                
                return {
                    "status": "error",
                    "message": "Account locked: Too many login attempts. Please wait 5-10 minutes."
                }
            
            # Save screenshot after login
            screenshot_path = Path(__file__).parent / "step2_logged_in.png"
            self.driver.save_screenshot(str(screenshot_path))
            self.log(f"Screenshot saved: {screenshot_path.name}")
            
            # Save page source
            source_path = Path(__file__).parent / "step2_page_source.html"
            with open(source_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            self.log(f"Page source saved: {source_path.name}")
            
            # Log page title
            page_title = self.driver.title
            self.log(f"Page title: '{page_title}'")
            
            # Try to find any visible text on page
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                visible_text = body.text[:200] if body.text else "(no visible text)"
                self.log(f"Visible page text: {visible_text}")
            except Exception as e:
                self.log(f"Could not extract visible text: {e}")
            
            # Try to get browser console logs
            try:
                logs = self.driver.get_log('browser')
                if logs:
                    self.log("=== Browser Console Logs ===")
                    for entry in logs[-10:]:  # Last 10 entries
                        self.log(f"  [{entry['level']}] {entry['message']}")
            except Exception as e:
                self.log(f"Could not get browser logs: {e}")
            
            self.is_logged_in = True
            self.progress("Login completed", 100)
            self.log("Step 2 completed - Check screenshot to verify page loaded correctly")
            
            if page_length < 100:
                return {
                    "status": "warning", 
                    "message": "Login completed but page is blank - likely locked out",
                    "page_title": page_title,
                    "page_size": page_length,
                    "recommendation": "Wait 5-10 minutes before trying again"
                }
            
            return {
                "status": "success", 
                "message": "Login completed successfully",
                "page_title": page_title,
                "page_size": page_length
            }
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to login: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            self.log(traceback.format_exc())
            return {"status": "error", "message": error_msg}
    
    def check_provisioning(self):
        """Step 3: Check provisioning status."""
        try:
            self.log("=== Step 3: Checking provisioning status ===")
            
            if not self.driver:
                raise Exception("Browser not opened. Please run Step 1 first.")
            
            if not self.is_logged_in:
                raise Exception("Not logged in. Please run Step 2 first.")
            
            # Navigate to the provisioning page
            provisioning_url = "/service/config/provisioningEnabled.xml"
            current_url = self.driver.current_url
            
            # Build full URL
            from urllib.parse import urlparse
            parsed = urlparse(current_url)
            full_provisioning_url = f"{parsed.scheme}://{parsed.netloc}{provisioning_url}"
            
            self.log(f"Navigating to provisioning page: {full_provisioning_url}")
            self.progress("Navigating to provisioning page...", 20)
            self.driver.get(full_provisioning_url)
            
            time.sleep(2)  # Wait for page to load
            
            self.progress("Looking for provisioning checkbox...", 40)
            self.log("Searching for 'provisioningEnabled' checkbox...")
            
            # Find the checkbox - there are TWO inputs with name="provisioningEnabled"
            # One is type="hidden", the other is type="checkbox"
            # We need the checkbox one
            provisioning_field = None
            is_checked = None
            
            try:
                # Find specifically the checkbox type
                provisioning_field = self.driver.find_element(By.XPATH, 
                    "//input[@name='provisioningEnabled' and @type='checkbox']")
                is_checked = provisioning_field.is_selected()
                self.log(f"✅ Found provisioningEnabled checkbox!")
            except Exception as e:
                self.log(f"❌ Could not find checkbox: {e}")
            
            self.progress("Reading checkbox status...", 60)
            
            if provisioning_field is not None:
                status_text = "CHECKED (enabled)" if is_checked else "UNCHECKED (disabled)"
                self.log(f"Provisioning status: {status_text}")
                
                # Save screenshot
                screenshot_path = Path(__file__).parent / "step3_provisioning.png"
                self.driver.save_screenshot(str(screenshot_path))
                self.log(f"Screenshot saved: {screenshot_path.name}")
                
                result = {
                    "status": "success",
                    "provisioning_enabled": is_checked,
                    "message": f"Provisioning is {status_text}"
                }
            else:
                # Field not found - save page source for inspection
                self.log("WARNING: Could not find provisioningEnabled field")
                source_path = Path(__file__).parent / "step3_page_source.html"
                with open(source_path, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                self.log(f"Page source saved for inspection: {source_path.name}")
                
                screenshot_path = Path(__file__).parent / "step3_not_found.png"
                self.driver.save_screenshot(str(screenshot_path))
                self.log(f"Screenshot saved: {screenshot_path.name}")
                
                result = {
                    "status": "warning",
                    "provisioning_enabled": None,
                    "message": "Could not find provisioningEnabled field. Check page source."
                }
            
            self.progress("Provisioning check complete", 100)
            self.log("Step 3 completed!")
            return result
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to check provisioning: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            self.log(traceback.format_exc())
            return {"status": "error", "message": error_msg}
    
    def manage_provisioning(self, action):
        """Manage provisioning based on action: 'report', 'enable', or 'disable'."""
        try:
            self.log(f"=== Provisioning Management (Action: {action}) ===")
            
            if not self.driver:
                raise Exception("Browser not opened. Please login first.")
            
            # Navigate to provisioning page
            current_url = self.driver.current_url
            from urllib.parse import urlparse
            parsed = urlparse(current_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            provisioning_url = f"{base_url}/service/config/provisioningEnabled.xml"
            
            self.log(f"Navigating to: {provisioning_url}")
            self.progress("Checking provisioning status...", 20)
            self.driver.get(provisioning_url)
            time.sleep(2)
            
            # Find the checkbox
            try:
                checkboxes = self.driver.find_elements(By.NAME, "provisioningEnabled")
                provisioning_checkbox = None
                for cb in checkboxes:
                    if cb.get_attribute("type") == "checkbox":
                        provisioning_checkbox = cb
                        break
                
                if not provisioning_checkbox:
                    raise Exception("Could not find provisioning checkbox")
                
                is_enabled = provisioning_checkbox.is_selected()
                self.log(f"Current provisioning status: {'Enabled' if is_enabled else 'Disabled'}")
                
                # Action: Report only
                if action == "report":
                    self.progress("Report complete", 100)
                    screenshot_path = Path(__file__).parent / "provisioning_report.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    self.log(f"Screenshot saved: {screenshot_path.name}")
                    
                    return {
                        "status": "success",
                        "message": f"Provisioning is currently {'Enabled' if is_enabled else 'Disabled'}",
                        "provisioning_enabled": is_enabled
                    }
                
                # Action: Enable
                elif action == "enable":
                    if is_enabled:
                        self.log("Provisioning is already enabled - no action needed")
                        self.progress("Already enabled", 100)
                        return {
                            "status": "success",
                            "message": "Provisioning is already enabled",
                            "provisioning_enabled": True
                        }
                    
                    self.log("Enabling provisioning...")
                    self.progress("Enabling provisioning...", 50)
                    
                    try:
                        provisioning_checkbox.click()
                    except:
                        self.log("Normal click failed, using JavaScript...")
                        self.driver.execute_script("arguments[0].click();", provisioning_checkbox)
                    time.sleep(1)
                    
                    # Click save
                    self.log("Clicking Save button...")
                    save_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                    try:
                        save_button.click()
                    except:
                        self.log("Normal click failed on Save, using JavaScript...")
                        self.driver.execute_script("arguments[0].click();", save_button)
                    time.sleep(3)
                    
                    self.log("✓ Provisioning enabled")
                    self.progress("Provisioning enabled", 100)
                    
                    screenshot_path = Path(__file__).parent / "provisioning_enabled.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    self.log(f"Screenshot saved: {screenshot_path.name}")
                    
                    return {
                        "status": "success",
                        "message": "Provisioning has been enabled",
                        "provisioning_enabled": True
                    }
                
                # Action: Disable
                elif action == "disable":
                    if not is_enabled:
                        self.log("Provisioning is already disabled - no action needed")
                        self.progress("Already disabled", 100)
                        return {
                            "status": "success",
                            "message": "Provisioning is already disabled",
                            "provisioning_enabled": False
                        }
                    
                    self.log("Disabling provisioning...")
                    self.progress("Disabling provisioning...", 50)
                    
                    try:
                        provisioning_checkbox.click()
                    except:
                        self.log("Normal click failed, using JavaScript...")
                        self.driver.execute_script("arguments[0].click();", provisioning_checkbox)
                    time.sleep(1)
                    
                    # Click save
                    self.log("Clicking Save button...")
                    save_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                    try:
                        save_button.click()
                    except:
                        self.log("Normal click failed on Save, using JavaScript...")
                        self.driver.execute_script("arguments[0].click();", save_button)
                    time.sleep(3)
                    
                    self.log("✓ Provisioning disabled")
                    self.progress("Provisioning disabled", 100)
                    
                    screenshot_path = Path(__file__).parent / "provisioning_disabled.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    self.log(f"Screenshot saved: {screenshot_path.name}")
                    
                    return {
                        "status": "success",
                        "message": "Provisioning has been disabled",
                        "provisioning_enabled": False
                    }
                
                else:
                    raise Exception(f"Unknown action: {action}")
                    
            except Exception as e:
                self.log(f"Error accessing provisioning: {e}")
                return {"status": "error", "message": f"Failed to access provisioning: {e}"}
                
        except Exception as e:
            import traceback
            error_msg = f"Failed to manage provisioning: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            self.log(traceback.format_exc())
            return {"status": "error", "message": error_msg}
    
    def enable_ssh_with_provisioning(self):
        """Enable SSH by managing provisioning state."""
        try:
            self.log("=== SSH Enablement Workflow ===")
            
            if not self.driver:
                raise Exception("Browser not opened. Please login first.")
            
            # Step 1: Check SSH status
            self.log("Step 1: Checking current SSH status...")
            self.progress("Checking SSH status...", 10)
            
            current_url = self.driver.current_url
            from urllib.parse import urlparse
            parsed = urlparse(current_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            ssh_url = f"{base_url}/service/config/ssh.xml"
            self.log(f"Navigating to: {ssh_url}")
            self.driver.get(ssh_url)
            time.sleep(2)
            
            # Check if SSH is already enabled
            try:
                # Find the checkbox (not the hidden input)
                ssh_checkboxes = self.driver.find_elements(By.NAME, "enabled")
                ssh_checkbox = None
                for cb in ssh_checkboxes:
                    if cb.get_attribute("type") == "checkbox":
                        ssh_checkbox = cb
                        break
                
                if not ssh_checkbox:
                    raise Exception("Could not find SSH checkbox (only found hidden input)")
                
                is_ssh_enabled = ssh_checkbox.is_selected()
                is_disabled = ssh_checkbox.get_attribute("disabled")
                
                self.log(f"SSH currently enabled: {is_ssh_enabled}")
                self.log(f"SSH checkbox disabled: {is_disabled is not None}")
                
                if is_ssh_enabled:
                    self.log("✓ SSH is already enabled - workflow complete!")
                    self.progress("SSH already enabled", 100)
                    return {"status": "success", "message": "SSH is already enabled"}
                
                # Check if SSH checkbox is accessible (not disabled)
                if is_disabled:
                    self.log("SSH checkbox is disabled - provisioning must be disabled first")
                    needs_provisioning_disable = True
                else:
                    self.log("✓ SSH checkbox is accessible - can enable directly!")
                    needs_provisioning_disable = False
                    
            except Exception as e:
                self.log(f"Could not find SSH checkbox: {e}")
                return {"status": "error", "message": "Could not access SSH configuration page"}
            
            # Step 2: Disable provisioning (only if needed)
            if needs_provisioning_disable:
                self.log("\nStep 2: Disabling provisioning...")
                self.progress("Disabling provisioning...", 20)
                
                provisioning_url = f"{base_url}/service/config/provisioningEnabled.xml"
                self.log(f"Navigating to: {provisioning_url}")
                self.driver.get(provisioning_url)
                time.sleep(2)
                
                try:
                    # Find and uncheck provisioning checkbox
                    checkboxes = self.driver.find_elements(By.NAME, "provisioningEnabled")
                    provisioning_checkbox = None
                    for cb in checkboxes:
                        if cb.get_attribute("type") == "checkbox":
                            provisioning_checkbox = cb
                            break
                    
                    if not provisioning_checkbox:
                        raise Exception("Could not find provisioning checkbox")
                    
                    if provisioning_checkbox.is_selected():
                        self.log("Unchecking provisioning checkbox...")
                        try:
                            provisioning_checkbox.click()
                        except:
                            self.log("Normal click failed, using JavaScript...")
                            self.driver.execute_script("arguments[0].click();", provisioning_checkbox)
                        time.sleep(1)
                    else:
                        self.log("Provisioning already unchecked")
                    
                    # Click save button (it's a submit button with value="Save")
                    self.log("Clicking Save button...")
                    save_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                    try:
                        save_button.click()
                    except:
                        self.log("Normal click failed on Save, using JavaScript...")
                        self.driver.execute_script("arguments[0].click();", save_button)
                    time.sleep(3)
                    
                    self.log("✓ Provisioning disabled")
                    
                except Exception as e:
                    self.log(f"Error disabling provisioning: {e}")
                    return {"status": "error", "message": f"Failed to disable provisioning: {e}"}
            else:
                self.log("\nStep 2: Skipping provisioning disable (not needed)")
                self.progress("SSH form is accessible...", 30)
            
            # Step 3: Enable SSH
            step_num = "3" if needs_provisioning_disable else "2"
            self.log(f"\nStep {step_num}: Enabling SSH...")
            self.progress("Enabling SSH...", 50)
            
            ssh_url = f"{base_url}/service/config/ssh.xml"
            self.log(f"Navigating to: {ssh_url}")
            self.driver.get(ssh_url)
            time.sleep(2)
            
            try:
                # Wait for checkbox to be ready
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                self.log("Waiting for SSH checkbox to be ready...")
                # There are TWO inputs with name="enabled" - one hidden, one checkbox
                # We need to find specifically the checkbox type
                ssh_checkboxes = self.driver.find_elements(By.NAME, "enabled")
                ssh_checkbox = None
                for cb in ssh_checkboxes:
                    if cb.get_attribute("type") == "checkbox":
                        ssh_checkbox = cb
                        break
                
                if not ssh_checkbox:
                    raise Exception("Could not find SSH checkbox (only found hidden input)")
                
                if not ssh_checkbox.is_selected():
                    self.log("Checking SSH checkbox...")
                    try:
                        # Try normal click first
                        ssh_checkbox.click()
                    except:
                        # If normal click fails, use JavaScript
                        self.log("Normal click failed, using JavaScript...")
                        self.driver.execute_script("arguments[0].click();", ssh_checkbox)
                    time.sleep(1)
                else:
                    self.log("SSH checkbox already checked")
                
                # Click save button
                self.log("Clicking Save button...")
                save_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                try:
                    save_button.click()
                except:
                    self.log("Normal click failed on Save, using JavaScript...")
                    self.driver.execute_script("arguments[0].click();", save_button)
                time.sleep(3)
                
                self.log("✓ SSH enabled")
                
            except Exception as e:
                self.log(f"Error enabling SSH: {e}")
                return {"status": "error", "message": f"Failed to enable SSH: {e}"}
            
            # Step 4: Re-enable provisioning (only if we disabled it)
            if needs_provisioning_disable:
                self.log("\nStep 4: Re-enabling provisioning...")
                self.progress("Re-enabling provisioning...", 75)
                
                provisioning_url = f"{base_url}/service/config/provisioningEnabled.xml"
                self.log(f"Navigating to: {provisioning_url}")
                self.driver.get(provisioning_url)
                time.sleep(2)
                
                try:
                    # Find and check provisioning checkbox
                    checkboxes = self.driver.find_elements(By.NAME, "provisioningEnabled")
                    provisioning_checkbox = None
                    for cb in checkboxes:
                        if cb.get_attribute("type") == "checkbox":
                            provisioning_checkbox = cb
                            break
                    
                    if not provisioning_checkbox:
                        raise Exception("Could not find provisioning checkbox")
                    
                    if not provisioning_checkbox.is_selected():
                        self.log("Checking provisioning checkbox...")
                        try:
                            provisioning_checkbox.click()
                        except:
                            self.log("Normal click failed, using JavaScript...")
                            self.driver.execute_script("arguments[0].click();", provisioning_checkbox)
                        time.sleep(1)
                    else:
                        self.log("Provisioning already checked")
                    
                    # Click save button
                    self.log("Clicking Save button...")
                    save_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                    try:
                        save_button.click()
                    except:
                        self.log("Normal click failed on Save, using JavaScript...")
                        self.driver.execute_script("arguments[0].click();", save_button)
                    time.sleep(3)
                    
                    self.log("✓ Provisioning re-enabled")
                        
                except Exception as e:
                    self.log(f"Error re-enabling provisioning: {e}")
                    return {"status": "warning", "message": f"SSH enabled but failed to re-enable provisioning: {e}"}
                
                # Step 5: Verify provisioning is enabled
                self.log("\nStep 5: Verifying provisioning status...")
                self.progress("Verifying provisioning...", 90)
                
                time.sleep(1)
                self.driver.get(provisioning_url)
                time.sleep(2)
                
                try:
                    checkboxes = self.driver.find_elements(By.NAME, "provisioningEnabled")
                    provisioning_checkbox = None
                    for cb in checkboxes:
                        if cb.get_attribute("type") == "checkbox":
                            provisioning_checkbox = cb
                            break
                    
                    if provisioning_checkbox and provisioning_checkbox.is_selected():
                        self.log("✓ Provisioning is enabled - verification successful!")
                        self.progress("SSH enablement complete!", 100)
                        
                        # Save screenshot
                        screenshot_path = Path(__file__).parent / "ssh_enabled_complete.png"
                        self.driver.save_screenshot(str(screenshot_path))
                        self.log(f"Screenshot saved: {screenshot_path.name}")
                        
                        return {
                            "status": "success",
                            "message": "SSH successfully enabled and provisioning restored"
                        }
                    else:
                        self.log("WARNING: Provisioning checkbox is not checked")
                        return {
                            "status": "warning",
                            "message": "SSH enabled but provisioning verification failed"
                        }
                        
                except Exception as e:
                    self.log(f"Error verifying provisioning: {e}")
                    return {
                        "status": "warning",
                        "message": "SSH enabled but could not verify provisioning status"
                    }
            else:
                # Provisioning was already disabled, just complete
                self.log("\n✓ SSH enabled successfully!")
                self.progress("SSH enablement complete!", 100)
                
                # Save screenshot
                screenshot_path = Path(__file__).parent / "ssh_enabled_complete.png"
                self.driver.save_screenshot(str(screenshot_path))
                self.log(f"Screenshot saved: {screenshot_path.name}")
                
                return {
                    "status": "success",
                    "message": "SSH successfully enabled"
                }
            
        except Exception as e:
            import traceback
            error_msg = f"SSH enablement workflow failed: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            self.log(traceback.format_exc())
            return {"status": "error", "message": error_msg}
    
    def manage_ssh(self, action):
        """Manage SSH based on action: 'report', 'enable', or 'disable'."""
        try:
            self.log(f"=== SSH Management (Action: {action}) ===")
            
            if not self.driver:
                raise Exception("Browser not opened. Please login first.")
            
            # Navigate to SSH page
            current_url = self.driver.current_url
            from urllib.parse import urlparse
            parsed = urlparse(current_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            ssh_url = f"{base_url}/service/config/ssh.xml"
            
            self.log(f"Navigating to: {ssh_url}")
            self.progress("Checking SSH status...", 20)
            self.driver.get(ssh_url)
            time.sleep(2)
            
            # Find the SSH checkbox
            try:
                ssh_checkboxes = self.driver.find_elements(By.NAME, "enabled")
                ssh_checkbox = None
                for cb in ssh_checkboxes:
                    if cb.get_attribute("type") == "checkbox":
                        ssh_checkbox = cb
                        break
                
                if not ssh_checkbox:
                    raise Exception("Could not find SSH checkbox")
                
                is_ssh_enabled = ssh_checkbox.is_selected()
                is_disabled = ssh_checkbox.get_attribute("disabled")
                
                self.log(f"Current SSH status: {'Enabled' if is_ssh_enabled else 'Disabled'}")
                self.log(f"SSH checkbox disabled: {is_disabled is not None}")
                
                # Action: Report only
                if action == "report":
                    self.progress("Report complete", 100)
                    screenshot_path = Path(__file__).parent / "ssh_report.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    self.log(f"Screenshot saved: {screenshot_path.name}")
                    
                    status_msg = f"SSH is currently {'Enabled' if is_ssh_enabled else 'Disabled'}"
                    if is_disabled:
                        status_msg += " (SSH form is disabled - provisioning may be enabled)"
                    
                    return {
                        "status": "success",
                        "message": status_msg,
                        "ssh_enabled": is_ssh_enabled
                    }
                
                # Action: Enable SSH
                elif action == "enable":
                    if is_ssh_enabled:
                        self.log("SSH is already enabled - no action needed")
                        self.progress("Already enabled", 100)
                        return {
                            "status": "success",
                            "message": "SSH is already enabled",
                            "ssh_enabled": True
                        }
                    
                    self.log("SSH needs to be enabled...")
                    
                    # Check if we need to disable provisioning first
                    if is_disabled:
                        self.log("SSH checkbox is disabled - need to disable provisioning first")
                        needs_provisioning_disable = True
                    else:
                        self.log("SSH checkbox is accessible")
                        needs_provisioning_disable = False
                    
                    # Disable provisioning if needed
                    if needs_provisioning_disable:
                        self.log("\nDisabling provisioning...")
                        self.progress("Disabling provisioning...", 30)
                        
                        provisioning_url = f"{base_url}/service/config/provisioningEnabled.xml"
                        self.driver.get(provisioning_url)
                        time.sleep(2)
                        
                        checkboxes = self.driver.find_elements(By.NAME, "provisioningEnabled")
                        provisioning_checkbox = None
                        for cb in checkboxes:
                            if cb.get_attribute("type") == "checkbox":
                                provisioning_checkbox = cb
                                break
                        
                        if provisioning_checkbox and provisioning_checkbox.is_selected():
                            self.log("Unchecking provisioning...")
                            try:
                                provisioning_checkbox.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", provisioning_checkbox)
                            time.sleep(1)
                            
                            save_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                            try:
                                save_button.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", save_button)
                            time.sleep(3)
                            self.log("✓ Provisioning disabled")
                    
                    # Enable SSH
                    self.log("\nEnabling SSH...")
                    self.progress("Enabling SSH...", 50)
                    self.driver.get(ssh_url)
                    time.sleep(2)
                    
                    ssh_checkboxes = self.driver.find_elements(By.NAME, "enabled")
                    ssh_checkbox = None
                    for cb in ssh_checkboxes:
                        if cb.get_attribute("type") == "checkbox":
                            ssh_checkbox = cb
                            break
                    
                    if not ssh_checkbox.is_selected():
                        self.log("Checking SSH checkbox...")
                        try:
                            ssh_checkbox.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", ssh_checkbox)
                        time.sleep(1)
                    
                    save_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                    try:
                        save_button.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", save_button)
                    time.sleep(3)
                    self.log("✓ SSH enabled")
                    
                    # Re-enable provisioning if we disabled it
                    if needs_provisioning_disable:
                        self.log("\nRe-enabling provisioning...")
                        self.progress("Re-enabling provisioning...", 75)
                        
                        provisioning_url = f"{base_url}/service/config/provisioningEnabled.xml"
                        self.driver.get(provisioning_url)
                        time.sleep(2)
                        
                        checkboxes = self.driver.find_elements(By.NAME, "provisioningEnabled")
                        provisioning_checkbox = None
                        for cb in checkboxes:
                            if cb.get_attribute("type") == "checkbox":
                                provisioning_checkbox = cb
                                break
                        
                        if provisioning_checkbox and not provisioning_checkbox.is_selected():
                            self.log("Checking provisioning...")
                            try:
                                provisioning_checkbox.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", provisioning_checkbox)
                            time.sleep(1)
                            
                            save_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                            try:
                                save_button.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", save_button)
                            time.sleep(3)
                            self.log("✓ Provisioning re-enabled")
                    
                    self.progress("SSH enabled successfully", 100)
                    screenshot_path = Path(__file__).parent / "ssh_enabled.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    self.log(f"Screenshot saved: {screenshot_path.name}")
                    
                    return {
                        "status": "success",
                        "message": "SSH has been enabled" + (" and provisioning restored" if needs_provisioning_disable else ""),
                        "ssh_enabled": True
                    }
                
                # Action: Disable SSH
                elif action == "disable":
                    if not is_ssh_enabled:
                        self.log("SSH is already disabled - no action needed")
                        self.progress("Already disabled", 100)
                        return {
                            "status": "success",
                            "message": "SSH is already disabled",
                            "ssh_enabled": False
                        }
                    
                    self.log("SSH needs to be disabled...")
                    
                    # Check if we need to disable provisioning first
                    if is_disabled:
                        self.log("SSH checkbox is disabled - need to disable provisioning first")
                        needs_provisioning_disable = True
                    else:
                        self.log("SSH checkbox is accessible")
                        needs_provisioning_disable = False
                    
                    # Disable provisioning if needed
                    if needs_provisioning_disable:
                        self.log("\nDisabling provisioning...")
                        self.progress("Disabling provisioning...", 30)
                        
                        provisioning_url = f"{base_url}/service/config/provisioningEnabled.xml"
                        self.driver.get(provisioning_url)
                        time.sleep(2)
                        
                        checkboxes = self.driver.find_elements(By.NAME, "provisioningEnabled")
                        provisioning_checkbox = None
                        for cb in checkboxes:
                            if cb.get_attribute("type") == "checkbox":
                                provisioning_checkbox = cb
                                break
                        
                        if provisioning_checkbox and provisioning_checkbox.is_selected():
                            self.log("Unchecking provisioning...")
                            try:
                                provisioning_checkbox.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", provisioning_checkbox)
                            time.sleep(1)
                            
                            save_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                            try:
                                save_button.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", save_button)
                            time.sleep(3)
                            self.log("✓ Provisioning disabled")
                    
                    # Disable SSH
                    self.log("\nDisabling SSH...")
                    self.progress("Disabling SSH...", 50)
                    self.driver.get(ssh_url)
                    time.sleep(2)
                    
                    ssh_checkboxes = self.driver.find_elements(By.NAME, "enabled")
                    ssh_checkbox = None
                    for cb in ssh_checkboxes:
                        if cb.get_attribute("type") == "checkbox":
                            ssh_checkbox = cb
                            break
                    
                    if ssh_checkbox.is_selected():
                        self.log("Unchecking SSH checkbox...")
                        try:
                            ssh_checkbox.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", ssh_checkbox)
                        time.sleep(1)
                    
                    save_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                    try:
                        save_button.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", save_button)
                    time.sleep(3)
                    self.log("✓ SSH disabled")
                    
                    # Re-enable provisioning if we disabled it
                    if needs_provisioning_disable:
                        self.log("\nRe-enabling provisioning...")
                        self.progress("Re-enabling provisioning...", 75)
                        
                        provisioning_url = f"{base_url}/service/config/provisioningEnabled.xml"
                        self.driver.get(provisioning_url)
                        time.sleep(2)
                        
                        checkboxes = self.driver.find_elements(By.NAME, "provisioningEnabled")
                        provisioning_checkbox = None
                        for cb in checkboxes:
                            if cb.get_attribute("type") == "checkbox":
                                provisioning_checkbox = cb
                                break
                        
                        if provisioning_checkbox and not provisioning_checkbox.is_selected():
                            self.log("Checking provisioning...")
                            try:
                                provisioning_checkbox.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", provisioning_checkbox)
                            time.sleep(1)
                            
                            save_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                            try:
                                save_button.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", save_button)
                            time.sleep(3)
                            self.log("✓ Provisioning re-enabled")
                    
                    self.progress("SSH disabled successfully", 100)
                    screenshot_path = Path(__file__).parent / "ssh_disabled.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    self.log(f"Screenshot saved: {screenshot_path.name}")
                    
                    return {
                        "status": "success",
                        "message": "SSH has been disabled" + (" and provisioning restored" if needs_provisioning_disable else ""),
                        "ssh_enabled": False
                    }
                
                else:
                    raise Exception(f"Unknown action: {action}")
                    
            except Exception as e:
                self.log(f"Error accessing SSH: {e}")
                return {"status": "error", "message": f"Failed to access SSH: {e}"}
                
        except Exception as e:
            import traceback
            error_msg = f"Failed to manage SSH: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            self.log(traceback.format_exc())
            return {"status": "error", "message": error_msg}
    
    def start_recording(self):
        """Start recording browser activity."""
        try:
            if not self.driver:
                raise Exception("Browser not opened. Please run Step 1 first.")
            
            self.log("=== Starting Activity Recording ===")
            self.recording = True
            self.recorded_events = []
            
            # Record initial state
            self._record_event("RECORDING_STARTED", {
                "url": self.driver.current_url,
                "title": self.driver.title,
                "timestamp": time.strftime("%H:%M:%S")
            })
            
            self.log("Recording started - perform your actions in the browser")
            self.log("The system will capture:")
            self.log("  - URL changes and redirects")
            self.log("  - Page titles")
            self.log("  - Network requests")
            self.log("  - Console logs")
            self.log("")
            self.log("Click 'Stop Recording' when done")
            
            # Start monitoring thread
            import threading
            self.monitor_thread = threading.Thread(target=self._monitor_browser, daemon=True)
            self.monitor_thread.start()
            
            return {"status": "success", "message": "Recording started - perform your actions"}
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to start recording: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            self.log(traceback.format_exc())
            return {"status": "error", "message": error_msg}
    
    def stop_recording(self):
        """Stop recording and save results."""
        try:
            if not self.recording:
                return {"status": "info", "message": "No recording in progress"}
            
            self.log("=== Stopping Recording ===")
            self.recording = False
            
            # Wait a moment for monitor thread to finish
            time.sleep(1)
            
            # Record final state
            self._record_event("RECORDING_STOPPED", {
                "url": self.driver.current_url,
                "title": self.driver.title,
                "timestamp": time.strftime("%H:%M:%S")
            })
            
            # Save recording to file
            recording_path = Path(__file__).parent / f"recording_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(recording_path, 'w', encoding='utf-8') as f:
                json.dump(self.recorded_events, f, indent=2)
            
            self.log(f"Recording saved: {recording_path.name}")
            self.log(f"Total events captured: {len(self.recorded_events)}")
            
            # Create summary
            summary = self._create_recording_summary()
            
            return {
                "status": "success",
                "message": f"Recording stopped - {len(self.recorded_events)} events captured",
                "file": str(recording_path.name),
                "summary": summary
            }
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to stop recording: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            self.log(traceback.format_exc())
            return {"status": "error", "message": error_msg}
    
    def _record_event(self, event_type, data):
        """Record an event."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        event = {
            "timestamp": timestamp,
            "type": event_type,
            "data": data
        }
        self.recorded_events.append(event)
        
        # Also log it
        if event_type == "URL_CHANGE":
            self.log(f"📍 URL Changed: {data.get('url', 'N/A')}")
        elif event_type == "TITLE_CHANGE":
            self.log(f"📄 Title: {data.get('title', 'N/A')}")
        elif event_type == "CONSOLE_LOG":
            self.log(f"🖥️ Console [{data.get('level', 'INFO')}]: {data.get('message', 'N/A')}")
    
    def _monitor_browser(self):
        """Monitor browser for changes while recording."""
        last_url = self.driver.current_url
        last_title = self.driver.title
        
        while self.recording:
            try:
                time.sleep(0.5)  # Check every 500ms
                
                # Check for URL changes
                current_url = self.driver.current_url
                if current_url != last_url:
                    self._record_event("URL_CHANGE", {
                        "from": last_url,
                        "to": current_url
                    })
                    last_url = current_url
                
                # Check for title changes
                current_title = self.driver.title
                if current_title != last_title:
                    self._record_event("TITLE_CHANGE", {
                        "from": last_title,
                        "to": current_title
                    })
                    last_title = current_title
                
                # Get browser console logs
                try:
                    logs = self.driver.get_log('browser')
                    for entry in logs:
                        self._record_event("CONSOLE_LOG", {
                            "level": entry['level'],
                            "message": entry['message'],
                            "source": entry.get('source', 'unknown')
                        })
                except:
                    pass  # Console logs might not be available
                
            except Exception as e:
                if self.recording:
                    self.log(f"Monitor error: {e}")
                break
    
    def _create_recording_summary(self):
        """Create a summary of the recording."""
        summary = {
            "total_events": len(self.recorded_events),
            "url_changes": 0,
            "redirects": [],
            "console_errors": 0,
            "console_warnings": 0
        }
        
        for event in self.recorded_events:
            if event["type"] == "URL_CHANGE":
                summary["url_changes"] += 1
                summary["redirects"].append({
                    "from": event["data"].get("from", ""),
                    "to": event["data"].get("to", ""),
                    "time": event["timestamp"]
                })
            elif event["type"] == "CONSOLE_LOG":
                level = event["data"].get("level", "")
                if level == "SEVERE" or "error" in level.lower():
                    summary["console_errors"] += 1
                elif level == "WARNING" or "warn" in level.lower():
                    summary["console_warnings"] += 1
        
        return summary
    
    def close(self):
        """Close the browser."""
        try:
            if self.driver:
                self.log("Closing browser...")
                self.recording = False  # Stop any recording
                self.driver.quit()
                self.driver = None
                self.is_logged_in = False
                self.log("Browser closed successfully")
                return {"status": "success", "message": "Browser closed"}
            else:
                return {"status": "info", "message": "No browser to close"}
        except Exception as e:
            error_msg = f"Error closing browser: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            return {"status": "error", "message": error_msg}

class App:
    def __init__(self, root, current_user):
        self.root = root
        self.current_user = current_user
        self.settings = load_settings()
        self.worker = WebAutomationWorker(self._update_progress, self._log_activity, root)
        
        # Configure window
        w, h = self.settings.get("window_size", [800, 700])
        root.geometry(f"{w}x{h}")
        root.title(f"{APP_NAME} v{APP_VERSION} - {current_user['full_name']} ({current_user['role']})")
        
        self._build_ui()
        root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _build_ui(self):
        # Configure modern style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Modern color scheme
        bg_color = "#F5F5F5"
        frame_bg = "#FFFFFF"
        accent_color = "#28A745"
        
        self.root.configure(bg=bg_color)
        
        # Configure ttk styles
        style.configure("Modern.TFrame", background=frame_bg)
        style.configure("Modern.TLabelframe", background=frame_bg, borderwidth=0, relief="flat")
        style.configure("Modern.TLabelframe.Label", background=frame_bg, foreground="#333333", font=("Segoe UI", 12, "bold"))
        style.configure("Modern.TLabel", background=frame_bg, foreground="#555555", font=("Segoe UI", 10))
        style.configure("Modern.TEntry", fieldbackground="white", borderwidth=1, padding=8)
        style.configure("Modern.TButton", background=accent_color, foreground="white", borderwidth=0, font=("Segoe UI", 10), padding=6)
        style.map("Modern.TButton", background=[("active", "#218838")])
        
        main_frame = ttk.Frame(self.root, padding=15, style="Modern.TFrame")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        # Quick Connect Frame
        conn_frame = ttk.LabelFrame(main_frame, text="Quick Connect", padding=15, style="Modern.TLabelframe")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Create a style for bordered entries
        style.configure("Bordered.TEntry", relief="solid", borderwidth=1, padding=5)
        
        # IP Address
        ttk.Label(conn_frame, text="IP Address:", style="Modern.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.ip_var = tk.StringVar(value="")
        ip_entry = ttk.Entry(conn_frame, textvariable=self.ip_var, width=20, style="Bordered.TEntry", font=("Segoe UI", 10))
        ip_entry.grid(row=0, column=1, sticky="w", padx=5)
        
        # Username
        ttk.Label(conn_frame, text="Username:", style="Modern.TLabel").grid(row=0, column=2, sticky="w", padx=(20, 10))
        self.username_var = tk.StringVar(value="")
        username_entry = ttk.Entry(conn_frame, textvariable=self.username_var, width=20, style="Bordered.TEntry", font=("Segoe UI", 10))
        username_entry.grid(row=0, column=3, sticky="w", padx=5)
        
        # Password
        ttk.Label(conn_frame, text="Password:", style="Modern.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        self.password_var = tk.StringVar(value="")
        self.password_entry = ttk.Entry(conn_frame, textvariable=self.password_var, width=20, show="*", style="Bordered.TEntry", font=("Segoe UI", 10))
        self.password_entry.grid(row=1, column=1, sticky="w", padx=5, pady=(10, 0))
        
        # Show password checkbox (larger)
        self.show_password_var = tk.BooleanVar(value=False)
        show_pwd_style = ttk.Style()
        show_pwd_style.configure("Larger.TCheckbutton", font=("Segoe UI", 10))
        show_pwd_check = ttk.Checkbutton(conn_frame, text="Show password", variable=self.show_password_var,
                                         style="Larger.TCheckbutton",
                                         command=lambda: self.password_entry.config(show="" if self.show_password_var.get() else "*"))
        show_pwd_check.grid(row=1, column=2, sticky="w", padx=(20, 0), pady=(10, 0))
        
        # Connect button
        self.quick_connect_btn = tk.Button(conn_frame, text="Connect", 
                                           command=self._on_quick_connect,
                                           font=("Segoe UI", 10, "bold"),
                                           bg="#007BFF", fg="white",
                                           activebackground="#0056b3",
                                           relief="flat", bd=0,
                                           padx=20, pady=8,
                                           cursor="hand2")
        self.quick_connect_btn.grid(row=1, column=3, sticky="w", padx=(20, 0), pady=(10, 0))
        
        # Operations Frame - reorganized with grouped buttons
        ops_frame = ttk.Frame(main_frame, style="Modern.TFrame")
        ops_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Browser Operations Group (Primary)
        browser_group = ttk.LabelFrame(ops_frame, text="Browser Operations", padding=10, style="Modern.TLabelframe")
        browser_group.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        self.start_browser_login_btn = tk.Button(browser_group, text="Select APs", 
                                                 command=self._on_start_browser_login,
                                                 font=("Segoe UI", 10, "bold"),
                                                 bg="#28A745", fg="white",
                                                 activebackground="#218838",
                                                 relief="flat", bd=0,
                                                 padx=15, pady=8,
                                                 cursor="hand2")
        self.start_browser_login_btn.pack(side="left", padx=(0, 5))
        
        # Disabled buttons with dark text for better readability
        self.check_provisioning_btn = tk.Button(browser_group, text="Provisioning", 
                                                command=self._on_check_provisioning,
                                                font=("Segoe UI", 10),
                                                bg="#E0E0E0", fg="#333333",
                                                activebackground="#D0D0D0",
                                                disabledforeground="#333333",
                                                relief="flat", bd=0,
                                                padx=15, pady=8,
                                                cursor="hand2",
                                                state="disabled")
        self.check_provisioning_btn.pack(side="left", padx=(0, 5))
        
        self.enable_ssh_btn = tk.Button(browser_group, text="SSH", 
                                        command=self._on_enable_ssh,
                                        font=("Segoe UI", 10),
                                        bg="#E0E0E0", fg="#333333",
                                        activebackground="#D0D0D0",
                                        disabledforeground="#333333",
                                        relief="flat", bd=0,
                                        padx=15, pady=8,
                                        cursor="hand2",
                                        state="disabled")
        self.enable_ssh_btn.pack(side="left", padx=(0, 5))
        
        self.close_browser_btn = tk.Button(browser_group, text="Close Browser", 
                                           command=self._on_close_browser,
                                           font=("Segoe UI", 10),
                                           bg="#E0E0E0", fg="#333333",
                                           activebackground="#D0D0D0",
                                           disabledforeground="#333333",
                                           relief="flat", bd=0,
                                           padx=15, pady=8,
                                           cursor="hand2",
                                           state="disabled")
        self.close_browser_btn.pack(side="left")
        
        # Settings Group
        settings_group = ttk.LabelFrame(ops_frame, text="Settings", padding=10, style="Modern.TLabelframe")
        settings_group.grid(row=0, column=1, sticky="w")
        
        self.credentials_btn = tk.Button(settings_group, text="Manage AP Credentials", 
                                         command=self._on_manage_credentials,
                                         font=("Segoe UI", 10),
                                         bg="#007BFF", fg="white",
                                         activebackground="#0056b3",
                                         relief="flat", bd=0,
                                         padx=15, pady=8,
                                         cursor="hand2")
        self.credentials_btn.pack(side="left", padx=(0, 5))
        
        self.user_manager_btn = tk.Button(settings_group, text="Manage Users", 
                                          command=self._on_user_manager,
                                          font=("Segoe UI", 10),
                                          bg="#007BFF", fg="white",
                                          activebackground="#0056b3",
                                          relief="flat", bd=0,
                                          padx=15, pady=8,
                                          cursor="hand2")
        self.user_manager_btn.pack(side="left")
        
        # Exit Program button with spacing label for alignment
        exit_group = ttk.LabelFrame(ops_frame, text=" ", padding=10, style="Modern.TLabelframe")
        exit_group.grid(row=0, column=2, sticky="e")
        
        self.exit_btn = tk.Button(exit_group, text="Exit Program", 
                                  command=self._on_exit_program,
                                  font=("Segoe UI", 10),
                                  bg="#DC3545", fg="white",
                                  activebackground="#C82333",
                                  relief="flat", bd=0,
                                  padx=15, pady=8,
                                  cursor="hand2")
        self.exit_btn.pack(side="right")
        
        # Configure column weights
        ops_frame.columnconfigure(0, weight=0)
        ops_frame.columnconfigure(1, weight=0)
        ops_frame.columnconfigure(2, weight=1)
        
        # Progress Frame
        progress_frame = ttk.Frame(main_frame, style="Modern.TFrame")
        progress_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.status_var, style="Modern.TLabel").pack(pady=5)
        
        # Activity Log Frame
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding=10, style="Modern.TLabelframe")
        log_frame.grid(row=3, column=0, sticky="nsew", padx=(0, 5), pady=(0, 10))
        main_frame.rowconfigure(3, weight=1)
        
        # Activity log text with scrollbar
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side="right", fill="y")
        
        self.log_text = tk.Text(log_frame, height=12, wrap="word", font=("Consolas", 9), 
                               yscrollcommand=log_scroll.set)
        self.log_text.pack(fill="both", expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        # Results Frame
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10, style="Modern.TLabelframe")
        results_frame.grid(row=3, column=1, sticky="nsew", pady=(0, 10))
        main_frame.columnconfigure(1, weight=1)
        
        # Results text with scrollbar
        results_scroll = ttk.Scrollbar(results_frame)
        results_scroll.pack(side="right", fill="y")
        
        self.results_text = tk.Text(results_frame, height=12, wrap="word", font=("Consolas", 9),
                                    yscrollcommand=results_scroll.set)
        self.results_text.pack(fill="both", expand=True)
        results_scroll.config(command=self.results_text.yview)
    
    def _log_activity(self, message):
        """Add message to activity log."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.root.update_idletasks()
    
    def _update_progress(self, message, percent):
        """Update progress bar and status."""
        self.status_var.set(message)
        self.progress_var.set(percent)
        self.root.update_idletasks()
    
    def _display_result(self, result):
        """Display result in results panel."""
        self.results_text.delete("1.0", "end")
        self.results_text.insert("end", json.dumps(result, indent=2))
    
    def _run_task_async(self, task_func):
        """Run a task in a separate thread."""
        thread = threading.Thread(target=task_func, daemon=True)
        thread.start()
    
    def _on_quick_connect(self):
        """Handle Quick Connect - connect to single AP and fetch status info."""
        ip = self.ip_var.get().strip()
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not ip or not username or not password:
            messagebox.showwarning("Missing Information", "Please enter IP Address, Username, and Password")
            return
        
        def task():
            try:
                self._update_progress("Connecting to AP...", 0)
                
                # Load credential manager (will check for existing AP after extracting AP ID)
                from credential_manager import CredentialManager
                creds_manager = CredentialManager()
                
                # Initialize browser if not already open
                if not self.worker.driver:
                    self.worker.log("Initializing Chrome driver...")
                    try:
                        from selenium import webdriver
                        from selenium.webdriver.chrome.service import Service
                        from webdriver_manager.chrome import ChromeDriverManager
                        
                        options = webdriver.ChromeOptions()
                        options.add_argument('--ignore-certificate-errors')
                        options.add_argument('--ignore-ssl-errors')
                        options.add_experimental_option('excludeSwitches', ['enable-logging'])
                        
                        service = Service(ChromeDriverManager().install())
                        self.worker.driver = webdriver.Chrome(service=service, options=options)
                        self.worker.log("✓ Chrome driver initialized")
                    except Exception as e:
                        self.worker.log(f"Failed to initialize browser: {str(e)}")
                        self._display_result({
                            "status": "error",
                            "message": f"Failed to initialize browser: {str(e)}"
                        })
                        return
                
                # Login using CDP authentication (same as multi-AP workflow)
                self._update_progress("Authenticating...", 25)
                try:
                    # Set authentication via CDP
                    import base64
                    self.worker.log(f"Setting up authentication for {ip}")
                    self.worker.driver.execute_cdp_cmd('Network.enable', {})
                    auth_header = 'Basic ' + base64.b64encode(f'{username}:{password}'.encode()).decode()
                    self.worker.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {'Authorization': auth_header}})
                    
                    # Navigate to main page first
                    url = f"http://{ip}"
                    self.worker.log(f"Navigating to {url}")
                    self.worker.driver.get(url)
                    time.sleep(2)
                    
                    # Check for and handle Cato Networks warning
                    self.worker.handle_cato_warning()
                    
                    self.worker.log(f"✓ Successfully authenticated to {ip}")
                except Exception as e:
                    self.worker.log(f"Authentication failed: {str(e)}")
                    self._display_result({
                        "status": "error",
                        "message": f"Authentication failed: {str(e)}"
                    })
                    return
                
                # Navigate to status.xml
                self._update_progress("Fetching AP status information...", 50)
                try:
                    status_url = f"http://{ip}/service/status.xml"
                    self.worker.log(f"Navigating to {status_url}")
                    self.worker.driver.get(status_url)
                    time.sleep(3)
                    
                    # Parse the HTML table to get AP information
                    page_source = self.worker.driver.page_source
                    self.worker.log(f"Page source length: {len(page_source)}")
                    
                    # Extract information from HTML table rows
                    ap_id = self._extract_xml_value(page_source, "AP ID")
                    transmitter = self._extract_xml_value(page_source, "Transmitter")
                    store_id = self._extract_xml_value(page_source, "Store ID")
                    ip_address = self._extract_xml_value(page_source, "IP Address") or ip
                    
                    self.worker.log(f"AP Information retrieved:")
                    self.worker.log(f"  AP ID: {ap_id}")
                    self.worker.log(f"  Transmitter: {transmitter}")
                    self.worker.log(f"  IP Address: {ip_address}")
                    self.worker.log(f"  Store ID: {store_id}")
                    
                    if not ap_id:
                        self.worker.log("WARNING: Could not extract AP ID from status.xml")
                        self.worker.log(f"First 500 chars of page: {page_source[:500]}")
                        self._display_result({
                            "status": "error",
                            "message": "Could not extract AP information from status.xml. Check if the URL is correct."
                        })
                        return
                    
                    # Now check if AP exists by AP ID (not IP)
                    existing_ap = creds_manager.find_by_ap_id(ap_id)
                    
                    # Compare with existing data
                    if existing_ap:
                        self.worker.log(f"AP {ap_id} found in credentials database")
                        changes = []
                        if existing_ap.get("ip_address") != ip_address:
                            changes.append(f"IP: {existing_ap.get('ip_address')} → {ip_address}")
                        if existing_ap.get("store_id") != store_id:
                            changes.append(f"Store ID: {existing_ap.get('store_id')} → {store_id}")
                        
                        if changes:
                            self.worker.log(f"Changes detected: {changes}")
                            msg = f"AP {ap_id} information has changed:\n" + "\n".join(changes)
                            msg += "\n\nDo you want to update the stored information?"
                            
                            if messagebox.askyesno("Update AP Information", msg):
                                existing_ap["ip_address"] = ip_address
                                existing_ap["store_id"] = store_id
                                existing_ap["username_webui"] = username
                                existing_ap["password_webui"] = password
                                existing_ap["type"] = transmitter
                                existing_ap["last_modified"] = datetime.now().isoformat()
                                creds_manager.save()
                                self.worker.log("✓ AP information updated in database")
                        else:
                            self.worker.log("No changes detected in AP information")
                    else:
                        self.worker.log(f"AP {ap_id} not found in credentials database")
                        # AP doesn't exist, ask to save
                        msg = f"AP {ap_id} is not in the credentials list.\n\n"
                        msg += f"Transmitter: {transmitter}\n"
                        msg += f"Store ID: {store_id}\n"
                        msg += f"IP: {ip_address}\n\n"
                        msg += "Do you want to save this AP to credentials?"
                        
                        if messagebox.askyesno("Save AP Credentials", msg):
                            new_ap = {
                                "retail_chain": "",
                                "ap_id": ap_id,
                                "store_id": store_id,
                                "store_alias": "",
                                "ip_address": ip_address,
                                "type": transmitter,
                                "username_webui": username,
                                "password_webui": password,
                                "username_ssh": "",
                                "password_ssh": "",
                                "su_password": "",
                                "notes": "Added via Quick Connect",
                                "last_modified": datetime.now().isoformat()
                            }
                            
                            # Set default SSH credentials for SES-imagotag APs
                            if "SES-imagotag Access Point AP-2010" in transmitter:
                                new_ap["username_ssh"] = "esl"
                                new_ap["password_ssh"] = "imagotag"
                            # For Vgate, don't set SSH credentials (unique per device)
                            
                            success, message = creds_manager.add_credential(new_ap)
                            if success:
                                self.worker.log(f"✓ AP {ap_id} saved to credentials")
                            else:
                                self.worker.log(f"Failed to save AP: {message}")
                    
                    self._display_result({
                        "status": "success",
                        "message": f"Successfully connected to AP {ap_id}"
                    })
                    
                    # Enable browser operation buttons
                    self.root.after(0, lambda: self.check_provisioning_btn.config(state="normal", bg="#FFC107"))
                    self.root.after(0, lambda: self.enable_ssh_btn.config(state="normal", bg="#17A2B8"))
                    self.root.after(0, lambda: self.close_browser_btn.config(state="normal"))
                    
                except Exception as e:
                    self.worker.log(f"Error fetching status: {str(e)}")
                    self._display_result({
                        "status": "error",
                        "message": f"Failed to fetch AP status: {str(e)}"
                    })
                    
            except Exception as e:
                self.worker.log(f"Quick connect error: {str(e)}")
                self._display_result({
                    "status": "error",
                    "message": f"Connection failed: {str(e)}"
                })
        
        self._run_task_async(task)
    
    def _extract_xml_value(self, html_text, field_name):
        """Extract value from HTML table row. The data is in format:
        <tr><th>Field Name:</th><td>Value</td></tr>
        """
        import re
        # Create pattern to match the table row with the field name
        pattern = f"<th>{field_name}:</th>\\s*<td>([^<]*)</td>"
        match = re.search(pattern, html_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _on_exit_program(self):
        """Handle Exit Program button."""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self._on_close()
    
    def _on_start_browser_login(self):
        """Handle combined Start Browser Login (opens browser with credentials)."""
        from ap_selector_dialog import APSelectorDialog
        
        # Show AP selector dialog
        dialog = APSelectorDialog(self.root)
        selected_aps = dialog.show()
        
        if not selected_aps:
            self._update_progress("No APs selected", 0)
            return
        
        def task():
            self._update_progress(f"Connecting to {len(selected_aps)} APs...", 0)
            # Limit to 5 simultaneous connections for stability
            result = self.worker.open_browser_with_multiple_aps(selected_aps, max_parallel=5)
            self._display_result(result)
            # Enable buttons if we have at least one successful connection (success or warning)
            if result["status"] in ["success", "warning"]:
                # Enable browser operation buttons after successful login
                self.root.after(0, lambda: self.check_provisioning_btn.config(state="normal", bg="#FFC107"))
                self.root.after(0, lambda: self.enable_ssh_btn.config(state="normal", bg="#17A2B8"))
                self.root.after(0, lambda: self.close_browser_btn.config(state="normal"))
        
        self._run_task_async(task)
    
    # Legacy methods removed - now using multi-AP workflow
    

    
    def _on_check_provisioning(self):
        """Handle Step 3: Check Provisioning."""
        from provisioning_dialog import ProvisioningDialog
        
        # Show dialog to get action
        dialog = ProvisioningDialog(self.root)
        action = dialog.show()
        
        if action is None:  # User canceled
            self._update_progress("Operation canceled", 0)
            return
        
        def task():
            self._update_progress(f"Managing provisioning ({action})...", 0)
            result = self.worker.manage_provisioning_batch(action)
            self._display_result(result)
        
        self._run_task_async(task)
    
    def _on_enable_ssh(self):
        """Handle Enable SSH workflow."""
        from ssh_dialog import SSHDialog
        
        # Show dialog to get action
        dialog = SSHDialog(self.root)
        action = dialog.show()
        
        if action is None:  # User canceled
            self._update_progress("Operation canceled", 0)
            return
        
        def task():
            self._update_progress(f"Managing SSH ({action})...", 0)
            result = self.worker.manage_ssh_batch(action)
            self._display_result(result)
        
        self._run_task_async(task)
    
    def _on_capture_page(self):
        """Capture current page and look for provisioning field."""
        def task():
            self._update_progress("Capturing page...", 0)
            if not self.worker.driver:
                result = {"status": "error", "message": "No browser open"}
            else:
                self.worker.log("=== Capturing Current Page ===")
                
                # Get current state
                current_url = self.worker.driver.current_url
                page_title = self.worker.driver.title
                
                self.worker.log(f"Current URL: {current_url}")
                self.worker.log(f"Page Title: '{page_title}'")
                
                # Save screenshot
                screenshot_path = Path(__file__).parent / "captured_page.png"
                self.worker.driver.save_screenshot(str(screenshot_path))
                self.worker.log(f"Screenshot saved: {screenshot_path.name}")
                
                # Save full page source
                source_path = Path(__file__).parent / "captured_page_source.html"
                with open(source_path, 'w', encoding='utf-8') as f:
                    f.write(self.worker.driver.page_source)
                self.worker.log(f"Page source saved: {source_path.name}")
                
                # Look for provisioning field
                self.worker.log("Searching for provisioning field...")
                provisioning_found = False
                provisioning_checked = None
                
                try:
                    # Try to find provisioningEnabled checkbox
                    field = self.worker.driver.find_element(By.NAME, "provisioningEnabled")
                    provisioning_found = True
                    provisioning_checked = field.is_selected()
                    self.worker.log(f"✅ Found provisioningEnabled field!")
                    self.worker.log(f"   Status: {'CHECKED' if provisioning_checked else 'UNCHECKED'}")
                except:
                    try:
                        field = self.worker.driver.find_element(By.ID, "provisioningEnabled")
                        provisioning_found = True
                        provisioning_checked = field.is_selected()
                        self.worker.log(f"✅ Found provisioningEnabled field by ID!")
                        self.worker.log(f"   Status: {'CHECKED' if provisioning_checked else 'UNCHECKED'}")
                    except:
                        self.worker.log("❌ provisioningEnabled field not found on this page")
                
                # Try to find all checkboxes
                try:
                    checkboxes = self.worker.driver.find_elements(By.XPATH, "//input[@type='checkbox']")
                    self.worker.log(f"Found {len(checkboxes)} checkbox(es) on page:")
                    for i, cb in enumerate(checkboxes[:10]):  # Limit to 10
                        name = cb.get_attribute('name') or '(no name)'
                        id_attr = cb.get_attribute('id') or '(no id)'
                        checked = cb.is_selected()
                        self.worker.log(f"  [{i+1}] name='{name}', id='{id_attr}', checked={checked}")
                except Exception as e:
                    self.worker.log(f"Could not enumerate checkboxes: {e}")
                
                result = {
                    "status": "success",
                    "url": current_url,
                    "title": page_title,
                    "provisioning_found": provisioning_found,
                    "provisioning_enabled": provisioning_checked,
                    "message": "Page captured - check logs for details"
                }
            
            self._display_result(result)
            self._update_progress("Capture complete", 100)
        
        self._run_task_async(task)
    
    def _on_diagnostics(self):
        """Run diagnostics on current page."""
        def task():
            self._update_progress("Running diagnostics...", 0)
            if not self.worker.driver:
                result = {"status": "error", "message": "No browser open"}
            else:
                self.worker.log("=== Running Diagnostics ===")
                
                # Get current state
                current_url = self.worker.driver.current_url
                page_title = self.worker.driver.title
                page_length = len(self.worker.driver.page_source)
                
                self.worker.log(f"Current URL: {current_url}")
                self.worker.log(f"Page Title: '{page_title}'")
                self.worker.log(f"Page Source Length: {page_length} characters")
                
                # Try to get visible text
                try:
                    body = self.worker.driver.find_element(By.TAG_NAME, "body")
                    visible_text = body.text[:500] if body.text else "(no visible text)"
                    self.worker.log(f"Visible Text: {visible_text}")
                except Exception as e:
                    self.worker.log(f"Could not get visible text: {e}")
                
                # Save diagnostic screenshot
                screenshot_path = Path(__file__).parent / "diagnostic_screenshot.png"
                self.worker.driver.save_screenshot(str(screenshot_path))
                self.worker.log(f"Diagnostic screenshot saved: {screenshot_path.name}")
                
                # Save page source
                source_path = Path(__file__).parent / "diagnostic_page_source.html"
                with open(source_path, 'w', encoding='utf-8') as f:
                    f.write(self.worker.driver.page_source)
                self.worker.log(f"Diagnostic page source saved: {source_path.name}")
                
                result = {
                    "status": "info",
                    "url": current_url,
                    "title": page_title,
                    "page_size": page_length,
                    "message": "Diagnostic complete - check logs and files"
                }
            
            self._display_result(result)
            self._update_progress("Diagnostic complete", 100)
        
        self._run_task_async(task)
    
    def _on_manage_credentials(self):
        """Open the credential manager."""
        from credential_manager_gui import CredentialManagerGUI
        
        try:
            # Open credential manager as a toplevel window with current user context
            CredentialManagerGUI(self.current_user, self.root)
            self._log_activity("Credential manager opened")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open credential manager: {e}")
    
    def _on_user_manager(self):
        """Open the user manager."""
        from user_manager_gui import UserManagerGUI
        
        try:
            UserManagerGUI(self.current_user, self.root)
            self._log_activity("User manager opened")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open user manager: {e}")
    
    def _on_close_browser(self):
        """Handle Close Browser."""
        def task():
            result = self.worker.close()
            self._display_result(result)
            self._update_progress("Ready", 0)
            self.root.after(0, lambda: self.login_btn.config(state="disabled"))
            self.root.after(0, lambda: self.check_provisioning_btn.config(state="disabled"))
            self.root.after(0, lambda: self.start_recording_btn.config(state="disabled"))
            self.root.after(0, lambda: self.stop_recording_btn.config(state="disabled"))
            self.root.after(0, lambda: self.diagnostic_btn.config(state="disabled"))
            self.root.after(0, lambda: self.capture_btn.config(state="disabled"))
            self.root.after(0, lambda: self.close_browser_btn.config(state="disabled"))
        
        self._run_task_async(task)
    
    def _save_settings(self):
        """Save current settings."""
        self.settings["last_ip"] = self.ip_var.get()
        self.settings["last_username"] = self.username_var.get()
        self.settings["last_password"] = self.password_var.get()
        self.settings["window_size"] = [self.root.winfo_width(), self.root.winfo_height()]
        save_settings(self.settings)
        self._log_activity("Settings saved")
        messagebox.showinfo("Settings Saved", "Connection settings have been saved.")
    
    def _on_close(self):
        """Handle window close."""
        if self.worker.driver:
            if messagebox.askyesno("Close Browser?", "Close the browser before exiting?"):
                self.worker.close()
        self.root.destroy()

def main():
    from login_dialog import LoginDialog
    
    # Show login dialog first (it creates its own Tk window)
    login = LoginDialog()
    current_user = login.show()
    
    if not current_user:
        # User cancelled login
        login.get_root().destroy()
        return
    
    # Reuse the Tk root from login dialog
    root = login.get_root()
    login.cleanup()  # Clean up login widgets before reusing root
    root.deiconify()  # Show the window again
    app = App(root, current_user)
    root.mainloop()

if __name__ == "__main__":
    main()

