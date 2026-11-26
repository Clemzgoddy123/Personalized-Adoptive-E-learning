import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
EXCLUDE_DIRS = {'venv', '__pycache__', 'migrations', '.git'}
MAX_LINE = 120

issues = []

for dirpath, dirnames, filenames in os.walk(ROOT):
    # skip excluded dirs
    parts = set(dirpath.split(os.sep))
    if parts & EXCLUDE_DIRS:
        continue
    for fname in filenames:
        if not fname.endswith('.py'):
            continue
        path = os.path.join(dirpath, fname)
        rel = os.path.relpath(path, ROOT)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            issues.append((rel, 0, 'read_error', str(e)))
            continue
        # check syntax
        try:
            src = ''.join(lines)
            compile(src, path, 'exec')
        except Exception as e:
            issues.append((rel, 0, 'syntax_error', str(e)))
            continue
        for i, line in enumerate(lines, start=1):
            if '\t' in line:
                issues.append((rel, i, 'tab_char', line.rstrip('\n')))
            if line.rstrip('\n').rstrip(' ') != line.rstrip('\n'):
                issues.append((rel, i, 'trailing_whitespace', line.rstrip('\n')))
            if len(line.rstrip('\n')) > MAX_LINE:
                issues.append((rel, i, 'long_line', f"{len(line.rstrip('\n'))} chars"))

if not issues:
    print('No issues found')
    sys.exit(0)

print(f'Found {len(issues)} issues:')
by_file = {}
for rel, ln, kind, desc in issues:
    by_file.setdefault(rel, []).append((ln, kind, desc))

for rel, items in sorted(by_file.items()):
    print('\n' + rel)
    for ln, kind, desc in items:
        print(f'  L{ln:3} {kind:<20} {desc}')

sys.exit(2)
