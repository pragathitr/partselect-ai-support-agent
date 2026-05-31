"""Root conftest — adds project root to sys.path so 'backend' is importable without pip install."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
