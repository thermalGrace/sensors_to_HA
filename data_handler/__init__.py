"""Package init ensures repository root is on sys.path for imports."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
	sys.path.append(str(ROOT))
