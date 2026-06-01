from pathlib import Path

from src.utils.compare_outputs import check_phase9_topology_isoforms


def test_phase9_topology_isoform_gate_passes():
    root = Path(__file__).resolve().parents[2]
    assert check_phase9_topology_isoforms(root) == []
