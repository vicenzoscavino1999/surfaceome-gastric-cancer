from pathlib import Path

from src.utils.compare_outputs import check_phase1_inventory


def test_phase1_inventory_gate_passes():
    root = Path(__file__).resolve().parents[2]
    assert check_phase1_inventory(root) == []
