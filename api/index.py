# api/index.py
import sys
from os.path import abspath, dirname

# Add the root directory to Python path
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from app import create_app

app = create_app()
