from __future__ import annotations

import csv
import hashlib
import io
import math
import random
import re
import statistics
import tarfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13198309/supplementaryFiles"
OA_PACKAGE_URL = "https://ftp.ncbi.nlm.nih.gov/pub/pmc/deprecated/oa_package/7b/4d/PMC13198309.tar.gz"
WANG_WORKBOOK = "mmc8.xlsx"
WANG_SHEET = "Drug_target_classes"
WANG_WORKBOOK_PATH = ROOT / "data" / "raw" / "wang2026" / WANG_WORKBOOK
WANG_CHECKSUM = ROOT / "data" / "checksums" / "wang2026_mmc8_sha256.tsv"
EXPECTED_MMC8_MD5 = "54b786e2df75cac2d1f478ebc26f7f3a"
EXPECTED_MMC8_SHA256 = "e9988d342fd4510956d701a037dd9a20834c0cccb05a2020ce5e1b2e5999b3dc"
UNIVERSE = ROOT / "data" / "processed" / "surfaceome_universe.tsv"
TIER_ASSIGNMENTS = ROOT / "results" / "tables" / "tier_assignments.tsv"
COMPONENT_SCORES = ROOT / "results" / "tables" / "component_scores_all_candidates.tsv"
OUTPUT = ROOT / "results" / "tables" / "wang2026_overlap_enrichment.tsv"
OUTPUT_MATCHED_NULL = ROOT / "results" / "tables" / "wang2026_matched_null.tsv"
MATCHED_NULL_SEED = 20260531
MATCHED_NULL_PERMUTATIONS = 20000
MATCHED_NULL_NEAREST_POOL = 100

MAIN_BACKGROUNDS = [
    (
        "all_drug_target_table",
        "all genes in Wang 2026 mmc8 Drug_target_classes",
        lambda row: True,
    ),
    (
        "membrane_prot_flag",
        "Wang 2026 genes with membrane_prot == 1",
        lambda row: str(row.get("membrane_prot", "")).strip() in {"1", "1.0"},
    ),
    (
        "membrane_class",
        "Wang 2026 genes with Class == Membrane",
        lambda row: row.get("Class", "") == "Membrane",
    ),
    (
        "therapeutic_surface_flag",
        "Wang 2026 genes flagged as ADC, antibody, T-cell target, or membrane",
        lambda row: any(
            str(row.get(column, "")).strip() in {"1", "1.0"}
            for column in ["ADCs", "Antibody", "T_cell_target", "Membrane"]
        ),
    ),
]

MATCHING_FEATURES = (
    "Surf_relative_confidence",
    "E_rank_percentile",
    "P_rank_percentile",
    "T_rank_percentile",
    "n_available_mvp_score_components",
    "accessibility_class",
    "P_missing_indicator",
)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_checksum(path: Path, xlsx_bytes: bytes, source_label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "source": source_label,
            "filename": WANG_WORKBOOK,
            "bytes": len(xlsx_bytes),
            "md5": hashlib.md5(xlsx_bytes).hexdigest(),
            "sha256": hashlib.sha256(xlsx_bytes).hexdigest(),
        }
    ]
    write_tsv(path, rows)


def verify_wang_workbook(xlsx_bytes: bytes, source_label: str) -> None:
    observed_md5 = hashlib.md5(xlsx_bytes).hexdigest()
    observed_sha256 = hashlib.sha256(xlsx_bytes).hexdigest()
    if observed_md5 != EXPECTED_MMC8_MD5 or observed_sha256 != EXPECTED_MMC8_SHA256:
        raise ValueError(
            f"{source_label} {WANG_WORKBOOK} checksum mismatch: "
            f"md5={observed_md5}, sha256={observed_sha256}"
        )


def fetch_bytes(url: str, timeout: int = 120) -> bytes:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content


def fetch_from_europe_pmc_zip() -> bytes:
    with zipfile.ZipFile(io.BytesIO(fetch_bytes(SOURCE_URL, timeout=30))) as archive:
        return archive.read(WANG_WORKBOOK)


def fetch_from_ncbi_oa_package() -> bytes:
    with tarfile.open(fileobj=io.BytesIO(fetch_bytes(OA_PACKAGE_URL, timeout=180)), mode="r:gz") as archive:
        for member in archive.getmembers():
            if Path(member.name).name != WANG_WORKBOOK:
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                break
            return extracted.read()
    raise FileNotFoundError(f"{WANG_WORKBOOK} not found in {OA_PACKAGE_URL}")


def load_wang_workbook() -> bytes:
    if WANG_WORKBOOK_PATH.exists():
        xlsx_bytes = WANG_WORKBOOK_PATH.read_bytes()
        verify_wang_workbook(xlsx_bytes, str(WANG_WORKBOOK_PATH.relative_to(ROOT)))
        write_checksum(WANG_CHECKSUM, xlsx_bytes, f"local:{WANG_WORKBOOK_PATH.relative_to(ROOT)}")
        return xlsx_bytes

    errors: list[str] = []
    for source_label, loader in [
        (OA_PACKAGE_URL, fetch_from_ncbi_oa_package),
        (SOURCE_URL, fetch_from_europe_pmc_zip),
    ]:
        try:
            xlsx_bytes = loader()
            verify_wang_workbook(xlsx_bytes, source_label)
            WANG_WORKBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
            WANG_WORKBOOK_PATH.write_bytes(xlsx_bytes)
            write_checksum(WANG_CHECKSUM, xlsx_bytes, source_label)
            return xlsx_bytes
        except (
            requests.RequestException,
            zipfile.BadZipFile,
            KeyError,
            tarfile.TarError,
            OSError,
            ValueError,
            FileNotFoundError,
        ) as exc:
            errors.append(f"{source_label}: {type(exc).__name__}: {exc}")

    raise RuntimeError("Could not retrieve Wang 2026 mmc8.xlsx. Tried " + " | ".join(errors))


def parse_float(value: str | None, default: float = -0.2) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def parse_int(value: str | None, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except ValueError:
        return default


def quantile(values: list[int], probability: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def cell_column_index(reference: str) -> int:
    match = re.match(r"([A-Z]+)", reference)
    if match is None:
        raise ValueError(f"invalid cell reference: {reference}")
    value = 0
    for character in match.group(1):
        value = value * 26 + ord(character) - ord("A") + 1
    return value - 1


def read_shared_strings(workbook: zipfile.ZipFile) -> list[str]:
    namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.findall(f"{namespace}si"):
        values.append("".join(text.text or "" for text in item.iter(f"{namespace}t")))
    return values


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    value_node = cell.find(f"{namespace}v")
    if value_node is None:
        return ""
    value = value_node.text or ""
    if cell.attrib.get("t") == "s" and value:
        return shared_strings[int(value)]
    return value


def worksheet_path(workbook: zipfile.ZipFile, sheet_name: str) -> str:
    main_ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    relationship_ns = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    workbook_xml = ET.fromstring(workbook.read("xl/workbook.xml"))
    rels_xml = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    rel_map = {node.attrib["Id"]: node.attrib["Target"] for node in rels_xml}
    sheets = workbook_xml.find("a:sheets", main_ns)
    if sheets is None:
        raise ValueError("workbook has no sheets")
    for sheet in sheets:
        if sheet.attrib.get("name") != sheet_name:
            continue
        relationship_id = sheet.attrib[f"{relationship_ns}id"]
        target = rel_map[relationship_id]
        return f"xl/{target}" if not target.startswith("xl/") else target
    raise ValueError(f"sheet not found: {sheet_name}")


def parse_wang_rows(xlsx_bytes: bytes) -> list[dict[str, str]]:
    namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as workbook:
        shared_strings = read_shared_strings(workbook)
        sheet_xml = ET.fromstring(workbook.read(worksheet_path(workbook, WANG_SHEET)))
    headers: list[str] = []
    rows: list[dict[str, str]] = []
    for row in sheet_xml.findall(f".//{namespace}row"):
        values: dict[int, str] = {}
        for cell in row.findall(f"{namespace}c"):
            values[cell_column_index(cell.attrib["r"])] = cell_value(cell, shared_strings)
        if row.attrib.get("r") == "1":
            headers = [values.get(index, "") for index in range(max(values) + 1)]
            continue
        parsed = {headers[index]: values.get(index, "") for index in range(len(headers))}
        if parsed.get("Genes"):
            rows.append(parsed)
    return rows


def hypergeometric_upper_tail(population: int, successes: int, draws: int, observed: int) -> float:
    def log_choose(total: int, selected: int) -> float:
        if selected < 0 or selected > total:
            return float("-inf")
        return math.lgamma(total + 1) - math.lgamma(selected + 1) - math.lgamma(total - selected + 1)

    def probability(count: int) -> float:
        return math.exp(
            log_choose(successes, count)
            + log_choose(population - successes, draws - count)
            - log_choose(population, draws)
        )

    return sum(probability(count) for count in range(observed, min(draws, successes) + 1))


def accessibility_distance(left: str, right: str) -> float:
    classes = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
    if not left or not right:
        return 1.0
    return 0.0 if left == right else min(abs(classes.get(left, 9) - classes.get(right, 9)), 3) / 3


def matched_distance(left: dict[str, str], right: dict[str, str]) -> float:
    left_p_missing = 1 if not left.get("P_rank_percentile") else 0
    right_p_missing = 1 if not right.get("P_rank_percentile") else 0
    return (
        ((parse_float(left.get("Surf_relative_confidence"), 0.0) - parse_float(right.get("Surf_relative_confidence"), 0.0)) / 0.2)
        ** 2
        + ((parse_float(left.get("E_rank_percentile")) - parse_float(right.get("E_rank_percentile"))) / 0.15)
        ** 2
        + ((parse_float(left.get("P_rank_percentile")) - parse_float(right.get("P_rank_percentile"))) / 0.2)
        ** 2
        + ((parse_float(left.get("T_rank_percentile")) - parse_float(right.get("T_rank_percentile"))) / 0.2)
        ** 2
        + ((parse_int(left.get("n_available_mvp_score_components")) - parse_int(right.get("n_available_mvp_score_components"))) / 2)
        ** 2
        + (2.0 if left_p_missing != right_p_missing else 0.0)
        + accessibility_distance(left.get("accessibility_class", ""), right.get("accessibility_class", ""))
    )


def nearest_neighbor_pools(
    component_by_gene: dict[str, dict[str, str]],
    tier12: set[str],
    pool_size: int,
) -> tuple[dict[str, list[str]], set[str]]:
    candidate_controls = sorted(set(component_by_gene) - tier12)
    pools: dict[str, list[str]] = {}
    for gene in sorted(tier12):
        target = component_by_gene[gene]
        distances = [
            (matched_distance(target, component_by_gene[control]), control)
            for control in candidate_controls
        ]
        distances.sort(key=lambda item: (item[0], item[1]))
        pools[gene] = [control for _, control in distances[:pool_size]]
    return pools, set(candidate_controls)


def draw_matched_sets(pools: dict[str, list[str]]) -> list[list[str]]:
    rng = random.Random(MATCHED_NULL_SEED)
    genes = sorted(pools)
    draws: list[list[str]] = []
    for _ in range(MATCHED_NULL_PERMUTATIONS):
        selected: set[str] = set()
        sampled: list[str] = []
        for gene in genes:
            pool = pools[gene]
            available = [control for control in pool if control not in selected]
            if not available:
                available = pool
            control = rng.choice(available)
            selected.add(control)
            sampled.append(control)
        draws.append(sampled)
    return draws


def build_matched_null_rows(
    background_gene_sets: dict[str, tuple[str, set[str]]],
    universe: set[str],
    tier12: set[str],
    mmc8_sha256: str,
) -> list[dict[str, object]]:
    component_by_gene = {
        row["hgnc_symbol"]: row
        for row in read_tsv(COMPONENT_SCORES)
        if row.get("hgnc_symbol") in universe
    }
    missing_targets = sorted(tier12 - set(component_by_gene))
    if missing_targets:
        raise ValueError(f"Tier 1/2 genes missing from component scores: {missing_targets}")

    pools, control_pool = nearest_neighbor_pools(component_by_gene, tier12, MATCHED_NULL_NEAREST_POOL)
    sampled_sets = draw_matched_sets(pools)
    output_rows: list[dict[str, object]] = []
    for background_id, (description, source_genes) in background_gene_sets.items():
        observed = len(source_genes & tier12)
        counts = [len(set(sampled) & source_genes) for sampled in sampled_sets]
        p_ge = (1 + sum(1 for count in counts if count >= observed)) / (1 + len(counts))
        mean_value = statistics.fmean(counts)
        sd_value = statistics.pstdev(counts)
        output_rows.append(
            {
                "background_id": background_id,
                "background_description": description,
                "source_url": SOURCE_URL,
                "source_workbook": WANG_WORKBOOK,
                "source_sheet": WANG_SHEET,
                "mmc8_sha256": mmc8_sha256,
                "tier1_2_gene_count": len(tier12),
                "observed_tier1_2_overlap": observed,
                "matched_control_pool_size": len(control_pool),
                "nearest_pool_size_per_target": MATCHED_NULL_NEAREST_POOL,
                "n_permutations": MATCHED_NULL_PERMUTATIONS,
                "random_seed": MATCHED_NULL_SEED,
                "matching_features": ";".join(MATCHING_FEATURES),
                "matched_null_mean_overlap": f"{mean_value:.6f}",
                "matched_null_sd_overlap": f"{sd_value:.6f}",
                "matched_null_q05_overlap": f"{quantile(counts, 0.05):.6f}",
                "matched_null_median_overlap": f"{quantile(counts, 0.50):.6f}",
                "matched_null_q95_overlap": f"{quantile(counts, 0.95):.6f}",
                "matched_null_upper_tail_p": f"{p_ge:.8g}",
                "interpretation": (
                    "not_enriched_vs_matched_surfaceome_evidence_null"
                    if p_ge >= 0.05
                    else "enriched_vs_matched_surfaceome_evidence_null"
                ),
            }
        )
    return output_rows


def main() -> int:
    xlsx_bytes = load_wang_workbook()
    mmc8_sha256 = hashlib.sha256(xlsx_bytes).hexdigest()
    wang_rows = parse_wang_rows(xlsx_bytes)

    universe = {
        row["hgnc_symbol"]
        for row in read_tsv(UNIVERSE)
        if row.get("surfaceome_category") in {"core_surfaceome", "probable_surfaceome"}
    }
    tier12 = {
        row["gene"]
        for row in read_tsv(TIER_ASSIGNMENTS)
        if row.get("tier") in {"Tier 1", "Tier 2"}
    }
    population = len(universe)
    draws = len(tier12)

    output_rows: list[dict[str, object]] = []
    background_gene_sets: dict[str, tuple[str, set[str]]] = {}
    for background_id, description, selector in MAIN_BACKGROUNDS:
        source_genes = {row["Genes"].strip() for row in wang_rows if selector(row) and row.get("Genes")}
        background_gene_sets[background_id] = (description, source_genes)
        successes = len(source_genes & universe)
        observed = len(source_genes & tier12)
        expected = draws * successes / population
        p_value = hypergeometric_upper_tail(population, successes, draws, observed)
        false_positive = draws - observed
        background_non_sample_successes = successes - observed
        background_non_successes = population - successes - false_positive
        odds_ratio = (
            observed * background_non_successes / (false_positive * background_non_sample_successes)
            if false_positive * background_non_sample_successes
            else float("inf")
        )
        output_rows.append(
            {
                "background_id": background_id,
                "background_description": description,
                "source_url": SOURCE_URL,
                "source_workbook": WANG_WORKBOOK,
                "source_sheet": WANG_SHEET,
                "mmc8_sha256": mmc8_sha256,
                "source_unique_genes": len(source_genes),
                "surfaceome_universe_size": population,
                "wang_background_genes_in_surfaceome_universe": successes,
                "tier1_2_gene_count": draws,
                "observed_tier1_2_overlap": observed,
                "expected_overlap_under_random_draw": f"{expected:.6f}",
                "hypergeometric_upper_tail_p": f"{p_value:.8g}",
                "odds_ratio": f"{odds_ratio:.6f}",
                "tier1_2_absent_from_background": ";".join(sorted(tier12 - source_genes)),
                "tier1_2_present_in_background": ";".join(sorted(tier12 & source_genes)),
                "interpretation": "enriched_vs_random_draw_from_core_probable_surfaceome_universe",
            }
        )

    write_tsv(OUTPUT, output_rows)
    matched_rows = build_matched_null_rows(background_gene_sets, universe, tier12, mmc8_sha256)
    write_tsv(OUTPUT_MATCHED_NULL, matched_rows)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {OUTPUT_MATCHED_NULL.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
