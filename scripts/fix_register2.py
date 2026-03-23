with open('templates/gouvernance/arbitre_register.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Input fields: white background, darker border, clearer text
content = content.replace(
    'padding:0.55rem 0.75rem;border:1px solid #e2e8f0;border-radius:0.4rem;background:#f8fafc;font-size:0.875rem;font-weight:600;color:#1e293b;text-transform:uppercase;box-sizing:border-box;',
    'padding:0.55rem 0.75rem;border:1.5px solid #cbd5e1;border-radius:0.4rem;background:#fff;font-size:0.875rem;font-weight:600;color:#0f172a;text-transform:uppercase;box-sizing:border-box;'
)
# Same without text-transform (telephone, email)
content = content.replace(
    'padding:0.55rem 0.75rem;border:1px solid #e2e8f0;border-radius:0.4rem;background:#f8fafc;font-size:0.875rem;font-weight:600;color:#1e293b;box-sizing:border-box;',
    'padding:0.55rem 0.75rem;border:1.5px solid #cbd5e1;border-radius:0.4rem;background:#fff;font-size:0.875rem;font-weight:600;color:#0f172a;box-sizing:border-box;'
)
# Select fields
content = content.replace(
    'padding:0.55rem 0.75rem;border:1px solid #e2e8f0;border-radius:0.4rem;background:#f8fafc;font-size:0.875rem;font-weight:600;color:#1e293b;box-sizing:border-box;appearance:auto;',
    'padding:0.55rem 0.75rem;border:1.5px solid #cbd5e1;border-radius:0.4rem;background:#fff;font-size:0.875rem;font-weight:600;color:#0f172a;box-sizing:border-box;appearance:auto;'
)

with open('templates/gouvernance/arbitre_register.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
