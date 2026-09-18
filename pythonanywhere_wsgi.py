"""WSGI entry point for PythonAnywhere.

Set the project and virtualenv paths to match the PythonAnywhere account.
"""
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

VENV_DIR = os.environ.get(
    "PYTHONANYWHERE_VENV",
    os.path.expanduser("~/.virtualenvs/aenor-venv"),
)
activate_this = os.path.join(VENV_DIR, "bin", "activate_this.py")
if os.path.isfile(activate_this):
    with open(activate_this, encoding="utf-8") as file_handle:
        exec(compile(file_handle.read(), activate_this, "exec"), {"__file__": activate_this})

from app import app as application
