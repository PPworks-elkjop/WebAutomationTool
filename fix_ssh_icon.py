with open('esl_ap_helper_v2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the duplicate SSH text parameter
content = content.replace('text="🔒 SSH","� SSH"', 'text="🔒 SSH"')

with open('esl_ap_helper_v2.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed SSH button text!")
