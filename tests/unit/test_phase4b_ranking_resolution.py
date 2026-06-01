from pathlib import Path

from src.utils.compare_outputs import check_phase4b_ranking_resolution


def test_phase4b_ranking_resolution_gate_passes():
    root = Path(__file__).resolve().parents[2]
    assert check_phase4b_ranking_resolution(root) == []
