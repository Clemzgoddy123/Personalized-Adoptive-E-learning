import os, re
ROOT = os.path.dirname(os.path.dirname(__file__))
EXCLUDE = {'venv', '__pycache__', '.git'}
count = 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    parts = set(dirpath.split(os.sep))
    if parts & EXCLUDE:
        continue
    for fname in filenames:
        if not fname.endswith('.py'):
            continue
        path = os.path.join(dirpath, fname)
        rel = os.path.relpath(path, ROOT)
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        new_lines = []
        changed = False
        for line in lines:
            new_line = re.sub(r'^\t+', lambda m: '    ' * len(m.group(0)), line)
            if new_line != line:
                changed = True
            new_lines.append(new_line)
        if changed:
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            count += 1
            print(f'Converted tabs in {rel}')
print(f'Done. Updated {count} files.')
