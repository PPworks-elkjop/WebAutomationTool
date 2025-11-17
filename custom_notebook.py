"""
Custom Notebook widget with full control over tab appearance
"""
import tkinter as tk


class CustomNotebook:
    """Custom notebook with button-based tabs for full styling control."""
    
    def __init__(self, parent, tab_font=('Segoe UI', 15), tab_height=45):
        self.parent = parent
        self.tab_font = tab_font
        self.tab_height = tab_height
        
        self.tabs = []  # List of (tab_button, content_frame) tuples
        self.current_tab = None
        
        # Main container
        self.container = tk.Frame(parent, bg="#F0F0F0")
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Tab bar container with scrolling support
        tab_bar_container = tk.Frame(self.container, bg="#E9ECEF", height=tab_height)
        tab_bar_container.pack(fill=tk.X, side=tk.TOP)
        tab_bar_container.pack_propagate(False)
        
        # Left scroll button
        left_scroll_btn = tk.Button(tab_bar_container, text="◀", font=('Segoe UI', 10),
                                    bg="#D0D0D0", fg="#495057", relief=tk.FLAT,
                                    cursor="hand2", padx=8, pady=8, bd=0,
                                    activebackground="#B0B0B0", activeforeground="#212529")
        left_scroll_btn.pack(side=tk.LEFT, fill=tk.Y)
        
        # Canvas for scrollable tab bar
        self.tab_canvas = tk.Canvas(tab_bar_container, bg="#E9ECEF", height=tab_height, 
                                     highlightthickness=0, bd=0)
        self.tab_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Right scroll button
        right_scroll_btn = tk.Button(tab_bar_container, text="▶", font=('Segoe UI', 10),
                                     bg="#D0D0D0", fg="#495057", relief=tk.FLAT,
                                     cursor="hand2", padx=8, pady=8, bd=0,
                                     activebackground="#B0B0B0", activeforeground="#212529")
        right_scroll_btn.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Scrollable frame inside canvas
        self.tab_bar = tk.Frame(self.tab_canvas, bg="#E9ECEF")
        self.tab_canvas_window = self.tab_canvas.create_window((0, 0), window=self.tab_bar, anchor="nw")
        
        # Configure scrolling
        self.tab_bar.bind("<Configure>", lambda e: self.tab_canvas.configure(scrollregion=self.tab_canvas.bbox("all")))
        
        # Scroll button commands
        def scroll_left():
            self.tab_canvas.xview_scroll(-1, "units")
        
        def scroll_right():
            self.tab_canvas.xview_scroll(1, "units")
        
        left_scroll_btn.config(command=scroll_left)
        right_scroll_btn.config(command=scroll_right)
        
        # Content area
        self.content_area = tk.Frame(self.container, bg="#FFFFFF")
        self.content_area.pack(fill=tk.BOTH, expand=True)
    
    def add(self, frame, text, closeable=False, close_callback=None):
        """Add a new tab."""
        # Create tab container to hold tab button and close button
        tab_container = tk.Frame(self.tab_bar, bg="#E9ECEF")
        tab_container.pack(side=tk.LEFT, fill=tk.Y, padx=2)
        
        # Create tab button
        tab_btn = tk.Button(tab_container, text=text, font=self.tab_font,
                           bg="#E9ECEF", fg="#495057", relief=tk.FLAT,
                           activebackground="#FFFFFF", activeforeground="#212529",
                           padx=20, pady=8, cursor="hand2", bd=0,
                           borderwidth=0, highlightthickness=0)
        tab_btn.pack(side=tk.LEFT)
        
        # Add close button if closeable
        close_btn = None
        if closeable:
            close_btn = tk.Button(tab_container, text="✕", font=('Segoe UI', 10),
                                 bg="#E9ECEF", fg="#6C757D", relief=tk.FLAT,
                                 activebackground="#DC3545", activeforeground="white",
                                 padx=6, pady=8, cursor="hand2", bd=0,
                                 borderwidth=0, highlightthickness=0)
            close_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # Close button command - use dynamic index lookup
            def close_tab():
                if close_callback:
                    # Find current index of this tab (in case tabs were removed)
                    for i, tab in enumerate(self.tabs):
                        if tab[3] == tab_container:  # Match by container
                            close_callback(i)
                            break
            close_btn.config(command=close_tab)
        
        # Store tab info
        tab_index = len(self.tabs)
        self.tabs.append((tab_btn, frame, text, tab_container, close_btn))
        
        # Configure tab selection - use a lambda that looks up current index
        def select_tab():
            # Find current index of this tab (in case tabs were removed)
            for i, tab in enumerate(self.tabs):
                if tab[0] == tab_btn:
                    self.select(i)
                    break
        
        tab_btn.config(command=select_tab)
        
        # Add hover effects
        def on_enter(e):
            if self.current_tab != tab_index:
                tab_btn.config(bg="#D0D0D0")
                tab_container.config(bg="#D0D0D0")
                if close_btn:
                    close_btn.config(bg="#D0D0D0")
        
        def on_leave(e):
            if self.current_tab != tab_index:
                tab_btn.config(bg="#E9ECEF")
                tab_container.config(bg="#E9ECEF")
                if close_btn:
                    close_btn.config(bg="#E9ECEF")
        
        tab_btn.bind("<Enter>", on_enter)
        tab_btn.bind("<Leave>", on_leave)
        if close_btn:
            close_btn.bind("<Enter>", on_enter)
            close_btn.bind("<Leave>", on_leave)
        
        # Place frame in content area
        frame.place(in_=self.content_area, x=0, y=0, relwidth=1.0, relheight=1.0)
        frame.lower()  # Hide initially
        
        # Select first tab automatically
        if len(self.tabs) == 1:
            self.select(0)
    
    def select(self, index):
        """Select a tab by index."""
        if index < 0 or index >= len(self.tabs):
            return
        
        # Deselect current tab
        if self.current_tab is not None:
            tab_info = self.tabs[self.current_tab]
            old_btn, old_frame = tab_info[0], tab_info[1]
            old_container = tab_info[3] if len(tab_info) > 3 else None
            old_close_btn = tab_info[4] if len(tab_info) > 4 else None
            old_btn.config(bg="#E9ECEF", fg="#495057", relief=tk.FLAT)
            if old_container:
                old_container.config(bg="#E9ECEF")
            if old_close_btn:
                old_close_btn.config(bg="#E9ECEF")
            old_frame.lower()
        
        # Select new tab
        tab_info = self.tabs[index]
        new_btn, new_frame = tab_info[0], tab_info[1]
        new_container = tab_info[3] if len(tab_info) > 3 else None
        new_close_btn = tab_info[4] if len(tab_info) > 4 else None
        
        # Update current_tab BEFORE setting colors (important for hover events)
        self.current_tab = index
        
        # Set active colors
        new_btn.config(bg="#FFFFFF", fg="#212529", relief=tk.FLAT)
        if new_container:
            new_container.config(bg="#FFFFFF")
        if new_close_btn:
            new_close_btn.config(bg="#FFFFFF")
        new_frame.lift()
        
        # Trigger event
        self.parent.event_generate("<<NotebookTabChanged>>")
    
    def index(self, what):
        """Get index of tab."""
        if what == "end":
            return len(self.tabs)
        elif what == self.current_tab or what == "current":
            return self.current_tab
        return 0
    
    def tab(self, index, option=None, **kw):
        """Get or set tab options."""
        if index < 0 or index >= len(self.tabs):
            return
        
        tab_info = self.tabs[index]
        btn, frame, text = tab_info[0], tab_info[1], tab_info[2]
        
        if option == "text":
            return text
        
        return None
    
    def forget(self, index):
        """Remove a tab."""
        if index < 0 or index >= len(self.tabs):
            return
        
        tab_info = self.tabs[index]
        btn, frame, text, container = tab_info[0], tab_info[1], tab_info[2], tab_info[3]
        
        # Destroy widgets
        container.destroy()
        frame.destroy()
        
        # Remove from list
        self.tabs.pop(index)
        
        # Adjust current_tab
        if self.current_tab == index:
            # Select previous tab or first tab
            new_index = max(0, index - 1) if len(self.tabs) > 0 else None
            self.current_tab = None
            if new_index is not None:
                self.select(new_index)
        elif self.current_tab is not None and self.current_tab > index:
            self.current_tab -= 1
    
    def pack(self, **kwargs):
        """Pack the notebook."""
        self.container.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the notebook."""
        self.container.grid(**kwargs)
