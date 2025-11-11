import re

with open('esl_ap_helper_v2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix SSH button - remove emoji and update styling
content = re.sub(
    r'self\.enable_ssh_btn = tk\.Button\(browser_group, text="[^"]*SSH",[^)]+\)',
    '''self.enable_ssh_btn = tk.Button(browser_group, text="SSH", 
                                        command=self._on_enable_ssh,
                                        font=("Segoe UI", 9),
                                        bg="#E0E0E0", fg="#333333",
                                        disabledforeground="#333333",
                                        relief="raised", bd=1,
                                        cursor="hand2",
                                        state="disabled")''',
    content,
    flags=re.DOTALL
)

# Fix Close Browser button - remove emoji and update styling
content = re.sub(
    r'self\.close_browser_btn = tk\.Button\(browser_group, text="[^"]*Close Browser",[^)]+\)',
    '''self.close_browser_btn = tk.Button(browser_group, text="Close Browser", 
                                           command=self._on_close_browser,
                                           font=("Segoe UI", 9),
                                           bg="#E0E0E0", fg="#333333",
                                           disabledforeground="#333333",
                                           relief="raised", bd=1,
                                           cursor="hand2",
                                           state="disabled")''',
    content,
    flags=re.DOTALL
)

with open('esl_ap_helper_v2.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ Fixed SSH and Close Browser buttons - removed emojis and updated styling')
