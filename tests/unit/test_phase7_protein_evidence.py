from pathlib import Path

from src.utils.compare_outputs import check_phase7_protein_evidence


def test_phase7_protein_evidence_gate_passes():
    root = Path(__file__).resolve().parents[2]
    assert check_phase7_protein_evidence(root) == []
