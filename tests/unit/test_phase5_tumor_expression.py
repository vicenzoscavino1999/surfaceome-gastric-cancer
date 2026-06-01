from pathlib import Path

from src.utils.compare_outputs import check_phase5_tumor_expression


def test_phase5_tumor_expression_gate_passes():
    root = Path(__file__).resolve().parents[2]
    assert check_phase5_tumor_expression(root) == []
