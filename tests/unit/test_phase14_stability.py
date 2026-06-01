from pathlib import Path

from src.utils.compare_outputs import check_phase14_stability


def test_phase14_stability_gate_passes():
    root = Path(__file__).resolve().parents[2]
    assert check_phase14_stability(root) == []
