with open('templates/gouvernance/arbitre_register.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('font-weight:600;color:#0f172a;text-transform:uppercase;', 'font-weight:400;color:#0f172a;text-transform:uppercase;')
content = content.replace('font-weight:600;color:#0f172a;box-sizing:border-box;', 'font-weight:400;color:#0f172a;box-sizing:border-box;')
content = content.replace('font-weight:600;color:#0f172a;box-sizing:border-box;appearance:auto;', 'font-weight:400;color:#0f172a;box-sizing:border-box;appearance:auto;')

with open('templates/gouvernance/arbitre_register.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
