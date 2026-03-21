import glob

count = 0
for path in glob.glob('templates/**/*.html', recursive=True):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    new = content
    new = new.replace('<div class="py-6">', '<div class="px-4 lg:px-8 py-6">')
    new = new.replace('<div class="py-4">', '<div class="px-4 lg:px-8 py-4">')
    if new != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new)
        count += 1
        print('Updated:', path)
print('Total:', count)
