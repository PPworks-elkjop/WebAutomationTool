"""
Test script to check font sizes on menus and tabs
"""
import tkinter as tk
from tkinter import ttk, font

root = tk.Tk()
root.title("Font Size Test")
root.geometry("800x600")

# Try to set menu font globally
root.option_add('*Font', ('Segoe UI', 15))
root.option_add('*Menu.font', ('Segoe UI', 15))

# Configure ttk styles
style = ttk.Style()
style.configure('TNotebook.Tab', font=('Segoe UI', 15, 'bold'), padding=[20, 14])

# Create menu
menubar = tk.Menu(root, font=('Segoe UI', 15))
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0, font=('Segoe UI', 15))
menubar.add_cascade(label="File", menu=file_menu, font=('Segoe UI', 15))
file_menu.add_command(label="Open")
file_menu.add_command(label="Exit", command=root.quit)

tools_menu = tk.Menu(menubar, tearoff=0, font=('Segoe UI', 15))
menubar.add_cascade(label="Tools", menu=tools_menu)
tools_menu.add_command(label="Option 1")
tools_menu.add_command(label="Option 2")

# Create notebook with tabs
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

tab1 = ttk.Frame(notebook)
notebook.add(tab1, text="Tab One")

tab2 = ttk.Frame(notebook)
notebook.add(tab2, text="Tab Two")

tab3 = ttk.Frame(notebook)
notebook.add(tab3, text="Tab Three")

# Add label to show what we're testing
tk.Label(root, text="Testing 15pt fonts on menu and tabs", 
         font=('Segoe UI', 12)).pack(pady=20)

root.mainloop()
