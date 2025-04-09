import sys
import os

print("Python Executable:", sys.executable)
print("Python Version:", sys.version)
print("\nPython Path:")
for path in sys.path:
    print(path)

print("\nTrying to import augmentorium:")
try:
    import augmentorium
    print("Successfully imported augmentorium")
    print("Package location:", augmentorium.__file__)
except ImportError as e:
    print("Import failed:", e)

print("\nChecking project structure:")
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print("Project Root:", project_root)
print("\nContents of project root:")
print(os.listdir(project_root))

print("\nContents of augmentorium directory:")
augmentorium_dir = os.path.join(project_root, 'augmentorium')
print(os.listdir(augmentorium_dir))