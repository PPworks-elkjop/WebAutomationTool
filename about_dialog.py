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
    dialog.geometry("500x600")
    dialog.resizable(False, False)
    dialog.transient(parent)
    
    # Center on parent
    dialog.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
    y = parent.winfo_y() + (parent.winfo_height() - 600) // 2
    dialog.geometry(f"500x600+{x}+{y}")
    
    # Wait for window to be ready
    dialog.update_idletasks()
    try:
        dialog.grab_set()
    except:
        pass
    
    # Header
    header = tk.Frame(dialog, bg="#0066CC", height=120)
    header.pack(fill=tk.X)
    header.pack_propagate(False)
    
    # Logo and title container
    title_container = tk.Frame(header, bg="#0066CC")
    title_container.pack(pady=(20, 5))
    
    # V logo
    logo_frame = tk.Frame(title_container, bg="white", width=50, height=50)
    logo_frame.pack(side=tk.LEFT, padx=(0, 15))
    logo_frame.pack_propagate(False)
    
    tk.Label(logo_frame, text="V", font=('Segoe UI', 28, 'bold'),
            bg="white", fg="#003D82").pack(expand=True)
    
    tk.Label(title_container, text="VERA", font=('Segoe UI', 32, 'bold'),
            bg="#0066CC", fg="white").pack(anchor="w")
    
    tk.Label(header, text="Version 3.0", font=('Segoe UI', 14),
            bg="#0066CC", fg="#E0E0E0").pack()
    
    # Content
    content = tk.Frame(dialog, bg="#FFFFFF", padx=40, pady=30)
    content.pack(fill=tk.BOTH, expand=True)
    
    # Description
    tk.Label(content, text="Vusion Expert Robot Assistant",
            font=('Segoe UI', 12, 'bold'), bg="#FFFFFF", fg="#212529").pack(pady=(0, 20))
    
    info_text = """VERA is a comprehensive management tool for Access Points and Vusion ESL systems, providing:

• Multi-tab AP support with live monitoring
• Integrated Jira ticket management
• Support notes with replies and history
• SSH and browser access integration
• Real-time ping monitoring
• Automated actions and workflows

Built for Elkjøp support teams to streamline AP and ESL troubleshooting with a human touch."""
    
    tk.Label(content, text=info_text, font=('Segoe UI', 10),
            bg="#FFFFFF", fg="#495057", justify=tk.LEFT, wraplength=420).pack(pady=(0, 30))
    
    # Divider
    tk.Frame(content, bg="#DEE2E6", height=1).pack(fill=tk.X, pady=(0, 20))
    
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
    
    dialog.focus_set()


if __name__ == '__main__':
    # Test
    root = tk.Tk()
    root.withdraw()
    show_about_dialog(root)
    root.mainloop()
