"""Pytest configuration for unit tests."""

import sys
from pathlib import Path

# Add the project root to Python path so imports work correctly
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
