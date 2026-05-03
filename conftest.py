"""Shared pytest configuration: sys.path, markers, fixtures."""

import sys
from pathlib import Path

# Make src/ importable without installation
sys.path.insert(0, str(Path(__file__).parent / "src"))
