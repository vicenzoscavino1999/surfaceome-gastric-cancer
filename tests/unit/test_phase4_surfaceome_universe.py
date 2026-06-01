from pathlib import Path

from src.utils.compare_outputs import check_phase4_surfaceome_universe


def test_phase4_surfaceome_universe_gate_passes():
    root = Path(__file__).resolve().parents[2]
    assert check_phase4_surfaceome_universe(root) == []
