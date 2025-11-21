"""
Batch Browser Operations Tool - Perform browser operations on multiple APs
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict
import threading
import time
from batch_operations_base import BatchOperationWindow
from database_manager import DatabaseManager
from browser_manager import BrowserManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class BatchBrowserWindow(BatchOperationWindow):
    """Window for batch browser operations on multiple APs."""
    
    def __init__(self, parent, current_user, db_manager: DatabaseManager):
        """Initialize batch browser operations window."""
        self.operation_type = tk.StringVar(value="enable_ssh")
        self.browser_manager = None
        self.browser_lock = threading.Lock()  # Lock for browser operations
        
        super().__init__(parent, "Batch Browser Operations", current_user, db_manager)
    
    def _create_operation_controls(self):
        """Create browser operation-specific controls."""
        # Operation type selection
        op_frame = ttk.LabelFrame(self.operation_frame, text="Select Operation", padding=10)
        op_frame.pack(fill=tk.X, pady=(0, 10))
        
        operations = [
            ("Enable SSH Server", "enable_ssh"),
            ("Disable SSH Server", "disable_ssh"),
            ("Reboot AP", "reboot"),
            ("Check AP Status", "check_status")
        ]
        
        for text, value in operations:
            ttk.Radiobutton(
                op_frame,
                text=text,
                variable=self.operation_type,
                value=value
            ).pack(anchor=tk.W, pady=2)
        
        # Settings
        settings_frame = ttk.LabelFrame(self.operation_frame, text="Browser Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Max tabs
        tabs_frame = ttk.Frame(settings_frame)
        tabs_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(tabs_frame, text="Max Parallel Tabs:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.max_tabs_var = tk.IntVar(value=9)
        tabs_spin = ttk.Spinbox(tabs_frame, from_=1, to=15, width=10,
                               textvariable=self.max_tabs_var)
        tabs_spin.pack(side=tk.LEFT)
        
        ttk.Label(tabs_frame, text="(Recommended: 5-9 tabs)", 
                 foreground="gray").pack(side=tk.LEFT, padx=(10, 0))
        
        # Timeout
        timeout_frame = ttk.Frame(settings_frame)
        timeout_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(timeout_frame, text="Page Timeout:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.timeout_var = tk.IntVar(value=30)
        timeout_spin = ttk.Spinbox(timeout_frame, from_=10, to=120, width=10,
                                   textvariable=self.timeout_var)
        timeout_spin.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(timeout_frame, text="seconds").pack(side=tk.LEFT)
        
        # Help text
        help_text = ttk.Label(
            self.operation_frame,
            text="ℹ Browser will open multiple tabs simultaneously. Each AP will be processed in its own tab. "
                 "Status updates show progress for each AP.",
            foreground="gray",
            wraplength=1000,
            font=('Segoe UI', 9)
        )
        help_text.pack(anchor=tk.W, pady=(10, 0))
    
    def _get_operation_description(self) -> str:
        """Get operation description for confirmation dialog."""
        op_type = self.operation_type.get()
        
        descriptions = {
            "enable_ssh": "Enable SSH Server on all marked APs via web interface",
            "disable_ssh": "Disable SSH Server on all marked APs via web interface",
            "reboot": "Reboot all marked APs via web interface",
            "check_status": "Check status of all marked APs via web interface",
            "read_config": "Read configuration from all marked APs",
            "custom": f"Custom action: {self.custom_text.get('1.0', tk.END).strip()}"
        }
        
        return descriptions.get(op_type, "Unknown operation")
    
    def _get_operation_params(self) -> dict:
        """Read tkinter variables in main thread."""
        return {
            'max_tabs': self.max_tabs_var.get(),
            'timeout': self.timeout_var.get(),
            'operation_type': self.operation_type.get()
        }
    
    def _run_operation(self, operation_params: dict = None):
        """Run batch browser operation with parallel tabs."""
        # Use parameters passed from main thread
        max_tabs = operation_params.get('max_tabs', 9)
        timeout = operation_params.get('timeout', 30)
        operation_type = operation_params.get('operation_type', 'check_status')
        
        self.current_timeout = timeout
        self.current_operation = operation_type
        
        try:
            # Initialize browser
            self.operation_queue.put(('log', 'Initializing browser...', 'info'))
            self.browser_manager = BrowserManager(
                log_callback=lambda msg: self.operation_queue.put(('log', msg, 'info'))
            )
            
            self.browser_manager.initialize_browser()
            self.operation_queue.put(('log', 'Browser initialized successfully', 'success'))
            
            # Process APs in batches of max_tabs
            total = len(self.selected_aps)
            completed = 0
            
            for batch_num, i in enumerate(range(0, total, max_tabs), 1):
                if not self.operation_running:
                    break
                
                batch = self.selected_aps[i:i + max_tabs]
                self.operation_queue.put(('log', 
                    f'Opening batch {batch_num} with {len(batch)} tabs...', 'info'))
                
                # Phase 1: Open tabs and navigate all to their URLs (sequentially to avoid issues)
                tab_handles = {}
                self.operation_queue.put(('log', f'Phase 1: Opening tabs and navigating to APs...', 'info'))
                
                for idx, ap in enumerate(batch):
                    ap_id = ap['ap_id']
                    ip = ap.get('ip_address', '')
                    
                    try:
                        # Open new tab (or use first tab for first AP)
                        if idx > 0:
                            self.browser_manager.driver.execute_script("window.open('');")
                            self.browser_manager.driver.switch_to.window(
                                self.browser_manager.driver.window_handles[-1]
                            )
                        
                        handle = self.browser_manager.driver.current_window_handle
                        tab_handles[ap_id] = {'handle': handle, 'ap': ap, 'index': idx}
                        
                        # Navigate to AP immediately
                        if ip:
                            url = f"http://{ip}"
                            self.operation_queue.put(('status', ap_id, 'Loading', f'Navigating to {ip}', '-'))
                            self.browser_manager.driver.get(url)
                        else:
                            self.operation_queue.put(('status', ap_id, 'Failed', 'No IP address', '-'))
                        
                    except Exception as e:
                        self.operation_queue.put(('status', ap_id, 'Failed', f'Tab error: {str(e)[:30]}', '-'))
                        self.operation_queue.put(('log', f"{ap_id}: Tab error - {str(e)}", 'error'))
                
                # Phase 2: Process all tabs in parallel now that they're loaded
                self.operation_queue.put(('log', f'Phase 2: Processing all tabs in parallel...', 'info'))
                
                threads = []
                for ap_id, tab_info in tab_handles.items():
                    if not self.operation_running:
                        break
                    
                    thread = threading.Thread(
                        target=self._process_ap_in_tab,
                        args=(tab_info['ap'], tab_info['handle'], tab_info['index']),
                        daemon=True
                    )
                    threads.append((thread, ap_id))
                    thread.start()
                
                # Wait for all threads to complete
                for thread, ap_id in threads:
                    thread.join()
                    completed += 1
                    progress = (completed / total) * 100
                    self.operation_queue.put(('progress', progress, f"Processed {completed} of {total}"))
                
                # Close all tabs in this batch (except the first one for next batch)
                try:
                    current_handles = self.browser_manager.driver.window_handles
                    if len(current_handles) > 1:
                        for handle in current_handles[1:]:
                            try:
                                self.browser_manager.driver.switch_to.window(handle)
                                self.browser_manager.driver.close()
                            except:
                                pass
                        # Switch back to first tab
                        if current_handles:
                            self.browser_manager.driver.switch_to.window(current_handles[0])
                except:
                    pass
            
        except Exception as e:
            self.operation_queue.put(('log', f'Fatal error: {str(e)}', 'error'))
        
        finally:
            # Clean up browser
            if self.browser_manager and self.browser_manager.driver:
                try:
                    self.browser_manager.driver.quit()
                    self.operation_queue.put(('log', 'Browser closed', 'info'))
                except:
                    pass
            
            self.operation_queue.put(('complete', None, None))
    
    def _process_ap_in_tab(self, ap: Dict, tab_handle: str, tab_index: int):
        """Process a single AP in its assigned tab (runs in parallel thread)."""
        ap_id = ap['ap_id']
        
        try:
            # Switch to this AP's tab (with lock to prevent race conditions during switch)
            with self.browser_lock:
                self.browser_manager.driver.switch_to.window(tab_handle)
                current_handle = self.browser_manager.driver.current_window_handle
            
            # Verify we're in the correct tab
            if current_handle != tab_handle:
                self.operation_queue.put(('status', ap_id, 'Failed', 'Tab switch failed', '-'))
                return
            
            # Update status
            self.operation_queue.put(('status', ap_id, 'Running', 'Logging in...', '-'))
            
            # Execute the operation (page already loaded, just need to login and operate)
            success, result = self._execute_browser_operation_in_loaded_tab(ap, tab_handle)
            
            # Update final status
            status = 'Success' if success else 'Failed'
            tag = 'success' if success else 'error'
            self.operation_queue.put(('status', ap_id, status, result, '1'))
            self.operation_queue.put(('log', f"{ap_id}: {result}", tag))
            
        except Exception as e:
            self.operation_queue.put(('status', ap_id, 'Failed', f'Error: {str(e)[:50]}', '-'))
            self.operation_queue.put(('log', f"{ap_id}: Error - {str(e)}", 'error'))
    
    def _execute_browser_operation_in_loaded_tab(self, ap: Dict, tab_handle: str) -> tuple[bool, str]:
        """
        Execute browser operation on a single AP (tab already loaded).
        
        Returns:
            tuple: (success, result_message)
        """
        # Use stored parameters from main thread
        operation = self.current_operation
        timeout = self.current_timeout
        
        ap_id = ap.get('ap_id', '')
        
        # Get credentials
        username = ap.get('username_webui', 'admin')
        password = ap.get('password_webui', '')
        
        # If not in ap dict, try to load from credential manager
        if not password:
            from credential_manager import CredentialManager
            cred_manager = CredentialManager()
            cred_manager.load()
            
            # Find credential for this AP
            credential = cred_manager.find_by_ap_id(ap_id)
            if credential:
                username = credential.get('username', username)
                password = credential.get('password', '')
        
        if not password:
            return False, f"No password configured"
        
        # ALL Selenium operations must be locked since WebDriver is not thread-safe
        with self.browser_lock:
            try:
                # Switch to this tab
                self.browser_manager.driver.switch_to.window(tab_handle)
                
                # Wait for page load
                time.sleep(2)
                
                # Check for Cato Networks warning
                try:
                    if "cato" in self.browser_manager.driver.page_source.lower():
                        continue_btn = WebDriverWait(self.browser_manager.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]"))
                        )
                        continue_btn.click()
                        time.sleep(1)
                except:
                    pass
                
                # Login
                username_field = WebDriverWait(self.browser_manager.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                username_field.clear()
                username_field.send_keys(username)
                
                password_field = self.browser_manager.driver.find_element(By.NAME, "password")
                password_field.clear()
                password_field.send_keys(password)
                
                login_btn = self.browser_manager.driver.find_element(By.XPATH, "//input[@type='submit']")
                login_btn.click()
                
                time.sleep(3)  # Wait for login to complete
                
                # For now, just return success after login
                return True, "Logged in successfully"
                
            except TimeoutException:
                return False, "Login page timeout"
            except NoSuchElementException:
                return False, "Login elements not found"
            except Exception as e:
                return False, f"Login error: {str(e)[:50]}"
    
    def _enable_ssh_server(self) -> tuple[bool, str]:
        """Enable SSH server on AP."""
        try:
            # Navigate to SSH settings
            # This is example code - adjust for actual AP interface
            ssh_link = WebDriverWait(self.browser_manager.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'SSH') or contains(text(), 'Services')]"))
            )
            ssh_link.click()
            time.sleep(2)
            
            # Enable SSH checkbox
            ssh_checkbox = self.browser_manager.driver.find_element(
                By.XPATH, "//input[@type='checkbox' and contains(@name, 'ssh')]"
            )
            
            if not ssh_checkbox.is_selected():
                ssh_checkbox.click()
                
                # Save/Apply
                apply_btn = self.browser_manager.driver.find_element(
                    By.XPATH, "//input[@type='submit' and (@value='Apply' or @value='Save')]"
                )
                apply_btn.click()
                time.sleep(2)
                
                return True, "SSH server enabled"
            else:
                return True, "SSH server already enabled"
        
        except Exception as e:
            return False, f"Failed to enable SSH: {str(e)[:30]}"
    
    def _disable_ssh_server(self) -> tuple[bool, str]:
        """Disable SSH server on AP."""
        try:
            # Navigate to SSH settings
            ssh_link = WebDriverWait(self.browser_manager.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'SSH') or contains(text(), 'Services')]"))
            )
            ssh_link.click()
            time.sleep(2)
            
            # Disable SSH checkbox
            ssh_checkbox = self.browser_manager.driver.find_element(
                By.XPATH, "//input[@type='checkbox' and contains(@name, 'ssh')]"
            )
            
            if ssh_checkbox.is_selected():
                ssh_checkbox.click()
                
                # Save/Apply
                apply_btn = self.browser_manager.driver.find_element(
                    By.XPATH, "//input[@type='submit' and (@value='Apply' or @value='Save')]"
                )
                apply_btn.click()
                time.sleep(2)
                
                return True, "SSH server disabled"
            else:
                return True, "SSH server already disabled"
        
        except Exception as e:
            return False, f"Failed to disable SSH: {str(e)[:30]}"
    
    def _reboot_ap(self) -> tuple[bool, str]:
        """Reboot the AP."""
        try:
            # Navigate to system/reboot page
            reboot_link = WebDriverWait(self.browser_manager.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Reboot') or contains(text(), 'System')]"))
            )
            reboot_link.click()
            time.sleep(2)
            
            # Click reboot button
            reboot_btn = self.browser_manager.driver.find_element(
                By.XPATH, "//input[@type='submit' and contains(@value, 'Reboot')]"
            )
            reboot_btn.click()
            
            # Confirm if needed
            try:
                confirm_btn = WebDriverWait(self.browser_manager.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='OK']"))
                )
                confirm_btn.click()
            except:
                pass
            
            return True, "Reboot initiated"
        
        except Exception as e:
            return False, f"Failed to reboot: {str(e)[:30]}"
    
    def _check_ap_status(self) -> tuple[bool, str]:
        """Check AP status."""
        try:
            # Get page title or system info
            page_source = self.browser_manager.driver.page_source
            
            # Extract useful info (example)
            if "Online" in page_source or "Connected" in page_source:
                return True, "AP is online and responding"
            else:
                return True, "AP responded but status unclear"
        
        except Exception as e:
            return False, f"Failed to check status: {str(e)[:30]}"
    
    def _read_config(self) -> tuple[bool, str]:
        """Read configuration from AP."""
        try:
            # This is a placeholder - implement based on AP interface
            return True, "Configuration read (not fully implemented)"
        
        except Exception as e:
            return False, f"Failed to read config: {str(e)[:30]}"


def main():
    """Test the batch browser window."""
    root = tk.Tk()
    root.withdraw()
    
    from database_manager import DatabaseManager
    db = DatabaseManager()
    
    window = BatchBrowserWindow(None, "test_user", db)
    window.window.mainloop()


if __name__ == '__main__':
    main()
