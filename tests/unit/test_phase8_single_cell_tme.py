from pathlib import Path

from src.utils.compare_outputs import check_phase8_single_cell_tme


def test_phase8_single_cell_tme_gate_passes():
    root = Path(__file__).resolve().parents[2]
    assert check_phase8_single_cell_tme(root) == []
