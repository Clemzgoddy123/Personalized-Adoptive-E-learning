import os, sys, importlib, traceback
sys.path.append(r'c:\Users\chromeworld\OneDrive\Desktop\project\\AdaptiveELearningSystem')
# set Django settings and initialize
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
try:
    m = importlib.import_module('teacher_support.views')
    print('Imported teacher_support.views OK')
except Exception:
    traceback.print_exc()
    print('Import failed')
