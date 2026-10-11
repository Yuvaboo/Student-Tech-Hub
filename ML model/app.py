"""
Root Launcher for Student Project Recommender Web Application
=============================================================
Runs the Streamlit application from the root directory.
"""

import os
import sys
import subprocess

TARGET_APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_ml_from_scratch", "app.py")

if __name__ == "__main__":
    print("=" * 75)
    print("  🚀 Launching Student Project Recommender Web Application...")
    print(f"  Command: streamlit run \"{TARGET_APP}\"")
    print("=" * 75)
    cmd = [sys.executable, "-m", "streamlit", "run", TARGET_APP] + sys.argv[1:]
    subprocess.run(cmd)
