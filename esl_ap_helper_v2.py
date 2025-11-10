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

APP_NAME = "ESL AP Helper"
APP_VERSION = "0.2"
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

class WebAutomationWorker:
    """Worker for web automation tasks - maintains persistent browser."""
    def __init__(self, progress_callback, log_callback):
        self.progress = progress_callback
        self.log = log_callback
        self.driver = None
        self.is_logged_in = False
        self.recording = False
        self.recorded_events = []
        
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
        """Step 2: Populate login credentials in the form (does NOT submit)."""
        try:
            self.log("=== Step 2: Populating login credentials ===")
            
            if not self.driver:
                raise Exception("Browser not opened. Please run Step 1 first.")
            
            self.progress("Looking for login form...", 10)
            
            current_url = self.driver.current_url
            self.log(f"Current URL: {current_url}")
            
            # Try to find and populate login form fields
            try:
                self.log("Searching for username/password fields...")
                
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
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.worker = WebAutomationWorker(self._update_progress, self._log_activity)
        
        # Configure window
        w, h = self.settings.get("window_size", [800, 700])
        root.geometry(f"{w}x{h}")
        root.title(f"{APP_NAME} v{APP_VERSION}")
        
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
        
        # Step 1: Open Browser button
        self.open_browser_btn = ttk.Button(btn_frame, text="1. Open Browser", 
                                          command=self._on_open_browser, 
                                          style="Modern.TButton")
        self.open_browser_btn.pack(side="left", padx=(0, 10))
        
        # Step 2: Login button
        self.login_btn = ttk.Button(btn_frame, text="2. Login", 
                                    command=self._on_login, 
                                    state="disabled", style="Modern.TButton")
        self.login_btn.pack(side="left", padx=(0, 10))
        
        # Step 3: Check Provisioning button
        self.check_provisioning_btn = ttk.Button(btn_frame, text="3. Check Provisioning", 
                                                command=self._on_check_provisioning, 
                                                state="disabled", style="Modern.TButton")
        self.check_provisioning_btn.pack(side="left", padx=(0, 10))
        
        # Add a separator line
        ttk.Separator(btn_frame, orient="vertical").pack(side="left", fill="y", padx=10, pady=5)
        
        # Recording buttons
        self.start_recording_btn = ttk.Button(btn_frame, text="🔴 Start Recording", 
                                             command=self._on_start_recording, 
                                             state="disabled", style="Modern.TButton")
        self.start_recording_btn.pack(side="left", padx=(0, 10))
        
        self.stop_recording_btn = ttk.Button(btn_frame, text="⏹️ Stop Recording", 
                                            command=self._on_stop_recording, 
                                            state="disabled", style="Modern.TButton")
        self.stop_recording_btn.pack(side="left", padx=(0, 10))
        
        # Diagnostic button
        self.diagnostic_btn = ttk.Button(btn_frame, text="📊 Diagnostics", 
                                        command=self._on_diagnostics, 
                                        state="disabled", style="Modern.TButton")
        self.diagnostic_btn.pack(side="left", padx=(0, 10))
        
        # Add separator
        ttk.Separator(btn_frame, orient="vertical").pack(side="left", fill="y", padx=10, pady=5)
        
        # Credential Manager button
        self.credentials_btn = ttk.Button(btn_frame, text="🔑 Manage Credentials", 
                                         command=self._on_manage_credentials, 
                                         style="Modern.TButton")
        self.credentials_btn.pack(side="left", padx=(0, 10))
        
        # Capture Page button
        self.capture_btn = ttk.Button(btn_frame, text="📸 Capture Page", 
                                     command=self._on_capture_page, 
                                     state="disabled", style="Modern.TButton")
        self.capture_btn.pack(side="left", padx=(0, 10))
        
        # Close Browser button
        self.close_browser_btn = ttk.Button(btn_frame, text="Close Browser", 
                                           command=self._on_close_browser, 
                                           state="disabled", style="Modern.TButton")
        self.close_browser_btn.pack(side="left", padx=(0, 10))
        
        # Save Settings button
        ttk.Button(btn_frame, text="Save Settings", command=self._save_settings, style="Modern.TButton").pack(side="right")
        
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
    
    def _on_open_browser(self):
        """Handle Step 1: Open Browser."""
        def task():
            self._update_progress("Opening browser...", 0)
            result = self.worker.open_browser(self.ip_var.get())
            self._display_result(result)
            if result["status"] in ["success", "warning"]:
                self.root.after(0, lambda: self.login_btn.config(state="normal"))
                self.root.after(0, lambda: self.start_recording_btn.config(state="normal"))
                self.root.after(0, lambda: self.diagnostic_btn.config(state="normal"))
                self.root.after(0, lambda: self.capture_btn.config(state="normal"))
                self.root.after(0, lambda: self.close_browser_btn.config(state="normal"))
        
        self._run_task_async(task)
    
    def _on_login(self):
        """Handle Step 2: Login."""
        def task():
            self._update_progress("Logging in...", 0)
            result = self.worker.login(self.username_var.get(), self.password_var.get())
            self._display_result(result)
            if result["status"] == "success":
                self.root.after(0, lambda: self.check_provisioning_btn.config(state="normal"))
        
        self._run_task_async(task)
    
    def _on_check_provisioning(self):
        """Handle Step 3: Check Provisioning."""
        def task():
            self._update_progress("Checking provisioning...", 0)
            result = self.worker.check_provisioning()
            self._display_result(result)
        
        self._run_task_async(task)
    
    def _on_start_recording(self):
        """Handle Start Recording."""
        def task():
            self._update_progress("Starting recording...", 0)
            result = self.worker.start_recording()
            self._display_result(result)
            if result["status"] == "success":
                self.root.after(0, lambda: self.start_recording_btn.config(state="disabled"))
                self.root.after(0, lambda: self.stop_recording_btn.config(state="normal"))
            self._update_progress("Recording in progress...", 50)
        
        self._run_task_async(task)
    
    def _on_stop_recording(self):
        """Handle Stop Recording."""
        def task():
            self._update_progress("Stopping recording...", 0)
            result = self.worker.stop_recording()
            self._display_result(result)
            if result["status"] == "success":
                self.root.after(0, lambda: self.start_recording_btn.config(state="normal"))
                self.root.after(0, lambda: self.stop_recording_btn.config(state="disabled"))
            self._update_progress("Recording stopped", 100)
        
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
        import subprocess
        import sys
        
        # Get the path to the credential manager script
        credential_manager_path = Path(__file__).parent / "credential_manager_gui.py"
        
        if not credential_manager_path.exists():
            messagebox.showerror("Error", "Credential manager not found")
            return
        
        try:
            # Launch the credential manager in a separate process
            subprocess.Popen([sys.executable, str(credential_manager_path)])
            self._log_activity("Credential manager opened")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open credential manager: {e}")
    
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
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
