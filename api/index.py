import sys
import os

# Add root directory to sys.path so app.py, database.py, and ml_model.py can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel entrypoint
app.debug = False
