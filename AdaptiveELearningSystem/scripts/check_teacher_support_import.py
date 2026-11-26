import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# put the package root (AdaptiveELearningSystem) on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(SCRIPT_DIR, '..')))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

print('SYS.PATH[0]=', sys.path[0])

try:
    import django
    django.setup()
    print('django.setup() succeeded')
except Exception as e:
    print('django.setup() failed:', repr(e))

try:
    from teacher_support import views as ts_views
    print('Imported teacher_support.views OK')
except Exception as e:
    print('Import failed:', repr(e))
    raise
