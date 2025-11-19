"""
About Dialog for AP Helper v3
Shows application information, version, and credits
"""

import tkinter as tk
from datetime import datetime


def show_about_dialog(parent):
    """Show the About dialog.
    
    Args:
        parent: Parent window
    """
    dialog = tk.Toplevel(parent)
    dialog.title("About AP Helper")
    dialog.geometry("550x650")
    dialog.resizable(False, False)
    dialog.transient(parent)
    
    # Center on parent
    dialog.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() - 550) // 2
    y = parent.winfo_y() + (parent.winfo_height() - 650) // 2
    dialog.geometry(f"550x650+{x}+{y}")
    
    # Wait for window to be ready
    dialog.update_idletasks()
    try:
        dialog.grab_set()
    except:
        pass
    
    # Header
    header = tk.Frame(dialog, bg="#3D6B9E", height=120)
    header.pack(fill=tk.X)
    header.pack_propagate(False)
    
    # Logo and title container
    title_container = tk.Frame(header, bg="#3D6B9E")
    title_container.pack(pady=(20, 5))
    
    # V logo
    logo_frame = tk.Frame(title_container, bg="white", width=50, height=50)
    logo_frame.pack(side=tk.LEFT, padx=(0, 15))
    logo_frame.pack_propagate(False)
    
    tk.Label(logo_frame, text="V", font=('Segoe UI', 28, 'bold'),
            bg="white", fg="#003D82").pack(expand=True)
    
    tk.Label(title_container, text="VERA", font=('Segoe UI', 32, 'bold'),
            bg="#3D6B9E", fg="white").pack(anchor="w")
    
    tk.Label(header, text="Version 3.0", font=('Segoe UI', 14),
            bg="#3D6B9E", fg="#E0E0E0").pack()
    
    # Scrollable content area
    content_wrapper = tk.Frame(dialog, bg="#FFFFFF")
    content_wrapper.pack(fill=tk.BOTH, expand=True)
    
    canvas = tk.Canvas(content_wrapper, bg="#FFFFFF", highlightthickness=0)
    scrollbar = tk.Scrollbar(content_wrapper, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill=tk.BOTH, expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Content inside scrollable frame
    content = tk.Frame(scrollable_frame, bg="#FFFFFF", padx=60, pady=30)
    content.pack(fill=tk.BOTH, expand=True)
    
    # Description - First paragraph with VERA expansion
    vera_text = tk.Text(content, font=('Segoe UI', 12), bg="#FFFFFF", fg="#495057",
                        wrap=tk.WORD, height=4, relief=tk.FLAT, borderwidth=0, width=45)
    vera_text.pack(pady=(0, 15))
    
    vera_text.insert("1.0", "VERA (")
    vera_text.insert(tk.END, "V", ("bold",))
    vera_text.insert(tk.END, "usion ")
    vera_text.insert(tk.END, "E", ("bold",))
    vera_text.insert(tk.END, "xpert ")
    vera_text.insert(tk.END, "R", ("bold",))
    vera_text.insert(tk.END, "obot ")
    vera_text.insert(tk.END, "A", ("bold",))
    vera_text.insert(tk.END, "ssistant) is a comprehensive management tool for Vusion ESL Access Points. What started as a simple credential manager quickly evolved into something entirely different.")
    
    vera_text.tag_configure("bold", font=('Segoe UI', 12, 'bold'))
    vera_text.config(state=tk.DISABLED)
    
    # Main description
    info_text = """Now the focus is on troubleshooting and fixing issues on the APs with features like:

• Multi-tab AP support with live monitoring
• Integrated Jira ticket management
• Support notes with replies and history
• SSH and browser access integration
• Real-time ping monitoring
• Batch operations for repetitive tasks

The true power lies in automation - when facing large-scale tasks like the summer 2025 SSH enablement across hundreds of APs, VERA can handle it in one big batch, saving countless hours of manual work."""
    
    tk.Label(content, text=info_text, font=('Segoe UI', 10),
            bg="#FFFFFF", fg="#495057", justify=tk.LEFT, wraplength=430).pack(pady=(0, 20))
    
    # Support info with clickable link
    support_frame = tk.Frame(content, bg="#F8F9FA", relief=tk.SOLID, borderwidth=1, padx=15, pady=12)
    support_frame.pack(fill=tk.X, pady=(0, 20))
    
    tk.Label(support_frame, text="Need help or found an issue?",
            font=('Segoe UI', 9, 'bold'), bg="#F8F9FA", fg="#495057").pack()
    tk.Label(support_frame, text="Please create a Jira ticket at:",
            font=('Segoe UI', 9), bg="#F8F9FA", fg="#6C757D").pack(pady=(2, 2))
    
    link_label = tk.Label(support_frame, text="https://fixit.elkjop.com",
                         font=('Segoe UI', 9, 'underline'), bg="#F8F9FA", fg="#0066CC",
                         cursor="hand2")
    link_label.pack()
    link_label.bind("<Button-1>", lambda e: __import__('webbrowser').get('windows-default').open("https://fixit.elkjop.com"))
    
    # Divider
    tk.Frame(content, bg="#DEE2E6", height=1).pack(fill=tk.X, pady=(0, 15))
    
    # Credits
    tk.Label(content, text="Original Idea & Development",
            font=('Segoe UI', 10, 'bold'), bg="#FFFFFF", fg="#3D6B9E").pack()
    tk.Label(content, text="Peter Andersson",
            font=('Segoe UI', 9, 'bold'), bg="#FFFFFF", fg="#495057").pack(pady=(5, 2))
    tk.Label(content, text="with friendly support by GitHub Copilot",
            font=('Segoe UI', 9), bg="#FFFFFF", fg="#6C757D").pack(pady=(0, 20))
    
    # Divider
    tk.Frame(content, bg="#DEE2E6", height=1).pack(fill=tk.X, pady=(0, 15))
    
    # Technical info
    tech_frame = tk.Frame(content, bg="#F8F9FA", relief=tk.SOLID, borderwidth=1)
    tech_frame.pack(fill=tk.X, pady=(0, 20))
    
    tech_info = tk.Frame(tech_frame, bg="#F8F9FA", padx=15, pady=15)
    tech_info.pack(fill=tk.BOTH)
    
    info_items = [
        ("Version:", "3.0"),
        ("Release Date:", "November 2025"),
        ("Framework:", "Python 3.13 + Tkinter"),
        ("Database:", "SQLite"),
        ("Developer:", "Elkjøp IT Team")
    ]
    
    for label, value in info_items:
        row = tk.Frame(tech_info, bg="#F8F9FA")
        row.pack(fill=tk.X, pady=3)
        
        tk.Label(row, text=label, font=('Segoe UI', 9, 'bold'),
                bg="#F8F9FA", fg="#495057", width=15, anchor="w").pack(side=tk.LEFT)
        tk.Label(row, text=value, font=('Segoe UI', 9),
                bg="#F8F9FA", fg="#212529", anchor="w").pack(side=tk.LEFT)
    
    # Footer
    footer_frame = tk.Frame(content, bg="#FFFFFF")
    footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
    
    tk.Label(footer_frame, text=f"© {datetime.now().year} Elkjøp Nordic AS",
            font=('Segoe UI', 9), bg="#FFFFFF", fg="#6C757D").pack()
    
    # Close button
    tk.Button(footer_frame, text="Close", command=dialog.destroy,
             bg="#3D6B9E", fg="white", font=('Segoe UI', 10, 'bold'),
             padx=30, pady=8, relief=tk.FLAT, cursor="hand2",
             borderwidth=0).pack(pady=(15, 0))
    
    # Enable mouse wheel scrolling
    def on_mousewheel(event):
        try:
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except tk.TclError:
            # Canvas has been destroyed, unbind the event
            try:
                canvas.unbind_all("<MouseWheel>")
            except:
                pass
    
    canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    def on_close():
        try:
            canvas.unbind_all("<MouseWheel>")
        except:
            pass
        dialog.destroy()
    
    dialog.protocol("WM_DELETE_WINDOW", on_close)
    
    dialog.focus_set()


if __name__ == '__main__':
    # Test
    root = tk.Tk()
    root.withdraw()
    show_about_dialog(root)
    root.mainloop()
