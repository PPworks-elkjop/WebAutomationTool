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
import subprocess
import platform

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
from browser_manager import BrowserManager

APP_NAME = "VERA"
APP_TAGLINE = "Vusion support with a human touch"
APP_VERSION = "0.4"
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

def ping_host(ip_address, timeout=1):
    """
    Ping a host and return True if reachable, False otherwise.
    Works on Windows, Linux, and Mac.
    
    Args:
        ip_address: IP address or hostname to ping
        timeout: Timeout in seconds (default 1)
    
    Returns:
        tuple: (success: bool, response_time: float or None)
    """
    try:
        # Determine ping command based on OS
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
        
        # Build ping command
        command = ['ping', param, '1', timeout_param, str(timeout * 1000 if platform.system().lower() == 'windows' else timeout), ip_address]
        
        # Execute ping
        start_time = time.time()
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout + 1)
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Check if ping was successful
        if result.returncode == 0:
            return (True, round(response_time, 2))
        else:
            return (False, None)
            
    except subprocess.TimeoutExpired:
        return (False, None)
    except Exception as e:
        return (False, None)

class WebAutomationWorker:
    """Worker for web automation tasks - maintains persistent browser."""
    def __init__(self, progress_callback, log_callback, parent_window=None, 
                 provisioning_callback=None, ssh_callback=None, 
                 close_browser_callback=None, ping_selected_callback=None):
        self.progress = progress_callback
        self.log = log_callback
        self.parent_window = parent_window
        self.driver = None
        self.is_logged_in = False
        self.recording = False
        self.recorded_events = []
        self.status_dialog = None
        self.provisioning_callback = provisioning_callback
        self.ssh_callback = ssh_callback
        self.close_browser_callback = close_browser_callback
        self.ping_selected_callback = ping_selected_callback
        
        # Initialize browser manager
        self.browser_manager = BrowserManager(
            log_callback=self.log,
            progress_callback=self.progress,
            extract_xml_callback=self._extract_xml_value,
            handle_cato_callback=self.handle_cato_warning
        )
    
    def _extract_xml_value(self, html_text, field_name):
        """Extract value from HTML table row. The data is in format:
        <tr><th>Field Name:</th><td>Value</td></tr>
        """
        import re
        pattern = f"<th>{field_name}:</th>\\s*<td>([^<]*)</td>"
        match = re.search(pattern, html_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def handle_cato_warning(self, driver=None):
        """Check for and handle Cato Networks warning page.
        Returns True if warning was detected and handled, False otherwise.
        """
        try:
            # Use provided driver or fall back to self.driver
            active_driver = driver if driver else self.driver
            if not active_driver:
                return False
                
            page_source = active_driver.page_source
            
            # Check if Cato Networks warning page is present
            has_warning = 'Warning - Restricted Website' in page_source
            has_ssl_error = 'Invalid SSL/TLS certificate' in page_source
            has_proceed_button = 'class="proceed prompt"' in page_source or 'onclick="onProceed()"' in page_source
            
            self.log(f"[Cato Check] Warning text: {has_warning}, SSL error: {has_ssl_error}, Proceed button: {has_proceed_button}")
            
            if (has_warning or has_ssl_error) and has_proceed_button:
                
                self.log("🚨 Cato Networks warning detected, clicking PROCEED button...")
                
                # Find and click the PROCEED button
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                try:
                    # Try multiple selectors for the proceed button
                    proceed_selectors = [
                        "button.proceed.prompt",
                        "button.proceed",
                        "button[class*='proceed']",
                        "//button[contains(text(), 'PROCEED')]",
                        "//button[contains(@class, 'proceed')]"
                    ]
                    
                    proceed_btn = None
                    for selector in proceed_selectors:
                        try:
                            if selector.startswith("//"):
                                # XPath selector
                                proceed_btn = WebDriverWait(active_driver, 3).until(
                                    EC.element_to_be_clickable((By.XPATH, selector))
                                )
                            else:
                                # CSS selector
                                proceed_btn = WebDriverWait(active_driver, 3).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                )
                            self.log(f"✓ Found PROCEED button with selector: {selector}")
                            break
                        except:
                            continue
                    
                    if not proceed_btn:
                        self.log("✗ Could not find PROCEED button with any selector")
                        return False
                    
                    # Try regular click first, then JavaScript click as fallback
                    try:
                        proceed_btn.click()
                        self.log("✓ Clicked PROCEED button (regular click)")
                    except Exception as click_err:
                        self.log(f"Regular click failed, trying JavaScript click: {str(click_err)}")
                        try:
                            active_driver.execute_script("arguments[0].click();", proceed_btn)
                            self.log("✓ Clicked PROCEED button (JavaScript click)")
                        except Exception as js_err:
                            self.log(f"✗ JavaScript click also failed: {str(js_err)}")
                            return False
                    
                    # Wait 2 seconds then refresh the page as per Cato requirements
                    self.log("⏱ Waiting 2 seconds before refresh...")
                    time.sleep(2)
                    
                    # Refresh to get past Cato warning
                    try:
                        self.log("🔄 Refreshing page after Cato PROCEED...")
                        active_driver.refresh()
                        self.log("✓ Page refreshed successfully")
                        
                        # Wait for page to load after refresh
                        time.sleep(3)
                        
                        # Wait for body element
                        WebDriverWait(active_driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        self.log("✓ Page loaded after Cato warning handling")
                        
                    except Exception as refresh_err:
                        self.log(f"⚠ Error during page refresh: {str(refresh_err)}")
                        # Continue anyway, page might have loaded
                    
                    return True
                except Exception as e:
                    self.log(f"Could not click PROCEED button: {str(e)}")
                    import traceback
                    self.log(traceback.format_exc())
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
        """
        Open browser and connect to multiple APs in tabs (max 5 simultaneously).
        
        Args:
            ap_list: List of AP credential dictionaries
            max_parallel: Maximum number of simultaneous connections (default: 5)
        """
        try:
            # Create status dialog
            if self.parent_window:
                self.status_dialog = ConnectionStatusDialog(
                    self.parent_window, 
                    ap_list,
                    provisioning_callback=self.provisioning_callback,
                    ssh_callback=self.ssh_callback,
                    close_browser_callback=self.close_browser_callback,
                    ping_host_func=ping_host
                )
                # Set reconnect callback
                self.status_dialog.reconnect_callback = self._reconnect_selected_aps
            
            # Use browser manager to open all APs
            result = self.browser_manager.open_multiple_aps(ap_list, self.status_dialog)
            
            # Sync state with browser manager
            self.driver = self.browser_manager.driver
            self.ap_tabs = self.browser_manager.ap_tabs
            self.is_logged_in = result["status"] in ["success", "warning"]
            
            return result
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to open multi-AP browser: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            self.log(traceback.format_exc())
            
            if self.status_dialog:
                self.status_dialog.update_summary(f"✗ Error: {str(e)}")
                self.status_dialog.enable_close()
            
            return {"status": "error", "message": error_msg}
    
    def _reconnect_selected_aps(self, selected_aps):
        """Reconnect to selected APs that failed or lost connection.
        
        Args:
            selected_aps: List of AP dictionaries to reconnect
        """
        if not selected_aps:
            return
        
        self.log(f"\n=== Reconnecting to {len(selected_aps)} selected APs ===")
        
        # Use browser manager to reconnect (it will handle opening tabs and logging in)
        import threading
        
        def reconnect_thread():
            try:
                # Pass is_reconnect=True to append new tabs instead of replacing
                result = self.browser_manager.open_multiple_aps(selected_aps, self.status_dialog, is_reconnect=True)
                
                # Sync state with browser manager after reconnection
                self.driver = self.browser_manager.driver
                self.ap_tabs = self.browser_manager.ap_tabs
                
                # Update dialog summary
                if self.status_dialog:
                    if result["status"] == "success":
                        self.status_dialog.update_summary(f"✓ Reconnected to {len(selected_aps)} APs successfully")
                    else:
                        self.status_dialog.update_summary(f"⚠ Reconnection completed with issues")
                    self.status_dialog.enable_action_buttons()
                
            except Exception as e:
                self.log(f"ERROR during reconnection: {str(e)}")
                import traceback
                self.log(traceback.format_exc())
                if self.status_dialog:
                    self.status_dialog.update_summary(f"✗ Reconnection error: {str(e)}")
        
        # Run reconnection in background thread
        thread = threading.Thread(target=reconnect_thread, daemon=True)
        thread.start()
    
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
            
            # Log individual AP results if user_manager callback is available
            if hasattr(self, 'user_manager_callback') and self.user_manager_callback:
                for result_item in results:
                    ap_id = result_item['ap_id']
                    success = result_item['success']
                    message = result_item['result'].get('message', '')
                    
                    self.user_manager_callback(
                        activity_type=f'SSH {action}',
                        description=message,
                        ap_id=ap_id,
                        success=success,
                        details={'action': action}
                    )
            
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
            
            # Log individual AP results if user_manager callback is available
            if hasattr(self, 'user_manager_callback') and self.user_manager_callback:
                for result_item in results:
                    ap_id = result_item['ap_id']
                    success = result_item['success']
                    message = result_item['result'].get('message', '')
                    
                    self.user_manager_callback(
                        activity_type=f'Provisioning {action}',
                        description=message,
                        ap_id=ap_id,
                        success=success,
                        details={'action': action}
                    )
            
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

class AboutDialog:
    """About dialog with application information and credits."""
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"About {APP_NAME}")
        self.dialog.geometry("650x700")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center window
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (650 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (700 // 2)
        self.dialog.geometry(f"650x700+{x}+{y}")
        
        # Main frame with white background
        main_frame = tk.Frame(self.dialog, bg="white")
        main_frame.pack(fill="both", expand=True)
        
        # Header with logo/icon (fixed at top)
        header_frame = tk.Frame(main_frame, bg="white")
        header_frame.pack(fill="x", pady=(20, 10))
        
        # App icon/logo - robot-granny emoji combination
        icon_label = tk.Label(header_frame, text="👵🤖", font=("Segoe UI", 48), bg="white")
        icon_label.pack()
        
        # App name and tagline
        name_label = tk.Label(header_frame, text=APP_NAME, 
                             font=("Segoe UI", 28, "bold"), 
                             bg="white", fg="#28A745")
        name_label.pack(pady=(5, 0))
        
        tagline_label = tk.Label(header_frame, text=APP_TAGLINE, 
                                font=("Segoe UI", 12, "italic"), 
                                bg="white", fg="#666666")
        tagline_label.pack(pady=(2, 0))
        
        # Version info
        version_label = tk.Label(header_frame, 
                                text=f"Version {APP_VERSION} • Released {APP_RELEASE_DATE}", 
                                font=("Segoe UI", 10), 
                                bg="white", fg="#888888")
        version_label.pack(pady=(5, 0))
        
        # Separator
        separator = tk.Frame(main_frame, height=2, bg="#E0E0E0")
        separator.pack(fill="x", padx=40, pady=15)
        
        # Scrollable content frame
        scroll_container = tk.Frame(main_frame, bg="white")
        scroll_container.pack(fill="both", expand=True, padx=40)
        
        # Canvas for scrolling
        canvas = tk.Canvas(scroll_container, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Description
        desc_frame = tk.Frame(scrollable_frame, bg="white")
        desc_frame.pack(fill="x", pady=(0, 10))
        
        desc_text = ("VERA (Vusion Electronic Retail Assistant) is a professional tool designed\n"
                    "to streamline and automate the management of SES-imagotag Vusion Access Points.\n\n"
                    "With VERA, IT professionals can efficiently handle multiple AP configurations,\n"
                    "perform batch operations, and maintain comprehensive credential management—\n"
                    "all through an intuitive, user-friendly interface.")
        
        desc_label = tk.Label(desc_frame, text=desc_text, 
                             font=("Segoe UI", 10), 
                             bg="white", fg="#333333",
                             justify="left", wraplength=550)
        desc_label.pack(anchor="w")
        
        # Features section
        features_frame = tk.Frame(scrollable_frame, bg="#F8F9FA", relief="solid", bd=1)
        features_frame.pack(fill="x", pady=15)
        
        features_title = tk.Label(features_frame, text="Key Features", 
                                 font=("Segoe UI", 12, "bold"), 
                                 bg="#F8F9FA", fg="#333333")
        features_title.pack(pady=(10, 5))
        
        features_text = ("• Automated provisioning status checks\n"
                        "• One-click SSH enablement\n"
                        "• Secure credential management with AES-256 encryption\n"
                        "• Batch operations across multiple Access Points\n"
                        "• Step-by-step execution control\n"
                        "• Connection status monitoring\n"
                        "• Multi-user support with role-based access\n"
                        "• Quick Connect for individual AP management\n"
                        "• Cato Networks warning detection and handling")
        
        features_label = tk.Label(features_frame, text=features_text, 
                                 font=("Segoe UI", 9), 
                                 bg="#F8F9FA", fg="#555555",
                                 justify="left")
        features_label.pack(padx=20, pady=(0, 10), anchor="w")
        
        # Credits section
        credits_frame = tk.Frame(scrollable_frame, bg="white")
        credits_frame.pack(fill="x", pady=10)
        
        credits_title = tk.Label(credits_frame, text="Credits", 
                                font=("Segoe UI", 12, "bold"), 
                                bg="white", fg="#333333")
        credits_title.pack(pady=(5, 10))
        
        credits_text = ("Created by: Peter Andersson\n"
                       "with assistance from my friendly GitHub Copilot friend\n\n"
                       "Built for Elkjøp Nordic AS")
        
        credits_label = tk.Label(credits_frame, text=credits_text, 
                                font=("Segoe UI", 10), 
                                bg="white", fg="#666666",
                                justify="center")
        credits_label.pack()
        
        # Add some bottom padding in scrollable content
        bottom_padding = tk.Frame(scrollable_frame, bg="white", height=20)
        bottom_padding.pack()
        
        # Close button (fixed at bottom)
        button_frame = tk.Frame(main_frame, bg="white")
        button_frame.pack(fill="x", pady=(10, 20))
        
        close_btn = tk.Button(button_frame, text="Close", 
                             command=self._cleanup_and_close,
                             font=("Segoe UI", 10, "bold"),
                             bg="#28A745", fg="white",
                             activebackground="#218838",
                             relief="flat", bd=0,
                             padx=40, pady=10,
                             cursor="hand2")
        close_btn.pack()
    
    def _cleanup_and_close(self):
        """Clean up event bindings and close dialog."""
        # Unbind mouse wheel to prevent memory leaks
        self.dialog.unbind_all("<MouseWheel>")
        self.dialog.destroy()

class App:
    def __init__(self, root, current_user):
        self.root = root
        self.current_user = current_user
        self.settings = load_settings()
        
        # Initialize user manager for activity logging
        from user_manager_v2 import UserManager
        self.user_manager = UserManager()
        
        self.worker = WebAutomationWorker(
            self._update_progress, 
            self._log_activity, 
            root,
            provisioning_callback=self._on_check_provisioning,
            ssh_callback=self._on_enable_ssh,
            close_browser_callback=self._on_close_browser,
            ping_selected_callback=self._on_ping_selected
        )
        
        # Set user_manager callback for activity logging in batch operations
        def user_manager_log_wrapper(**kwargs):
            """Wrapper to add username to activity logging."""
            self.user_manager.log_activity(
                username=self.current_user['username'],
                **kwargs
            )
        self.worker.user_manager_callback = user_manager_log_wrapper
        
        # Configure window
        root.title(f"{APP_NAME} v{APP_VERSION} - {current_user['full_name']} ({current_user['role']})")
        
        # Enable window resizing (remove any size restrictions)
        root.resizable(True, True)
        
        # Set minimum window size
        root.minsize(800, 600)
        
        # Start maximized
        root.state('zoomed')  # Windows maximized state
        
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
        
        # AP ID with search button (Row 0)
        ttk.Label(conn_frame, text="AP ID:", style="Modern.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.ap_id_var = tk.StringVar(value="")
        ap_id_entry = ttk.Entry(conn_frame, textvariable=self.ap_id_var, width=20, style="Bordered.TEntry", font=("Segoe UI", 10))
        ap_id_entry.grid(row=0, column=1, sticky="w", padx=5)
        
        # Search button with magnifying glass icon
        self.search_ap_btn = tk.Button(conn_frame, text="🔍", 
                                       command=self._on_search_ap,
                                       font=("Segoe UI", 12),
                                       bg="#17A2B8", fg="white",
                                       activebackground="#117A8B",
                                       relief="flat", bd=0,
                                       padx=8, pady=4,
                                       cursor="hand2")
        self.search_ap_btn.grid(row=0, column=2, sticky="w", padx=(5, 20))
        
        # IP Address
        ttk.Label(conn_frame, text="IP Address:", style="Modern.TLabel").grid(row=0, column=3, sticky="w", padx=(0, 10))
        self.ip_var = tk.StringVar(value="")
        ip_entry = ttk.Entry(conn_frame, textvariable=self.ip_var, width=20, style="Bordered.TEntry", font=("Segoe UI", 10))
        ip_entry.grid(row=0, column=4, sticky="w", padx=5)
        
        # Ping button
        self.ping_btn = tk.Button(conn_frame, text="Ping", 
                                  command=self._on_ping_single,
                                  font=("Segoe UI", 10),
                                  bg="#6C757D", fg="white",
                                  activebackground="#5A6268",
                                  relief="flat", bd=0,
                                  padx=15, pady=8,
                                  cursor="hand2")
        self.ping_btn.grid(row=0, column=5, sticky="w", padx=(20, 0))
        
        # Username (Row 1)
        ttk.Label(conn_frame, text="Username:", style="Modern.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        self.username_var = tk.StringVar(value="")
        username_entry = ttk.Entry(conn_frame, textvariable=self.username_var, width=20, style="Bordered.TEntry", font=("Segoe UI", 10))
        username_entry.grid(row=1, column=1, sticky="w", padx=5, pady=(10, 0))
        
        # Password
        ttk.Label(conn_frame, text="Password:", style="Modern.TLabel").grid(row=1, column=3, sticky="w", padx=(0, 10), pady=(10, 0))
        self.password_var = tk.StringVar(value="")
        self.password_entry = ttk.Entry(conn_frame, textvariable=self.password_var, width=20, show="*", style="Bordered.TEntry", font=("Segoe UI", 10))
        self.password_entry.grid(row=1, column=4, sticky="w", padx=5, pady=(10, 0))
        
        # Show password checkbox (larger)
        self.show_password_var = tk.BooleanVar(value=False)
        show_pwd_style = ttk.Style()
        show_pwd_style.configure("Larger.TCheckbutton", font=("Segoe UI", 10))
        show_pwd_check = ttk.Checkbutton(conn_frame, text="Show password", variable=self.show_password_var,
                                         style="Larger.TCheckbutton",
                                         command=lambda: self.password_entry.config(show="" if self.show_password_var.get() else "*"))
        show_pwd_check.grid(row=1, column=2, columnspan=2, sticky="w", padx=(5, 0), pady=(10, 0))
        
        # Connect button
        self.quick_connect_btn = tk.Button(conn_frame, text="Connect", 
                                           command=self._on_quick_connect,
                                           font=("Segoe UI", 10, "bold"),
                                           bg="#007BFF", fg="white",
                                           activebackground="#0056b3",
                                           relief="flat", bd=0,
                                           padx=20, pady=8,
                                           cursor="hand2")
        self.quick_connect_btn.grid(row=1, column=5, sticky="w", padx=(20, 0), pady=(10, 0))
        
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
        
        self.ping_all_btn = tk.Button(browser_group, text="Ping All APs", 
                                      command=self._on_ping_all,
                                      font=("Segoe UI", 10),
                                      bg="#6C757D", fg="white",
                                      activebackground="#5A6268",
                                      relief="flat", bd=0,
                                      padx=15, pady=8,
                                      cursor="hand2")
        self.ping_all_btn.pack(side="left")
        
        self.stop_ping_btn = tk.Button(browser_group, text="Stop Ping", 
                                       command=self._on_stop_ping,
                                       font=("Segoe UI", 10),
                                       bg="#DC3545", fg="white",
                                       activebackground="#C82333",
                                       relief="flat", bd=0,
                                       padx=15, pady=8,
                                       cursor="hand2")
        # Hidden by default
        
        # Settings Group
        settings_group = ttk.LabelFrame(ops_frame, text="Settings", padding=10, style="Modern.TLabelframe")
        settings_group.grid(row=0, column=1, sticky="w", padx=(0, 10))
        
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
        self.user_manager_btn.pack(side="left", padx=(0, 5))
        
        self.support_btn = tk.Button(settings_group, text="🛠️ AP Support", 
                                     command=self._on_ap_support,
                                     font=("Segoe UI", 10),
                                     bg="#28A745", fg="white",
                                     activebackground="#218838",
                                     relief="flat", bd=0,
                                     padx=15, pady=8,
                                     cursor="hand2")
        self.support_btn.pack(side="left", padx=(0, 5))
        
        self.about_btn = tk.Button(settings_group, text="About", 
                                   command=self._show_about,
                                   font=("Segoe UI", 10),
                                   bg="#17A2B8", fg="white",
                                   activebackground="#117A8B",
                                   relief="flat", bd=0,
                                   padx=15, pady=8,
                                   cursor="hand2")
        self.about_btn.pack(side="left")
        
        # Administration Group (Admin-only)
        is_admin = (self.current_user.get('is_admin') or 
                   (self.current_user.get('role', '').lower() == 'admin'))
        
        if is_admin:
            admin_group = ttk.LabelFrame(ops_frame, text="Administration", padding=10, style="Modern.TLabelframe")
            admin_group.grid(row=0, column=2, sticky="w", padx=(0, 10))
            
            self.audit_log_btn = tk.Button(admin_group, text="📋 Audit Log", 
                                          command=self._on_audit_log,
                                          font=("Segoe UI", 10),
                                          bg="#6C757D", fg="white",
                                          activebackground="#5A6268",
                                          relief="flat", bd=0,
                                          padx=15, pady=8,
                                          cursor="hand2")
            self.audit_log_btn.pack(side="left", padx=(0, 5))
            
            self.admin_settings_btn = tk.Button(admin_group, text="⚙️ Admin Settings", 
                                               command=self._on_admin_settings,
                                               font=("Segoe UI", 10),
                                               bg="#6C757D", fg="white",
                                               activebackground="#5A6268",
                                               relief="flat", bd=0,
                                               padx=15, pady=8,
                                               cursor="hand2")
            self.admin_settings_btn.pack(side="left")
        
        # Exit Program button with spacing label for alignment
        exit_group = ttk.LabelFrame(ops_frame, text=" ", padding=10, style="Modern.TLabelframe")
        exit_group.grid(row=0, column=3, sticky="e")
        
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
        ops_frame.columnconfigure(2, weight=0)
        ops_frame.columnconfigure(3, weight=1)
        
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
    
    def _on_search_ap(self):
        """Search for AP in credential manager and auto-fill fields."""
        ap_id = self.ap_id_var.get().strip()
        
        if not ap_id:
            messagebox.showwarning("Missing AP ID", "Please enter an AP ID to search")
            return
        
        try:
            from credential_manager_v2 import CredentialManager
            creds_manager = CredentialManager()
            
            # Find credentials for this AP
            credentials = creds_manager.find_by_ap_id(ap_id)
            
            if credentials:
                # Auto-fill the fields - map credential manager fields to our fields
                ip = credentials.get('ip_address', '')
                username = credentials.get('username_webui', '')
                password = credentials.get('password_webui', '')
                
                self.ip_var.set(ip)
                self.username_var.set(username)
                self.password_var.set(password)
                
                # Log success with details
                store_info = f"Store {credentials.get('store_id', 'N/A')}"
                if credentials.get('store_alias'):
                    store_info += f" ({credentials.get('store_alias')})"
                self._log_activity(f"✓ Loaded credentials for AP: {ap_id} - {store_info} - IP: {ip}")
            else:
                self._log_activity(f"✗ No credentials found for AP: {ap_id}")
                messagebox.showwarning("AP Not Found", 
                                      f"No credentials found for AP ID: {ap_id}\n\n"
                                      f"Please check:\n"
                                      f"• AP ID is correct\n"
                                      f"• AP has been added to Credential Manager")
                
        except ImportError:
            messagebox.showerror("Error", "Credential Manager not found")
        except Exception as e:
            self._log_activity(f"Error searching for AP {ap_id}: {str(e)}")
            messagebox.showerror("Search Error", f"Error: {str(e)}")
    
    def _on_ping_single(self):
        """Ping the IP address in Quick Connect field."""
        ip = self.ip_var.get().strip()
        
        if not ip:
            messagebox.showwarning("Missing IP Address", "Please enter an IP Address to ping")
            return
        
        # Log activity
        self.user_manager.log_activity(
            username=self.current_user['username'],
            activity_type='Ping AP',
            description=f'Pinging AP at {ip}',
            details={'ip_address': ip}
        )
        
        def task():
            try:
                self._log_activity(f"Pinging {ip}...")
                self._update_progress(f"Pinging {ip}...", 50)
                
                success, response_time = ping_host(ip, timeout=2)
                
                if success:
                    self._log_activity(f"✓ {ip} is reachable (Response: {response_time}ms)")
                    self._update_progress(f"Ping successful: {response_time}ms", 100)
                    messagebox.showinfo("Ping Successful", 
                                       f"{ip} is reachable\nResponse time: {response_time}ms")
                else:
                    self._log_activity(f"✗ {ip} is unreachable")
                    self._update_progress("Ping failed", 100)
                    messagebox.showwarning("Ping Failed", 
                                          f"{ip} is unreachable\n\nPlease check:\n• IP address is correct\n• Device is powered on\n• Network connection is working")
                
            except Exception as e:
                self._log_activity(f"Error pinging {ip}: {str(e)}")
                messagebox.showerror("Ping Error", f"Error: {str(e)}")
            finally:
                self._update_progress("Ready", 0)
        
        self._run_task_async(task)
    
    def _on_ping_all(self):
        """Ping all APs in the credential manager."""
        try:
            from credential_manager_v2 import CredentialManager
            creds_manager = CredentialManager()
            all_credentials = creds_manager.get_all()
            
            if not all_credentials:
                messagebox.showinfo("No APs Found", "No Access Points configured in credential manager.\n\nPlease add AP credentials first.")
                return
            
            # Log activity
            self.user_manager.log_activity(
                username=self.current_user['username'],
                activity_type='Ping All APs',
                description=f'Pinging all {len(all_credentials)} APs in credentials',
                details={'ap_count': len(all_credentials)}
            )
            
            # Show confirmation dialog
            total = len(all_credentials)
            response = messagebox.askyesno(
                "Confirm Ping All APs",
                f"This will ping ALL {total} Access Points in the database.\n\n"
                f"This operation may take several minutes.\n\n"
                f"Do you want to continue?",
                icon='warning'
            )
            
            if not response:
                self._log_activity("Ping All APs operation cancelled by user")
                return
            
            # Create stop flag and show stop button
            self.stop_ping_flag = False
            self.ping_all_btn.pack_forget()
            self.stop_ping_btn.pack(side="left", padx=(0, 5))
            
            def task():
                try:
                    total = len(all_credentials)
                    online = 0
                    offline = 0
                    stopped = False
                    
                    self._log_activity(f"Starting ping test for {total} Access Points...")
                    self.results_text.delete("1.0", "end")
                    self.results_text.insert("end", f"Ping Results for {total} Access Points:\n")
                    self.results_text.insert("end", "=" * 60 + "\n\n")
                    
                    for idx, cred in enumerate(all_credentials, 1):
                        # Check stop flag
                        if self.stop_ping_flag:
                            stopped = True
                            self._log_activity(f"Ping test stopped by user at {idx}/{total}")
                            break
                        
                        ap_id = cred.get('ap_id', 'N/A')
                        ip = cred.get('ip_address', 'N/A')
                        
                        self._update_progress(f"Pinging AP {idx}/{total}: {ip}", (idx / total) * 100)
                        self._log_activity(f"Pinging {ap_id} ({ip})...")
                        
                        success, response_time = ping_host(ip, timeout=2)
                        
                        if success:
                            online += 1
                            status = f"✓ ONLINE  ({response_time}ms)"
                            self.results_text.insert("end", f"{status:25} {ap_id:20} {ip}\n", "online")
                            self._log_activity(f"  ✓ {ap_id} is online ({response_time}ms)")
                            # Log individual AP ping success
                            self.user_manager.log_activity(
                                username=self.current_user['username'],
                                activity_type='Ping AP Result',
                                description=f'AP is online ({response_time}ms)',
                                ap_id=ap_id,
                                success=True,
                                details={'ip_address': ip, 'response_time': response_time}
                            )
                        else:
                            offline += 1
                            status = "✗ OFFLINE"
                            self.results_text.insert("end", f"{status:25} {ap_id:20} {ip}\n", "offline")
                            self._log_activity(f"  ✗ {ap_id} is offline")
                            # Log individual AP ping failure
                            self.user_manager.log_activity(
                                username=self.current_user['username'],
                                activity_type='Ping AP Result',
                                description='AP is offline',
                                ap_id=ap_id,
                                success=False,
                                details={'ip_address': ip}
                            )
                    
                    # Configure text tags for colored output
                    self.results_text.tag_config("online", foreground="#28A745")
                    self.results_text.tag_config("offline", foreground="#DC3545")
                    
                    # Summary
                    self.results_text.insert("end", "\n" + "=" * 60 + "\n")
                    if stopped:
                        self.results_text.insert("end", f"STOPPED: Tested {idx} of {total} APs\n")
                        self.results_text.insert("end", f"Summary: {online} online, {offline} offline ({idx} tested)\n")
                        self._log_activity(f"Ping test stopped: {online} online, {offline} offline ({idx}/{total} tested)")
                        self._update_progress(f"Stopped: {online} online, {offline} offline ({idx}/{total} tested)", 0)
                        messagebox.showwarning("Ping Stopped", 
                                             f"Ping test was stopped by user.\n\n"
                                             f"Tested:  {idx} of {total}\n"
                                             f"Online:  {online}\n"
                                             f"Offline: {offline}")
                    else:
                        self.results_text.insert("end", f"Summary: {online} online, {offline} offline ({total} total)\n")
                        self._log_activity(f"Ping test complete: {online} online, {offline} offline")
                        self._update_progress(f"Complete: {online} online, {offline} offline", 100)
                        messagebox.showinfo("Ping Complete", 
                                           f"Ping test completed!\n\n"
                                           f"Online:  {online}\n"
                                           f"Offline: {offline}\n"
                                           f"Total:   {total}")
                    
                except Exception as e:
                    self._log_activity(f"Error during ping test: {str(e)}")
                    messagebox.showerror("Ping Error", f"Error: {str(e)}")
                finally:
                    self._update_progress("Ready", 0)
                    self.stop_ping_flag = False
                    # Restore buttons
                    self.stop_ping_btn.pack_forget()
                    self.ping_all_btn.pack(side="left")
            
            self._run_task_async(task)
            
        except ImportError:
            messagebox.showerror("Error", "Credential Manager not found")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading credentials: {str(e)}")
    
    def _on_stop_ping(self):
        """Stop the ongoing ping operation."""
        if hasattr(self, 'stop_ping_flag'):
            self.stop_ping_flag = True
            self._log_activity("Stop ping requested...")
            messagebox.showinfo("Stopping", "Stopping ping operation...\nPlease wait for current ping to complete.")
    
    def _on_ping_selected(self, selected_aps):
        """Ping selected APs from the connection status dialog.
        
        Args:
            selected_aps: List of AP dictionaries to ping
        """
        if not selected_aps:
            messagebox.showinfo("No APs", "No Access Points selected.")
            return
        
        total = len(selected_aps)
        response = messagebox.askyesno(
            "Confirm Ping Selected APs",
            f"This will ping {total} selected Access Point{'s' if total > 1 else ''}.\n\n"
            f"Do you want to continue?",
            icon='question'
        )
        
        if not response:
            self._log_activity("Ping selected APs operation cancelled by user")
            return
        
        def task():
            try:
                online = 0
                offline = 0
                
                self._log_activity(f"Starting ping test for {total} selected Access Point{'s' if total > 1 else ''}...")
                self.results_text.delete("1.0", "end")
                self.results_text.insert("end", f"Ping Results for {total} Selected AP{'s' if total > 1 else ''}:\n")
                self.results_text.insert("end", "=" * 60 + "\n\n")
                
                for idx, ap in enumerate(selected_aps, 1):
                    ap_id = ap.get('ap_id', 'N/A')
                    ip = ap.get('ip_address', 'N/A')
                    
                    self._update_progress(f"Pinging AP {idx}/{total}: {ip}", (idx / total) * 100)
                    self._log_activity(f"Pinging {ap_id} ({ip})...")
                    
                    success, response_time = ping_host(ip, timeout=2)
                    
                    if success:
                        online += 1
                        status = f"✓ ONLINE  ({response_time}ms)"
                        self.results_text.insert("end", f"{status:25} {ap_id:20} {ip}\n", "online")
                        self._log_activity(f"  ✓ {ap_id} is online ({response_time}ms)")
                    else:
                        offline += 1
                        status = "✗ OFFLINE"
                        self.results_text.insert("end", f"{status:25} {ap_id:20} {ip}\n", "offline")
                        self._log_activity(f"  ✗ {ap_id} is offline")
                
                # Configure text tags for colored output
                self.results_text.tag_config("online", foreground="#28A745")
                self.results_text.tag_config("offline", foreground="#DC3545")
                
                # Summary
                self.results_text.insert("end", "\n" + "=" * 60 + "\n")
                self.results_text.insert("end", f"Summary: {online} online, {offline} offline ({total} total)\n")
                
                self._log_activity(f"Ping test complete: {online} online, {offline} offline")
                self._update_progress(f"Complete: {online} online, {offline} offline", 100)
                
                messagebox.showinfo("Ping Complete", 
                                   f"Ping test completed!\n\n"
                                   f"Online:  {online}\n"
                                   f"Offline: {offline}\n"
                                   f"Total:   {total}")
                
            except Exception as e:
                self._log_activity(f"Error during ping test: {str(e)}")
                messagebox.showerror("Ping Error", f"Error: {str(e)}")
            finally:
                self._update_progress("Ready", 0)
        
        self._run_task_async(task)
    
    
    def _on_quick_connect(self):
        """Handle Quick Connect - connect to single AP and fetch status info."""
        ip = self.ip_var.get().strip()
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        # If only IP is provided, ask user for credential preference
        if ip and not username and not password:
            from tkinter import messagebox
            response = messagebox.askyesnocancel(
                "Credentials Required",
                "No credentials provided.\n\n"
                "Use default credentials?\n"
                "• Yes = Use username: admin\n"
                "• No = Enter credentials manually\n"
                "• Cancel = Abort",
                icon='question'
            )
            
            if response is None:  # Cancel
                return
            elif response:  # Yes - use defaults
                username = "admin"
                password = "admin"
                self.username_var.set(username)
                self.password_var.set(password)
            else:  # No - ask user to enter credentials
                messagebox.showinfo("Enter Credentials", "Please enter Username and Password in the fields above.")
                return
        
        if not ip or not username or not password:
            messagebox.showwarning("Missing Information", "Please enter IP Address, Username, and Password")
            return
        
        # Log activity
        self.user_manager.log_activity(
            username=self.current_user['username'],
            activity_type='Quick Connect',
            description=f'Connecting to AP at {ip}',
            details={'ip_address': ip}
        )
        
        def task():
            try:
                self._update_progress("Connecting to AP...", 0)
                
                # Load credential manager (will check for existing AP after extracting AP ID)
                from credential_manager_v2 import CredentialManager
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
                    
                    # Extract hardware/software info
                    serial_number = self._extract_xml_value(page_source, "Serial Number")
                    software_version = self._extract_xml_value(page_source, "Software Version")
                    firmware_version = self._extract_xml_value(page_source, "Firmware Version")
                    hardware_revision = self._extract_xml_value(page_source, "Hardware Revision")
                    build = self._extract_xml_value(page_source, "Build")
                    configuration_mode = self._extract_xml_value(page_source, "Configuration mode")
                    uptime = self._extract_xml_value(page_source, "Uptime")
                    mac_address = self._extract_xml_value(page_source, "MAC Address")
                    
                    # Extract status fields
                    service_status = self._extract_status_field(page_source, "service")
                    communication_daemon_status = self._extract_status_field(page_source, "daemon")
                    
                    # Extract connectivity status
                    connectivity_internet = self._extract_xml_value(page_source, "Internet")
                    connectivity_provisioning = self._extract_xml_value(page_source, "Provisioning")
                    connectivity_ntp_server = self._extract_xml_value(page_source, "NTP Server")
                    connectivity_apc_address = self._extract_xml_value(page_source, "APC Address")
                    
                    self.worker.log(f"AP Information retrieved:")
                    self.worker.log(f"  AP ID: {ap_id}")
                    self.worker.log(f"  Transmitter: {transmitter}")
                    self.worker.log(f"  IP Address: {ip_address}")
                    self.worker.log(f"  Store ID: {store_id}")
                    self.worker.log(f"  Serial: {serial_number}, SW: {software_version}, FW: {firmware_version}")
                    self.worker.log(f"  Service: {service_status}, Daemon: {communication_daemon_status}")
                    
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
                        
                        # Prepare update data with all fields
                        update_data = {
                            "ip_address": ip_address,
                            "store_id": store_id,
                            "username_webui": username,
                            "password_webui": password,
                            "type": transmitter,
                            "serial_number": serial_number,
                            "software_version": software_version,
                            "firmware_version": firmware_version,
                            "hardware_revision": hardware_revision,
                            "build": build,
                            "configuration_mode": configuration_mode,
                            "service_status": service_status,
                            "uptime": uptime,
                            "communication_daemon_status": communication_daemon_status,
                            "mac_address": mac_address,
                            "connectivity_internet": connectivity_internet,
                            "connectivity_provisioning": connectivity_provisioning,
                            "connectivity_ntp_server": connectivity_ntp_server,
                            "connectivity_apc_address": connectivity_apc_address
                        }
                        
                        # Update in database
                        success, msg = creds_manager.update_credential(store_id, ap_id, update_data)
                        if success:
                            self.worker.log("✓ AP information updated in database")
                        else:
                            self.worker.log(f"✗ Failed to update AP: {msg}")
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
                                "serial_number": serial_number,
                                "software_version": software_version,
                                "firmware_version": firmware_version,
                                "hardware_revision": hardware_revision,
                                "build": build,
                                "configuration_mode": configuration_mode,
                                "service_status": service_status,
                                "uptime": uptime,
                                "communication_daemon_status": communication_daemon_status,
                                "mac_address": mac_address,
                                "connectivity_internet": connectivity_internet,
                                "connectivity_provisioning": connectivity_provisioning,
                                "connectivity_ntp_server": connectivity_ntp_server,
                                "connectivity_apc_address": connectivity_apc_address
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
                    
                    # Log successful connection with AP ID
                    self.user_manager.log_activity(
                        username=self.current_user['username'],
                        activity_type='Quick Connect Complete',
                        description=f'Successfully connected to AP {ap_id}',
                        ap_id=ap_id,
                        success=True,
                        details={
                            'ip_address': ip_address,
                            'store_id': store_id,
                            'type': transmitter
                        }
                    )
                    
                    self._display_result({
                        "status": "success",
                        "message": f"Successfully connected to AP {ap_id}"
                    })
                    
                    # Enable browser operation buttons in status dialog
                    if self.worker.status_dialog:
                        self.root.after(0, lambda: self.worker.status_dialog.enable_action_buttons())
                    
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
    
    def _extract_status_field(self, html_text, context):
        """Extract Status field based on context (service or daemon).
        Service status appears first, daemon status appears later.
        """
        import re
        
        if context == "service":
            # Service status is the first Status field
            pattern = r'<th>Status:</th>\\s*<td[^>]*>([^<]*)</td>'
            match = re.search(pattern, html_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        elif context == "daemon":
            # Daemon status is the second Status field
            pattern = r'<th>Status:</th>\\s*<td[^>]*>([^<]*)</td>'
            matches = re.findall(pattern, html_text, re.IGNORECASE)
            if len(matches) >= 2:
                return matches[1].strip()
        
        return None
    
    def _show_about(self):
        """Show About dialog."""
        AboutDialog(self.root)
    
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
        
        # Log activity
        ap_ids = [ap.get('ap_id', 'Unknown') for ap in selected_aps]
        self.user_manager.log_activity(
            username=self.current_user['username'],
            activity_type='Browser Login',
            description=f'Opening browser with {len(selected_aps)} APs',
            details={'ap_count': len(selected_aps), 'ap_ids': ap_ids}
        )
        
        def task():
            self._update_progress(f"Connecting to {len(selected_aps)} APs...", 0)
            # Limit to 5 simultaneous connections for stability
            result = self.worker.open_browser_with_multiple_aps(selected_aps, max_parallel=5)
            self._display_result(result)
            
            # Log completion with actual connected APs
            if 'connected_ap_ids' in result and result['connected_ap_ids']:
                self.user_manager.log_activity(
                    username=self.current_user['username'],
                    activity_type='Browser Login Complete',
                    description=f'Successfully connected to {len(result["connected_ap_ids"])} APs',
                    success=True,
                    details={
                        'connected_ap_ids': result['connected_ap_ids'],
                        'failed_ap_ids': result.get('failed_ap_ids', [])
                    }
                )
                # Log individual AP connections
                for ap_id in result['connected_ap_ids']:
                    self.user_manager.log_activity(
                        username=self.current_user['username'],
                        activity_type='AP Connection',
                        description=f'Connected to AP via browser',
                        ap_id=ap_id,
                        success=True
                    )
            
            # Enable buttons if we have at least one successful connection (success or warning)
            if result["status"] in ["success", "warning"]:
                # Enable browser operation buttons in status dialog after successful login
                if self.worker.status_dialog:
                    self.root.after(0, lambda: self.worker.status_dialog.enable_action_buttons())
        
        self._run_task_async(task)
    
    # Legacy methods removed - now using multi-AP workflow
    

    
    def _on_check_provisioning(self):
        """Handle Step 3: Check Provisioning."""
        from provisioning_dialog import ProvisioningDialog
        
        # Log activity
        self.user_manager.log_activity(
            username=self.current_user['username'],
            activity_type='Provisioning Check',
            description='Checking provisioning status'
        )
        
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
        
        # Log activity
        self.user_manager.log_activity(
            username=self.current_user['username'],
            activity_type='SSH Management',
            description=f'Managing SSH ({action})',
            details={'action': action}
        )
        
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
            # Log activity
            self.user_manager.log_activity(
                username=self.current_user['username'],
                activity_type='Credential Manager',
                description='Opened credential manager'
            )
            
            # Open credential manager as a toplevel window with current user context
            CredentialManagerGUI(self.current_user, self.root)
            self._log_activity("Credential manager opened")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open credential manager: {e}")
    
    def _on_user_manager(self):
        """Open the user manager."""
        from user_manager_gui_v2 import UserManagerGUI
        
        # Log activity
        self.user_manager.log_activity(
            username=self.current_user['username'],
            activity_type='User Manager',
            description='Opened user manager'
        )
        
        try:
            UserManagerGUI(self.current_user, self.root)
            self._log_activity("User manager opened")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open user manager: {e}")
    
    def _on_audit_log(self):
        """Open the audit log window (Admin only)."""
        from user_manager_gui_v2 import AuditLogViewer
        
        # Verify admin status
        is_admin = (self.current_user.get('is_admin') or 
                   (self.current_user.get('role', '').lower() == 'admin'))
        if not is_admin:
            messagebox.showerror("Access Denied", "Only administrators can view audit logs")
            return
        
        # Log activity
        self.user_manager.log_activity(
            username=self.current_user['username'],
            activity_type='Audit Log',
            description='Opened audit log window'
        )
        
        try:
            AuditLogViewer(self.root, self.user_manager)
            self._log_activity("Audit log opened")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open audit log: {e}")
    
    def _on_admin_settings(self):
        """Open the admin settings dialog (Admin only)."""
        from admin_settings import AdminSettingsDialog
        from database_manager import DatabaseManager
        
        # Verify admin status
        is_admin = (self.current_user.get('is_admin') or 
                   (self.current_user.get('role', '').lower() == 'admin'))
        if not is_admin:
            messagebox.showerror("Access Denied", "Only administrators can access admin settings")
            return
        
        # Log activity
        self.user_manager.log_activity(
            username=self.current_user['username'],
            activity_type='Admin Settings',
            description='Opened admin settings dialog'
        )
        
        try:
            db = DatabaseManager()
            AdminSettingsDialog(self.root, self.current_user, db)
            self._log_activity("Admin settings opened")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open admin settings: {e}")
    
    def _on_ap_support(self):
        """Open the AP Support system."""
        from ap_support_ui import APSearchDialog, APSupportWindow, MODERN_UI_AVAILABLE
        from database_manager import DatabaseManager
        
        # Import modern UI if available
        if MODERN_UI_AVAILABLE:
            from ap_support_ui_v3 import APSupportWindowModern
        
        # Log activity
        self.user_manager.log_activity(
            username=self.current_user['username'],
            activity_type='AP Support',
            description='Opened AP Support system'
        )
        
        try:
            # Open search dialog
            search_dialog = APSearchDialog(self.root, self.current_user['username'], DatabaseManager())
            self.root.wait_window(search_dialog.dialog)
            
            # If an AP was selected, open support window
            selected_ap = search_dialog.get_selected_ap()
            if selected_ap:
                # Use modern UI if available
                if MODERN_UI_AVAILABLE:
                    print(f"Opening modern UI for AP {selected_ap['ap_id']} from main app")
                    APSupportWindowModern(self.root, selected_ap, self.current_user['username'], 
                                  DatabaseManager(), browser_helper=self)
                else:
                    print(f"Opening classic UI for AP {selected_ap['ap_id']} from main app")
                    APSupportWindow(self.root, selected_ap, self.current_user['username'], 
                                  DatabaseManager(), browser_helper=self)
                self._log_activity(f"Opened support window for AP: {selected_ap['ap_id']}")
        except Exception as e:
            import traceback
            messagebox.showerror("Error", f"Failed to open AP Support: {e}\n\n{traceback.format_exc()}")
            self._log_activity(f"Error opening AP Support: {str(e)}")
    
    def _on_close_browser(self):
        """Handle Close Browser."""
        # Log activity
        self.user_manager.log_activity(
            username=self.current_user['username'],
            activity_type='Close Browser',
            description='Closing browser session'
        )
        
        def task():
            result = self.worker.close()
            self._display_result(result)
            self._update_progress("Ready", 0)
            self.root.after(0, lambda: self.login_btn.config(state="disabled"))
            self.root.after(0, lambda: self.start_recording_btn.config(state="disabled"))
            self.root.after(0, lambda: self.stop_recording_btn.config(state="disabled"))
            self.root.after(0, lambda: self.diagnostic_btn.config(state="disabled"))
            self.root.after(0, lambda: self.capture_btn.config(state="disabled"))
            # Disable action buttons in status dialog
            if self.worker.status_dialog:
                self.root.after(0, lambda: self.worker.status_dialog.disable_action_buttons())
        
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

