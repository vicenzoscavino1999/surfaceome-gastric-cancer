from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

DATA_DEPENDENT_TEST_FILES = {
    "test_phase4_surfaceome_universe.py",
    "test_phase5_tumor_expression.py",
    "test_phase8_single_cell_tme.py",
    "test_phase9_topology_isoforms.py",
}

MINIMUM_RELEASE_DATA_FILES = [
    "data/raw/surfaceome/tcsa_supplementary_tables_1_40.xlsx",
    "data/raw/cbioportal/stad_tcga_pan_can_atlas_2018_patient_clinical_data.json",
    "data/raw/tcga_purity/tidyestimate_1.1.1.tar.gz",
    "data/raw/uniprot/uniprot_reviewed_human_features.tsv.gz",
]


def release_data_bundle_present() -> bool:
    return all((ROOT / rel_path).exists() for rel_path in MINIMUM_RELEASE_DATA_FILES)


def pytest_collection_modifyitems(config, items):
    if release_data_bundle_present():
        return

    marker = pytest.mark.skip(
        reason="frozen release data bundle is absent; run the release-audit workflow on the full package"
    )
    for item in items:
        if Path(str(item.fspath)).name in DATA_DEPENDENT_TEST_FILES:
            item.add_marker(marker)
