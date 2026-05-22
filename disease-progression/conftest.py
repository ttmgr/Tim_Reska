"""Put the ``src/`` layout on ``sys.path`` so tests can import the package.

The existing tests validate inline reference data and logic but never import
``disease_progression`` itself, so its feature extractors, models, and ETL had
no test reachability at all. This conftest makes the real package importable,
which is what lets the feature-leakage tests exercise the actual extractor.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
