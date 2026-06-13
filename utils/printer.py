"""
Printer Utility
================
Sends a generated PDF file directly to the system's default printer
without requiring further user interaction, where supported.

Behaviour by platform:
- Windows: uses the ShellExecute "print" verb via os.startfile.
- macOS / Linux: uses the `lp` command (CUPS) if available.

If silent printing isn't possible on the current platform/environment,
the function returns False and the caller can fall back to simply
opening the file for the user to print manually.
"""

import os
import sys
import shutil
import subprocess


def print_pdf(file_path: str) -> bool:
    """
    Attempt to send `file_path` to the default printer silently.
    Returns True if a print command was successfully dispatched,
    False otherwise (caller should fall back gracefully).
    """
    if not os.path.exists(file_path):
        return False

    try:
        if sys.platform.startswith("win"):
            # Uses the registered "print" verb for the file type (Acrobat/Edge/etc.)
            os.startfile(file_path, "print")
            return True

        elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
            lp_path = shutil.which("lp")
            if lp_path:
                subprocess.run([lp_path, file_path], check=False)
                return True
            return False

    except Exception:
        return False

    return False
