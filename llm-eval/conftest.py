"""Make the standalone analysis scripts importable from the test suite.

The scripts in ``scripts/`` are run directly (``python scripts/x.py``), so they
import their shared module as a sibling (``from scoring import ...``). Adding
``scripts/`` to ``sys.path`` lets the tests import ``scoring`` the same way.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
