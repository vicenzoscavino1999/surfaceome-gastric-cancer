from pathlib import Path

from src.utils.compare_outputs import check_phase13_mvp_scoring


def test_phase13_mvp_scoring_gate_passes():
    root = Path(__file__).resolve().parents[2]
    assert check_phase13_mvp_scoring(root) == []
