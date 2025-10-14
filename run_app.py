"""
PyInstaller entry point wrapper for CIB Mango Tree CLI.

This wrapper uses absolute imports to avoid the "attempted relative import
with no known parent package" error that occurs when PyInstaller runs
__main__.py directly.
"""

from cibmangotree.__main__ import main

if __name__ == "__main__":
    main()
