"""Compatibility namespace for pre-M2 imports.

Reusable implementation lives in :mod:`mvstudio.engines.mv`. Legacy scripts
that import ``mv_engine.*`` resolve submodules from that package first.
"""
from pathlib import Path

_SOURCE = Path(__file__).resolve().parents[2] / "src" / "mvstudio" / "engines" / "mv"
__path__ = [str(_SOURCE), str(Path(__file__).resolve().parent)]
