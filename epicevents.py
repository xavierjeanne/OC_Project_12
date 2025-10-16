"""
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cli.commands import mainnts CRM - Main Application Entry Point
Usage: python epicevents.py <command>
"""

import sys
from pathlib import Path
from cli.commands import main

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


if __name__ == "__main__":
    main()
