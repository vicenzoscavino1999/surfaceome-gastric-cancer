from pathlib import Path

from src.utils.compare_outputs import check_bootstrap


def test_required_bootstrap_files_exist():
    root = Path(__file__).resolve().parents[2]
    assert check_bootstrap(root) == []
