import re

with open('templates/gouvernance/arbitre_register.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove all placeholder attributes
content = re.sub(r'\s*placeholder="[^"]*"', '', content)

# Change submit button color to #2d5a8e
content = content.replace('background:#0036ca;border:none;border-radius:0.5rem;font-size:0.875rem;font-weight:700;color:#fff;cursor:pointer;', 'background:#2d5a8e;border:none;border-radius:0.5rem;font-size:0.875rem;font-weight:700;color:#fff;cursor:pointer;')
content = content.replace("onmouseover=\"this.style.background='#0029a3'\"", "onmouseover=\"this.style.background='#1e3a5f'\"")
content = content.replace("onmouseout=\"this.style.background='#0036ca'\"", "onmouseout=\"this.style.background='#2d5a8e'\"")

with open('templates/gouvernance/arbitre_register.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
