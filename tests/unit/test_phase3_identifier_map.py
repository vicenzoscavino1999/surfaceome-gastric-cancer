from pathlib import Path

from src.utils.compare_outputs import check_phase3_identifier_map


def test_phase3_identifier_map_gate_passes():
    root = Path(__file__).resolve().parents[2]
    assert check_phase3_identifier_map(root) == []
