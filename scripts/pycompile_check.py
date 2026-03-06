import py_compile
import glob
import sys

files = glob.glob('**/*.py', recursive=True)
errs = 0
for f in files:
    if f.endswith('.py'):
        try:
            py_compile.compile(f, doraise=True)
        except Exception as e:
            print('COMPILE_ERROR:', f, e)
            errs += 1

if errs:
    print('PYCOMPILE_ERRORS:', errs)
    sys.exit(2)

print('PYCOMPILE_OK')
