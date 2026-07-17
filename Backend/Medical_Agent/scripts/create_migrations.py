import os
import subprocess
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)

subprocess.run([sys.executable, "manage.py", "makemigrations"], check=True)
subprocess.run([sys.executable, "manage.py", "migrate"], check=True)

print("Database migrations completed!")
