from pathlib import Path

from src.utils.compare_outputs import check_phase6_normal_selectivity


def test_phase6_normal_selectivity_gate_passes():
    root = Path(__file__).resolve().parents[2]
    assert check_phase6_normal_selectivity(root) == []
