"""
ESL AP Helper - Web automation tool for ESL AP management

Requirements:
    python -m pip install selenium webdriver-manager
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from pathlib import Path
import json

# Selenium imports will be added after installation
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

APP_NAME = "ESL AP Helper"
APP_VERSION = "0.1"
APP_RELEASE_DATE = "2025-11-10"
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

class WebAutomationWorker(threading.Thread):
    """Worker thread for web automation tasks."""
    def __init__(self, ip_address, username, password, task_type, progress_callback, finished_callback, stop_event):
        super().__init__(daemon=True)
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.task_type = task_type
        self.progress = progress_callback
        self.finished = finished_callback
        self.stop_event = stop_event
        self.driver = None
        
    def run(self):
        try:
            self.progress("Initializing browser...", 0)
            
            # Setup Chrome options
            chrome_options = Options()
            # chrome_options.add_argument('--headless')  # Uncomment to run without visible browser
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Ignore SSL certificate errors
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--allow-insecure-localhost')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            # Accept insecure certificates
            chrome_options.set_capability('acceptInsecureCerts', True)
            
            # Initialize Chrome driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
            if self.stop_event.is_set():
                return self.finished(None, cancelled=True, error=None)
            
            # Navigate to IP address with embedded credentials for HTTP Basic Auth
            # This bypasses the browser's authentication popup
            if not self.ip_address.startswith(('http://', 'https://')):
                # Build URL with credentials embedded
                url = f"https://{self.username}:{self.password}@{self.ip_address}"
            else:
                # If protocol already specified, insert credentials
                protocol = 'https://' if 'https://' in self.ip_address else 'http://'
                ip_without_protocol = self.ip_address.replace('https://', '').replace('http://', '')
                url = f"{protocol}{self.username}:{self.password}@{ip_without_protocol}"
            
            self.progress(f"Navigating to {self.ip_address} with credentials...", 10)
            self.driver.get(url)
            
            if self.stop_event.is_set():
                return self.finished(None, cancelled=True, error=None)
            
            # Wait for page to load after authentication
            import time
            time.sleep(2)
            self.progress("Authentication completed", 30)
            
            # Save screenshot after login
            screenshot_path = Path(__file__).parent / "after_auth.png"
            self.driver.save_screenshot(str(screenshot_path))
            self.progress(f"Screenshot saved to {screenshot_path}", 35)
            
            if self.stop_event.is_set():
                return self.finished(None, cancelled=True, error=None)
            
            # Save page source for debugging
            source_path = Path(__file__).parent / "main_page.html"
            with open(source_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            self.progress(f"Page source saved to {source_path}", 40)
            
            # Execute task based on type
            if self.task_type == "check_provisioning":
                result = self._check_provisioning_status()
            else:
                result = {"error": "Unknown task type"}
            
            self.finished(result, cancelled=False, error=None)
            
        except Exception as e:
            import traceback
            self.finished(None, cancelled=False, error=str(e) + "\n" + traceback.format_exc())
        finally:
            if self.driver:
                self.driver.quit()
    
    def _login(self):
        """Handle login to the web interface."""
        try:
            import time
            
            # Wait for the page to load and dialog to appear
            time.sleep(2)
            self.progress("Waiting for login dialog...", 35)
            
            # Save screenshot for debugging
            screenshot_path = Path(__file__).parent / "login_page.png"
            self.driver.save_screenshot(str(screenshot_path))
            self.progress(f"Screenshot saved to {screenshot_path}", 37)
            
            # Save page source for inspection
            source_path = Path(__file__).parent / "login_page.html"
            with open(source_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            self.progress(f"Page source saved to {source_path}", 40)
            
            # Wait for dialog/modal to be visible
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='text' or @type='password']"))
                )
                self.progress("Login dialog detected", 42)
            except:
                self.progress("No input fields detected yet, continuing...", 42)
            
            # Try to find login fields using multiple strategies
            username_field = None
            password_field = None
            
            # Strategy 1: Try common field names
            for name in ["username", "user", "login", "userName", "j_username"]:
                try:
                    username_field = self.driver.find_element(By.NAME, name)
                    self.progress(f"Found username field with name='{name}'", 42)
                    break
                except:
                    pass
            
            # Strategy 2: Try by ID
            if not username_field:
                for id_name in ["username", "user", "login", "userName", "userid"]:
                    try:
                        username_field = self.driver.find_element(By.ID, id_name)
                        self.progress(f"Found username field with id='{id_name}'", 42)
                        break
                    except:
                        pass
            
            # Strategy 3: Try by input type
            if not username_field:
                try:
                    username_field = self.driver.find_element(By.XPATH, "//input[@type='text']")
                    self.progress("Found username field by type='text'", 42)
                except:
                    pass
            
            if not username_field:
                raise Exception("Could not find username field. Please check login_page.html and login_page.png")
            
            # Find password field
            for name in ["password", "passwd", "pwd", "pass", "j_password"]:
                try:
                    password_field = self.driver.find_element(By.NAME, name)
                    self.progress(f"Found password field with name='{name}'", 44)
                    break
                except:
                    pass
            
            if not password_field:
                for id_name in ["password", "passwd", "pwd", "pass"]:
                    try:
                        password_field = self.driver.find_element(By.ID, id_name)
                        self.progress(f"Found password field with id='{id_name}'", 44)
                        break
                    except:
                        pass
            
            if not password_field:
                try:
                    password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
                    self.progress("Found password field by type='password'", 44)
                except:
                    pass
            
            if not password_field:
                raise Exception("Could not find password field. Please check login_page.html and login_page.png")
            
            # Enter credentials
            username_field.clear()
            username_field.send_keys(self.username)
            self.progress("Username entered", 46)
            
            password_field.clear()
            password_field.send_keys(self.password)
            self.progress("Password entered", 48)
            
            # Find and click login button (specifically looking for "Sign in" from the screenshot)
            login_button = None
            for xpath in [
                "//button[contains(text(), 'Sign in')]",
                "//button[contains(., 'Sign in')]",
                "//input[@value='Sign in']",
                "//button[@type='submit']",
                "//input[@type='submit']",
                "//button[contains(text(), 'Login')]",
                "//input[@value='Login']"
            ]:
                try:
                    login_button = self.driver.find_element(By.XPATH, xpath)
                    self.progress(f"Found login button: 'Sign in'", 49)
                    break
                except:
                    pass
            
            if not login_button:
                raise Exception("Could not find login button. Please check login_page.html")
            
            login_button.click()
            self.progress("Login button clicked", 50)
            
            # Wait for login to process and page to load
            time.sleep(3)
            
            # Save post-login screenshot
            screenshot_path_after = Path(__file__).parent / "after_login.png"
            self.driver.save_screenshot(str(screenshot_path_after))
            self.progress(f"Post-login screenshot saved", 55)
            
            self.progress("Login successful", 60)
            
        except Exception as e:
            raise Exception(f"Login failed: {str(e)}")
    
    def _check_provisioning_status(self):
        """Check provisioning status in the web interface."""
        try:
            self.progress("Checking provisioning status...", 60)
            
            # Navigate to provisioning menu (adjust based on actual interface)
            # This is a placeholder - will need to be customized based on actual UI
            
            # Example: Click on menu item
            # menu_item = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Provisioning')]")
            # menu_item.click()
            
            self.progress("Reading provisioning data...", 80)
            
            # Example: Extract provisioning status
            # status_element = self.driver.find_element(By.ID, "provisioning-status")
            # status = status_element.text
            
            # Placeholder result
            result = {
                "status": "Provisioned",
                "details": "Placeholder - needs actual selectors from the web interface"
            }
            
            self.progress("Provisioning check complete", 100)
            return result
            
        except Exception as e:
            raise Exception(f"Failed to check provisioning: {str(e)}")

class App:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.worker = None
        self.stop_event = threading.Event()
        
        # Configure window
        w, h = self.settings.get("window_size", [700, 600])
        root.geometry(f"{w}x{h}")
        root.title(APP_NAME)
        
        self.worker, self.stop_event = None, threading.Event()
        self._build_ui()
        root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _build_ui(self):
        # Configure modern style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Modern color scheme
        bg_color = "#F5F5F5"
        frame_bg = "#FFFFFF"
        accent_color = "#28A745"  # Green color
        
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
        
        # Connection Settings Frame
        conn_frame = ttk.LabelFrame(main_frame, text="Connection Settings", padding=15, style="Modern.TLabelframe")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # IP Address
        ttk.Label(conn_frame, text="IP Address:", style="Modern.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.ip_var = tk.StringVar(value=self.settings.get("last_ip", ""))
        ip_entry = ttk.Entry(conn_frame, textvariable=self.ip_var, width=20, style="Modern.TEntry", font=("Segoe UI", 10))
        ip_entry.grid(row=0, column=1, sticky="w", padx=5)
        
        # Username
        ttk.Label(conn_frame, text="Username:", style="Modern.TLabel").grid(row=0, column=2, sticky="w", padx=(20, 10))
        self.username_var = tk.StringVar(value=self.settings.get("last_username", ""))
        username_entry = ttk.Entry(conn_frame, textvariable=self.username_var, width=20, style="Modern.TEntry", font=("Segoe UI", 10))
        username_entry.grid(row=0, column=3, sticky="w", padx=5)
        
        # Password
        ttk.Label(conn_frame, text="Password:", style="Modern.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        self.password_var = tk.StringVar(value=self.settings.get("last_password", ""))
        password_entry = ttk.Entry(conn_frame, textvariable=self.password_var, width=20, show="*", style="Modern.TEntry", font=("Segoe UI", 10))
        password_entry.grid(row=1, column=1, sticky="w", padx=5, pady=(10, 0))
        
        # Show password checkbox
        self.show_password_var = tk.BooleanVar(value=False)
        show_pwd_check = ttk.Checkbutton(conn_frame, text="Show password", variable=self.show_password_var, 
                                         command=lambda: password_entry.config(show="" if self.show_password_var.get() else "*"))
        show_pwd_check.grid(row=1, column=2, columnspan=2, sticky="w", padx=(20, 0), pady=(10, 0))
        
        # Operations Frame
        ops_frame = ttk.LabelFrame(main_frame, text="Operations", padding=15, style="Modern.TLabelframe")
        ops_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Buttons
        btn_frame = ttk.Frame(ops_frame, style="Modern.TFrame")
        btn_frame.pack(fill="x")
        
        # Check Provisioning button
        self.provisioning_btn = ttk.Button(btn_frame, text="Check Provisioning Status", 
                                          command=lambda: self._start_task("check_provisioning"), 
                                          style="Modern.TButton")
        self.provisioning_btn.pack(side="left", padx=(0, 10))
        
        # Cancel button
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self._on_cancel, state="disabled", style="Modern.TButton")
        self.cancel_btn.pack(side="left", padx=(0, 10))
        
        # Save Settings button
        ttk.Button(btn_frame, text="Save Settings", command=self._save_settings, style="Modern.TButton").pack(side="right")
        
        # Progress bar
        self.progress_var = tk.IntVar()
        style.configure("Modern.Horizontal.TProgressbar", background=accent_color, troughcolor="#E0E0E0", borderwidth=0, thickness=8)
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100, style="Modern.Horizontal.TProgressbar")
        self.progress_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, style="Modern.TLabel", font=("Segoe UI", 10, "italic"))
        status_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Activity Log
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding=10, style="Modern.TLabelframe")
        log_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        main_frame.rowconfigure(4, weight=1)
        
        # Log text widget with scrollbar
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side="right", fill="y")
        
        self.log_text = tk.Text(log_frame, height=15, width=80, wrap="word", 
                               yscrollcommand=log_scroll.set, font=("Consolas", 9),
                               bg="white", fg="#333333", relief="flat", borderwidth=0)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        # Results Frame
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10, style="Modern.TLabelframe")
        results_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        self.results_text = tk.Text(results_frame, height=8, width=80, wrap="word",
                                    font=("Segoe UI", 10), bg="#F9F9F9", fg="#333333",
                                    relief="flat", borderwidth=0)
        self.results_text.pack(fill="both", expand=True)
    
    def _log(self, message):
        """Add message to activity log."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
    
    def _set_status(self, message, percent):
        """Update status and progress."""
        self.status_var.set(message)
        if percent >= 0:
            self.progress_var.set(percent)
    
    def _start_task(self, task_type):
        """Start a web automation task."""
        ip = self.ip_var.get().strip()
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not ip:
            messagebox.showerror("Error", "Please enter an IP address")
            return
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        self._log(f"Starting task: {task_type}")
        self._set_status("Starting...", 0)
        
        # Disable buttons
        self.provisioning_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        
        # Clear previous results
        self.results_text.delete("1.0", "end")
        
        # Start worker thread
        self.stop_event.clear()
        self.worker = WebAutomationWorker(ip, username, password, task_type,
                                         self._worker_progress, self._worker_finished, self.stop_event)
        self.worker.start()
    
    def _on_cancel(self):
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            self._log("Cancelling operation...")
            self._set_status("Cancelling...", -1)
            self.cancel_btn.config(state="disabled")
    
    def _worker_progress(self, message, percent):
        def ui():
            self._set_status(message, percent)
            self._log(message)
        self.root.after(0, ui)
    
    def _worker_finished(self, result, cancelled, error):
        def on_finish():
            self.worker = None
            self.provisioning_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")
            
            if error:
                self._log("Error: " + str(error))
                messagebox.showerror("Error", str(error))
                self._set_status("Error", 0)
            elif cancelled:
                self._log("Operation cancelled")
                self._set_status("Cancelled", 0)
            else:
                self._log("Operation completed successfully")
                self._set_status("Completed", 100)
                
                # Display results
                if result:
                    result_text = json.dumps(result, indent=2)
                    self.results_text.delete("1.0", "end")
                    self.results_text.insert("1.0", result_text)
        
        self.root.after(0, on_finish)
    
    def _save_settings(self):
        """Save current settings."""
        self.settings["last_ip"] = self.ip_var.get()
        self.settings["last_username"] = self.username_var.get()
        self.settings["last_password"] = self.password_var.get()
        save_settings(self.settings)
        self._log("Settings saved")
        messagebox.showinfo("Success", "Settings saved successfully")
    
    def _on_close(self):
        try:
            self.settings["window_size"] = [self.root.winfo_width(), self.root.winfo_height()]
            save_settings(self.settings)
        except:
            pass
        if self.worker and self.worker.is_alive():
            if messagebox.askyesno("Exit", "An operation is running. Exit anyway?"):
                self.stop_event.set()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    if webdriver is None:
        print("Please install required packages:")
        print("pip install selenium webdriver-manager")
        return
    
    root = tk.Tk()
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
