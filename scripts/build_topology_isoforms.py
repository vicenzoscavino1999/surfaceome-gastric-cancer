"""Build Fase 9 topology, isoform, and extracellular accessibility outputs."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import math
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"
CHECKSUM_DIR = REPO_ROOT / "data" / "checksums"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
TABLES_DIR = REPO_ROOT / "results" / "tables"
FIGURES_DIR = REPO_ROOT / "results" / "figures"
DOCS_DIR = REPO_ROOT / "docs"

UNIPROT_FEATURES = RAW_DIR / "uniprot" / "uniprot_reviewed_human_features.tsv.gz"
SURFACEOME_UNIVERSE = PROCESSED_DIR / "surfaceome_universe.tsv"
ID_MAP = PROCESSED_DIR / "id_map_master.tsv"
PROTEIN_EVIDENCE = PROCESSED_DIR / "protein_evidence.tsv"
TOPOLOGY_CONFIG = REPO_ROOT / "config" / "topology_isoforms.yaml"

CORE_SURFACEOME_CATEGORIES = {"core_surfaceome", "probable_surfaceome"}
MANDATORY_ISOFORM_TARGETS = {
    "CLDN18": {
        "issue": "CLDN18.2_isoform_unresolved_gene_level_only",
        "context": "CLDN18.2 clinical benchmark requires transcript/isoform evidence.",
        "followup": "Resolve CLDN18.1 versus CLDN18.2 by transcript/exon-level data or manual literature/candidate-card curation.",
    },
    "FGFR2": {
        "issue": "FGFR2b_isoform_unresolved_gene_level_only",
        "context": "FGFR2b/IIIb clinical context cannot be inferred from total FGFR2 gene-level RNA.",
        "followup": "Resolve FGFR2 IIIb versus IIIc by transcript/exon-level data or manual literature/candidate-card curation.",
    },
}

UNIPROT_FEATURE_FIELDS = [
    "accession",
    "id",
    "gene_names",
    "protein_name",
    "length",
    "ft_topo_dom",
    "ft_transmem",
    "ft_intramem",
    "ft_signal",
    "ft_lipid",
    "ft_carbohyd",
    "ft_disulfid",
    "ft_chain",
    "ft_domain",
    "cc_subcellular_location",
    "cc_ptm",
    "xref_ensembl",
]
UNIPROT_FEATURE_URL = "https://rest.uniprot.org/uniprotkb/stream?" + urllib.parse.urlencode(
    {
        "compressed": "true",
        "format": "tsv",
        "fields": ",".join(UNIPROT_FEATURE_FIELDS),
        "query": "(reviewed:true) AND (organism_id:9606)",
    }
)

FEATURE_START_RE = re.compile(r"\b([A-Z_]+)\s+(<?\d+(?:\.\.>?\d+)?);")
NOTE_RE = re.compile(r'/note="([^"]+)"')
ISOFORM_RE = re.compile(r"\[([A-Z0-9]+-\d+)\]")


@dataclass(frozen=True)
class Feature:
    kind: str
    start: int
    end: int
    note: str
    text: str

    @property
    def length(self) -> int:
        return max(0, self.end - self.start + 1)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_tsv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024 * 8), b""):
            digest.update(chunk)
    return digest.hexdigest()


def update_global_sha256sums(entries: dict[str, str]) -> None:
    path = CHECKSUM_DIR / "sha256sums.txt"
    current: dict[str, str] = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                checksum, rel_path = stripped.split(maxsplit=1)
                current[rel_path.strip()] = checksum
    current.update(entries)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for rel_path in sorted(current):
            handle.write(f"{current[rel_path]}  {rel_path}\n")


def ensure_uniprot_features() -> None:
    UNIPROT_FEATURES.parent.mkdir(parents=True, exist_ok=True)
    release = "UniProt release reported by API at retrieval"
    status = "reused_existing_raw"
    if not UNIPROT_FEATURES.exists():
        request = urllib.request.Request(
            UNIPROT_FEATURE_URL,
            headers={"User-Agent": "surfaceome-gastric-cancer-fase9/0.1"},
        )
        with urllib.request.urlopen(request, timeout=240) as response:
            release = response.headers.get("x-uniprot-release", release)
            UNIPROT_FEATURES.write_bytes(response.read())
        status = "downloaded_raw"

    checksum = sha256_file(UNIPROT_FEATURES)
    rel_path = UNIPROT_FEATURES.relative_to(REPO_ROOT).as_posix()
    write_tsv(
        CHECKSUM_DIR / "uniprot_phase9_features_sha256.tsv",
        [
            {
                "source_id": "uniprot_reviewed_human_features_phase9",
                "action": status,
                "local_path": rel_path,
                "filename": UNIPROT_FEATURES.name,
                "url_or_endpoint": UNIPROT_FEATURE_URL,
                "retrieval_date": dt.date.today().isoformat(),
                "version_or_release": release,
                "bytes": UNIPROT_FEATURES.stat().st_size,
                "sha256": checksum,
                "status": "ok",
                "license_or_terms": "UniProt terms; reviewed human bulk feature fields",
                "notes": "Fase 9 reviewed human UniProt features: length, topology, TM, signal, lipid/GPI, glycosylation, disulfide, chains, domains, subcellular location, PTM, Ensembl isoform mappings.",
            }
        ],
        [
            "source_id",
            "action",
            "local_path",
            "filename",
            "url_or_endpoint",
            "retrieval_date",
            "version_or_release",
            "bytes",
            "sha256",
            "status",
            "license_or_terms",
            "notes",
        ],
    )
    update_global_sha256sums({rel_path: checksum})


def fmt(value: float | int | str, digits: int = 6) -> str:
    if isinstance(value, str):
        return value
    numeric = float(value)
    if not math.isfinite(numeric):
        return ""
    if abs(numeric) >= 1000:
        return f"{numeric:.3f}"
    return f"{numeric:.{digits}f}"


def bool_text(value: bool) -> str:
    return str(value).lower()


def split_gene_names(value: str) -> list[str]:
    return [part for part in str(value or "").split() if part and "/" not in part]


def parse_position(position: str) -> tuple[int, int]:
    clean = position.replace("<", "").replace(">", "")
    if ".." in clean:
        start_text, end_text = clean.split("..", 1)
    else:
        start_text = end_text = clean
    return int(start_text), int(end_text)


def parse_features(text: str) -> list[Feature]:
    if not text:
        return []
    matches = list(FEATURE_START_RE.finditer(text))
    features: list[Feature] = []
    for idx, match in enumerate(matches):
        start_idx = match.start()
        end_idx = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        chunk = text[start_idx:end_idx].strip().strip(";")
        kind = match.group(1)
        start, end = parse_position(match.group(2))
        note_match = NOTE_RE.search(chunk)
        note = note_match.group(1) if note_match else ""
        features.append(Feature(kind=kind, start=start, end=end, note=note, text=chunk))
    return features


def load_uniprot_features() -> dict[str, dict[str, object]]:
    ensure_uniprot_features()
    records: dict[str, dict[str, object]] = {}
    with gzip.open(UNIPROT_FEATURES, "rt", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            accession = row.get("Entry", "")
            if not accession:
                continue
            row["_gene_names_list"] = split_gene_names(row.get("Gene Names", ""))
            row["_topology_features"] = parse_features(row.get("Topological domain", ""))
            row["_tm_features"] = parse_features(row.get("Transmembrane", ""))
            row["_intramem_features"] = parse_features(row.get("Intramembrane", ""))
            row["_signal_features"] = parse_features(row.get("Signal peptide", ""))
            row["_lipid_features"] = parse_features(row.get("Lipidation", ""))
            row["_glyco_features"] = parse_features(row.get("Glycosylation", ""))
            row["_disulfide_features"] = parse_features(row.get("Disulfide bond", ""))
            row["_chain_features"] = parse_features(row.get("Chain", ""))
            row["_domain_features"] = parse_features(row.get("Domain [FT]", ""))
            row["_isoforms"] = sorted(set(ISOFORM_RE.findall(row.get("Ensembl", ""))))
            records[accession] = row
    return records


def candidate_rows() -> list[dict[str, str]]:
    rows = [
        row
        for row in read_tsv(SURFACEOME_UNIVERSE)
        if row.get("surfaceome_category") in CORE_SURFACEOME_CATEGORIES
    ]
    rows.sort(key=lambda row: row["hgnc_symbol"])
    return rows


def id_map_by_symbol() -> dict[str, dict[str, str]]:
    return {row["hgnc_symbol"]: row for row in read_tsv(ID_MAP)}


def protein_rows_by_symbol() -> dict[str, dict[str, str]]:
    if not PROTEIN_EVIDENCE.exists():
        return {}
    return {row["hgnc_symbol"]: row for row in read_tsv(PROTEIN_EVIDENCE)}


def rank_percentiles(values_by_symbol: dict[str, float]) -> dict[str, float]:
    symbols = sorted(values_by_symbol)
    values = np.array([values_by_symbol[symbol] for symbol in symbols], dtype=float)
    finite_mask = np.isfinite(values)
    finite_symbols = [symbol for symbol, ok in zip(symbols, finite_mask) if ok]
    finite_values = values[finite_mask]
    if finite_values.size == 0:
        return {}
    order = np.argsort(finite_values, kind="mergesort")
    ranks = np.zeros(finite_values.size, dtype=float)
    start = 0
    while start < finite_values.size:
        end = start + 1
        while end < finite_values.size and finite_values[order[end]] == finite_values[order[start]]:
            end += 1
        ranks[order[start:end]] = (start + 1 + end) / 2.0
        start = end
    if finite_values.size == 1:
        percentiles = np.ones(1, dtype=float)
    else:
        percentiles = (ranks - 1.0) / (finite_values.size - 1.0)
    return {symbol: float(value) for symbol, value in zip(finite_symbols, percentiles)}


def total_length(segments: list[Feature]) -> int:
    return sum(feature.length for feature in segments)


def longest_length(segments: list[Feature]) -> int:
    return max((feature.length for feature in segments), default=0)


def segment_text(segments: list[Feature]) -> str:
    return ";".join(f"{feature.start}-{feature.end}:{feature.note or feature.kind}" for feature in segments)


def terminal_orientation(topology: list[Feature], protein_length: int, terminal: str) -> str:
    if not topology:
        return "unknown"
    if terminal == "N":
        matching = [feature for feature in topology if feature.start <= 2]
    else:
        matching = [feature for feature in topology if protein_length and feature.end >= protein_length - 1]
        if not matching:
            max_end = max(feature.end for feature in topology)
            matching = [feature for feature in topology if feature.end == max_end]
    if not matching:
        return "unknown"
    note = matching[0].note.lower()
    if "extracellular" in note:
        return "extracellular"
    if "cytoplasmic" in note:
        return "cytoplasmic"
    if note:
        return matching[0].note
    return "unknown"


def infer_gpi_extracellular(record: dict[str, object], protein_length: int) -> list[Feature]:
    lipid_features: list[Feature] = record["_lipid_features"]  # type: ignore[assignment]
    signal_features: list[Feature] = record["_signal_features"]  # type: ignore[assignment]
    subcellular = str(record.get("Subcellular location [CC]", ""))
    if "gpi-anchor" not in (str(record.get("Lipidation", "")) + " " + subcellular).lower():
        return []
    gpi_positions = [feature.start for feature in lipid_features if "gpi" in feature.text.lower()]
    if not gpi_positions:
        return []
    start = max((feature.end for feature in signal_features), default=0) + 1
    end = min(gpi_positions) - 1
    if start <= end and protein_length and end <= protein_length:
        return [Feature("INFERRED_GPI_ECD", start, end, "Extracellular inferred from GPI-anchor and signal peptide", "")]
    return []


def extracellular_segments(record: dict[str, object], protein_length: int) -> tuple[list[Feature], str]:
    topology: list[Feature] = record["_topology_features"]  # type: ignore[assignment]
    extracellular = [feature for feature in topology if "extracellular" in feature.note.lower()]
    if extracellular:
        return extracellular, "uniprot_topological_domain"
    gpi = infer_gpi_extracellular(record, protein_length)
    if gpi:
        return gpi, "inferred_from_uniprot_gpi_anchor"
    return [], "not_resolved_from_current_features"


def domain_flags(record: dict[str, object]) -> list[str]:
    domain_text = " ".join(
        [
            str(record.get("Protein names", "")),
            str(record.get("Domain [FT]", "")),
            str(record.get("Subcellular location [CC]", "")),
        ]
    ).lower()
    checks = [
        ("ig_like", ["ig-like", "immunoglobulin"]),
        ("cadherin", ["cadherin"]),
        ("egf_like", ["egf-like", "egf "]),
        ("mucin_like", ["mucin"]),
        ("receptor", ["receptor"]),
        ("transporter", ["transporter", "transport"]),
        ("gpcr", ["g-protein coupled receptor", "gpcr"]),
        ("tetraspanin", ["tetraspanin"]),
        ("claudin", ["claudin"]),
    ]
    flags = [label for label, terms in checks if any(term in domain_text for term in terms)]
    return flags


def accessibility_class(
    ecd_total: int,
    largest_loop: int,
    tm_count: int,
    gpi_anchor: bool,
    source: str,
) -> tuple[str, str, float]:
    if ecd_total <= 0:
        return "E", "No extracellular domain resolved from current UniProt features.", 0.0
    if source == "not_resolved_from_current_features":
        return "D", "Topology is uncertain; extracellular accessibility requires manual review.", 0.25
    if tm_count > 1 and not gpi_anchor:
        if largest_loop >= 100:
            return "B", "Multipass protein with a large extracellular region; feasible but conformation-sensitive.", 0.80
        if largest_loop >= 20:
            return "C", "Multipass protein with extracellular loops; possible but difficult for antibody targeting.", 0.55
        return "D", "Multipass protein with short extracellular loops.", 0.25
    if largest_loop > 100:
        return "A", "Large extracellular region with clear membrane anchoring.", 1.0
    if 50 <= largest_loop <= 100:
        return "B", "Moderate extracellular region with clear orientation.", 0.80
    if 20 <= largest_loop < 50:
        return "C", "Short extracellular region or loop.", 0.55
    return "D", "Very short extracellular region.", 0.25


def topology_confidence(record: dict[str, object], source: str) -> tuple[float, str]:
    topology_text = str(record.get("Topological domain", ""))
    tm_text = str(record.get("Transmembrane", ""))
    lipid_text = str(record.get("Lipidation", ""))
    if "ECO:0000269" in topology_text or "PubMed" in topology_text:
        return 1.0, "experimental_topology_evidence"
    if source == "uniprot_topological_domain":
        return 0.85, "curated_or_predicted_uniprot_topology"
    if "GPI-anchor" in lipid_text or source == "inferred_from_uniprot_gpi_anchor":
        return 0.80, "curated_gpi_anchor_inference"
    if tm_text:
        return 0.60, "transmembrane_without_extracellular_topology"
    return 0.20, "missing_or_unresolved_topology"


def isoform_confidence(symbol: str, isoforms: list[str], config: dict[str, object]) -> tuple[float, str, str]:
    isoform_config = config["isoform_confidence"]  # type: ignore[index]
    if symbol in MANDATORY_ISOFORM_TARGETS:
        issue = MANDATORY_ISOFORM_TARGETS[symbol]["issue"]
        return float(isoform_config["mandatory_isoform_target_gene_level_unresolved"]), issue, "isoform_specific_claim_blocked"  # type: ignore[index]
    if len(isoforms) > 1:
        return float(isoform_config["multiple_uniprot_isoforms_not_resolved"]), "multiple_uniprot_isoforms_mapped_not_resolved", "gene_level_ok_with_isoform_note"  # type: ignore[index]
    return float(isoform_config["default_or_single_canonical"]), "not_isoform_critical_or_single_canonical_mapping", "gene_level_topology_acceptable"  # type: ignore[index]


def penalty_flags(record: dict[str, object]) -> tuple[float, float, str, str, str]:
    text = " ".join(
        [
            str(record.get("Protein names", "")),
            str(record.get("Chain", "")),
            str(record.get("Subcellular location [CC]", "")),
            str(record.get("Post-translational modification", "")),
        ]
    ).lower()
    cleavage = any(term in text for term in ["cleaved into", "shed", "shedding", "cleavage", "soluble"])
    secreted_isoform = "secreted" in text and ("isoform" in text or "cleaved" in text or "soluble" in text)
    shedding_penalty = 0.15 if cleavage else 0.0
    soluble_penalty = 0.10 if secreted_isoform else 0.0
    cleavage_flag = "cleavage_or_shedding_possible" if cleavage else "no_cleavage_shedding_annotation_in_current_fields"
    soluble_flag = "soluble_or_secreted_isoform_annotation" if secreted_isoform else "no_soluble_decoy_annotation_in_current_fields"
    internalization = "not_assessed_in_fase9_uniprot_bulk_fields"
    return shedding_penalty, soluble_penalty, cleavage_flag, soluble_flag, internalization


def build_rows() -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    config = load_yaml(TOPOLOGY_CONFIG)
    uniprot = load_uniprot_features()
    candidates = candidate_rows()
    ids = id_map_by_symbol()
    protein_by_symbol = protein_rows_by_symbol()

    topology_rows: list[dict[str, object]] = []
    flag_rows: list[dict[str, object]] = []
    t_scores: dict[str, float] = {}

    for candidate in candidates:
        symbol = candidate["hgnc_symbol"]
        accession = candidate.get("uniprot_accession", "")
        record = uniprot.get(accession, {})
        id_row = ids.get(symbol, {})
        protein_row = protein_by_symbol.get(symbol, {})
        protein_length = int(record.get("Length", "0") or 0) if record else 0
        tm_features: list[Feature] = record.get("_tm_features", []) if record else []  # type: ignore[assignment]
        signal_features: list[Feature] = record.get("_signal_features", []) if record else []  # type: ignore[assignment]
        lipid_features: list[Feature] = record.get("_lipid_features", []) if record else []  # type: ignore[assignment]
        glyco_features: list[Feature] = record.get("_glyco_features", []) if record else []  # type: ignore[assignment]
        disulfide_features: list[Feature] = record.get("_disulfide_features", []) if record else []  # type: ignore[assignment]
        topology_features: list[Feature] = record.get("_topology_features", []) if record else []  # type: ignore[assignment]
        isoforms: list[str] = record.get("_isoforms", []) if record else []  # type: ignore[assignment]
        if not isoforms and id_row.get("uniprot_isoform_id"):
            isoforms = [id_row["uniprot_isoform_id"]]
        extracellular, ecd_source = extracellular_segments(record, protein_length) if record else ([], "missing_uniprot_record")
        ecd_total = total_length(extracellular)
        largest_loop = longest_length(extracellular)
        gpi_anchor = any("gpi" in feature.text.lower() for feature in lipid_features) or "gpi-anchor" in str(record.get("Subcellular location [CC]", "")).lower()
        domain_architecture = domain_flags(record) if record else []
        access_class, access_text, access_score = accessibility_class(
            ecd_total=ecd_total,
            largest_loop=largest_loop,
            tm_count=len(tm_features),
            gpi_anchor=gpi_anchor,
            source=ecd_source,
        )
        access_score = float(config["accessibility_class_scores"][access_class])  # type: ignore[index]
        topo_conf, topo_evidence = topology_confidence(record, ecd_source) if record else (0.0, "missing_uniprot_record")
        iso_conf, iso_status, iso_implication = isoform_confidence(symbol, isoforms, config)
        raw_shedding_penalty, raw_soluble_penalty, cleavage_flag, soluble_flag, internalization = penalty_flags(record) if record else (0.0, 0.0, "missing_uniprot_record", "missing_uniprot_record", "not_assessed")
        penalty_config = config["penalties"]  # type: ignore[index]
        shedding_penalty = float(penalty_config["cleavage_or_shedding"]) if raw_shedding_penalty > 0 else 0.0  # type: ignore[index]
        soluble_penalty = float(penalty_config["soluble_decoy_or_secreted_isoform"]) if raw_soluble_penalty > 0 else 0.0  # type: ignore[index]
        length_score = min(1.0, math.log1p(max(0, largest_loop)) / math.log1p(150)) if largest_loop > 0 else 0.0
        weights = config["t_score_weights"]  # type: ignore[index]
        t_score = max(
            0.0,
            min(
                1.0,
                float(weights["accessibility_class_score"]) * access_score  # type: ignore[index]
                + float(weights["extracellular_length_score"]) * length_score  # type: ignore[index]
                + float(weights["topology_confidence"]) * topo_conf  # type: ignore[index]
                + float(weights["isoform_confidence"]) * iso_conf  # type: ignore[index]
                - shedding_penalty
                - soluble_penalty,
            ),
        )
        t_scores[symbol] = t_score

        topology_note_parts = []
        if ecd_source.startswith("inferred"):
            topology_note_parts.append("ECD inferred from GPI anchor because explicit UniProt TOPO_DOM was absent")
        if symbol in MANDATORY_ISOFORM_TARGETS:
            topology_note_parts.append(MANDATORY_ISOFORM_TARGETS[symbol]["context"])
        if protein_row.get("membrane_support_class"):
            topology_note_parts.append(f"Fase7 membrane support={protein_row.get('membrane_support_class')}")

        topology_rows.append(
            {
                "hgnc_symbol": symbol,
                "ensembl_gene_id": candidate.get("ensembl_gene_id", ""),
                "uniprot_accession": accession,
                "protein_name": record.get("Protein names", candidate.get("protein_name", "")) if record else candidate.get("protein_name", ""),
                "surfaceome_category": candidate.get("surfaceome_category", ""),
                "uniprot_feature_status": "reviewed_human_features_found" if record else "missing_uniprot_feature_record",
                "protein_length_aa": protein_length or "",
                "tm_helix_count": len(tm_features),
                "signal_peptide_present": bool_text(bool(signal_features)),
                "gpi_anchor_present": bool_text(gpi_anchor),
                "n_terminal_orientation": terminal_orientation(topology_features, protein_length, "N"),
                "c_terminal_orientation": terminal_orientation(topology_features, protein_length, "C"),
                "extracellular_segment_count": len(extracellular),
                "extracellular_segments": segment_text(extracellular),
                "total_extracellular_aa": ecd_total,
                "largest_extracellular_loop_aa": largest_loop,
                "topology_confidence": fmt(topo_conf),
                "topology_evidence_class": topo_evidence,
                "accessibility_class": access_class,
                "accessibility_interpretation": access_text,
                "domain_architecture_flags": ";".join(domain_architecture),
                "glycosylation_site_count": len(glyco_features),
                "disulfide_bond_count": len(disulfide_features),
                "cleavage_or_shedding_flag": cleavage_flag,
                "soluble_isoform_or_secreted_flag": soluble_flag,
                "internalization_status": internalization,
                "isoform_count": len(isoforms),
                "mapped_uniprot_isoforms": ";".join(isoforms),
                "isoform_confidence": fmt(iso_conf),
                "isoform_resolution_status": iso_status,
                "accessibility_class_score": fmt(access_score),
                "extracellular_length_score": fmt(length_score),
                "shedding_penalty": fmt(shedding_penalty),
                "soluble_decoy_penalty": fmt(soluble_penalty),
                "T_score": fmt(t_score),
                "T_rank_percentile": "",
                "topology_notes": "; ".join(topology_note_parts),
            }
        )

        issue_rows: list[tuple[str, str, str, str]] = []
        if symbol in MANDATORY_ISOFORM_TARGETS:
            issue_rows.append(
                (
                    MANDATORY_ISOFORM_TARGETS[symbol]["issue"],
                    MANDATORY_ISOFORM_TARGETS[symbol]["context"],
                    "not_eligible_for_isoform_specific_claim_from_gene_level_data",
                    MANDATORY_ISOFORM_TARGETS[symbol]["followup"],
                )
            )
        elif len(isoforms) > 1:
            issue_rows.append(
                (
                    "multiple_uniprot_isoforms_mapped",
                    "Multiple UniProt isoform mappings are present; current scoring uses canonical gene-level topology.",
                    "allowed_with_isoform_note_if_prioritized",
                    "Manual candidate-card review should verify whether the prioritized antigenic region is isoform-stable.",
                )
            )
        if access_class in {"D", "E"}:
            issue_rows.append(
                (
                    f"accessibility_class_{access_class}",
                    access_text,
                    "not_eligible_for_tier1_antibody_targeting_without_counterevidence",
                    "Manual review or structure/literature evidence required before antibody-accessibility claims.",
                )
            )
        if cleavage_flag == "cleavage_or_shedding_possible" or soluble_flag == "soluble_or_secreted_isoform_annotation":
            issue_rows.append(
                (
                    "shedding_or_soluble_isoform_annotation",
                    "UniProt names/chains/subcellular/PTM annotations suggest cleavage, shedding, or secreted isoform context.",
                    "candidate_card_must_discuss_antigen_density_and_soluble_decoy_risk",
                    "Review UniProt entry, HPA protein evidence, and modality-specific literature.",
                )
            )
        for issue, context, implication, followup in issue_rows:
            flag_rows.append(
                {
                    "hgnc_symbol": symbol,
                    "ensembl_gene_id": candidate.get("ensembl_gene_id", ""),
                    "uniprot_accession": accession,
                    "isoform_or_topology_issue": issue,
                    "isoform_resolution_status": iso_status,
                    "mapped_transcripts_or_isoforms": ";".join(isoforms),
                    "clinical_target_context": context,
                    "tiering_implication": implication,
                    "evidence_basis": "UniProt reviewed human feature bulk file plus Fase 3 gene-level ID mapping",
                    "required_followup": followup,
                }
            )

    ranks = rank_percentiles(t_scores)
    for row in topology_rows:
        row["T_rank_percentile"] = fmt(ranks.get(str(row["hgnc_symbol"]), float("nan")))

    metadata = {
        "candidate_n": len(topology_rows),
        "uniprot_feature_coverage": sum(row["uniprot_feature_status"] == "reviewed_human_features_found" for row in topology_rows),
        "class_counts": {
            label: sum(row["accessibility_class"] == label for row in topology_rows)
            for label in ["A", "B", "C", "D", "E"]
        },
        "gpi_anchor_n": sum(row["gpi_anchor_present"] == "true" for row in topology_rows),
        "mandatory_isoform_unresolved_n": sum(
            row["hgnc_symbol"] in MANDATORY_ISOFORM_TARGETS for row in topology_rows
        ),
        "low_accessibility_n": sum(row["accessibility_class"] in {"D", "E"} for row in topology_rows),
        "shedding_or_soluble_n": sum(
            row["cleavage_or_shedding_flag"] == "cleavage_or_shedding_possible"
            or row["soluble_isoform_or_secreted_flag"] == "soluble_or_secreted_isoform_annotation"
            for row in topology_rows
        ),
    }
    return topology_rows, flag_rows, metadata


def plot_ecd_distribution(rows: list[dict[str, object]]) -> None:
    classes = ["A", "B", "C", "D", "E"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    values = [float(row["largest_extracellular_loop_aa"] or 0) for row in rows]
    axes[0].hist(values, bins=40, color="#4c78a8", edgecolor="white")
    axes[0].set_xlabel("Largest extracellular segment (aa)")
    axes[0].set_ylabel("Core+Probable genes")
    axes[0].set_title("ECD/loop length")
    counts = [sum(row["accessibility_class"] == label for row in rows) for label in classes]
    axes[1].bar(classes, counts, color=["#2f855a", "#68a357", "#d6a33d", "#d46a3a", "#8c2d2d"])
    axes[1].set_xlabel("Accessibility class")
    axes[1].set_ylabel("Genes")
    axes[1].set_title("Fase 9 accessibility classes")
    fig.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / "ecd_length_distribution.svg", format="svg")
    plt.close(fig)


def write_notes(rows: list[dict[str, object]], flag_rows: list[dict[str, object]], metadata: dict[str, object]) -> None:
    class_lines = "\n".join(f"- {label}: {metadata['class_counts'][label]}" for label in ["A", "B", "C", "D", "E"])
    control_symbols = ["ERBB2", "CLDN18", "FGFR2", "TACSTD2", "EPCAM", "MET", "MSLN"]
    by_symbol = {str(row["hgnc_symbol"]): row for row in rows}
    control_lines = "\n".join(
        "- {symbol}: class={cls}, ECD={ecd}, TM={tm}, GPI={gpi}, isoform={iso}, T_score={score}".format(
            symbol=symbol,
            cls=by_symbol.get(symbol, {}).get("accessibility_class", "not_covered"),
            ecd=by_symbol.get(symbol, {}).get("largest_extracellular_loop_aa", ""),
            tm=by_symbol.get(symbol, {}).get("tm_helix_count", ""),
            gpi=by_symbol.get(symbol, {}).get("gpi_anchor_present", ""),
            iso=by_symbol.get(symbol, {}).get("isoform_resolution_status", ""),
            score=by_symbol.get(symbol, {}).get("T_score", ""),
        )
        for symbol in control_symbols
    )
    mandatory_lines = "\n".join(
        "- {symbol}: {status}; implication={implication}".format(
            symbol=symbol,
            status=by_symbol.get(symbol, {}).get("isoform_resolution_status", "not_covered"),
            implication="isoform-specific claims blocked from gene-level data",
        )
        for symbol in MANDATORY_ISOFORM_TARGETS
    )
    (DOCS_DIR / "fase9_topology_isoforms.md").write_text(
        f"""# Fase 9 Topology, Isoforms, and Extracellular Accessibility

Access date: {dt.date.today().isoformat()}

Fase 9 builds the topology component `T` for the Core+Probable surfaceome universe. The component is not a final biological ranking. It uses reviewed UniProt human feature fields for protein length, topological domains, transmembrane segments, signal peptide, lipid/GPI anchor, glycosylation, disulfide bonds, chains, domains, subcellular location, PTM comments, and Ensembl isoform mappings.

## Scope

Candidate genes assessed: {metadata['candidate_n']}.

UniProt feature coverage: {metadata['uniprot_feature_coverage']}/{metadata['candidate_n']}.

GPI-anchor annotations: {metadata['gpi_anchor_n']}.

Genes with D/E accessibility class: {metadata['low_accessibility_n']}.

Genes with cleavage, shedding, soluble, or secreted-isoform annotation: {metadata['shedding_or_soluble_n']}.

## Accessibility Classes

{class_lines}

Class A/B means a clear or inferred extracellular region supports antibody-accessibility review. Class C is possible but harder, usually for multipass proteins or shorter loops. Class D/E is not an automatic exclusion from the table, but it blocks Tier 1 antibody-targeting claims unless later structure/literature/candidate-card evidence provides a strong counterargument.

## Mandatory Isoform Handling

{mandatory_lines}

`CLDN18` and `FGFR2` remain gene-level in the current expression layers. `CLDN18.2` and `FGFR2b/IIIb` claims are therefore marked `isoform_unresolved` and cannot be used as proof that the pipeline resolved isoform-specific targets.

## Benchmark Controls

{control_lines}

`MSLN` illustrates why Fase 9 uses the expanded UniProt feature file: its GPI-anchor supports membrane accessibility even though the earlier Fase 2 topology-only raw file did not expose a transmembrane or topological-domain feature.

## Score Definition

`T_score` combines accessibility class, extracellular length, topology confidence, and isoform confidence, then subtracts conservative cleavage/shedding and soluble-decoy penalties. These penalties are candidate-card flags, not hard filters.

## Outputs

- `data/processed/topology_isoforms_ecd.tsv`
- `results/tables/isoform_risk_flags.tsv`
- `results/figures/ecd_length_distribution.svg`
""",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args(argv)
    topology_rows, flag_rows, metadata = build_rows()
    topology_fields = [
        "hgnc_symbol",
        "ensembl_gene_id",
        "uniprot_accession",
        "protein_name",
        "surfaceome_category",
        "uniprot_feature_status",
        "protein_length_aa",
        "tm_helix_count",
        "signal_peptide_present",
        "gpi_anchor_present",
        "n_terminal_orientation",
        "c_terminal_orientation",
        "extracellular_segment_count",
        "extracellular_segments",
        "total_extracellular_aa",
        "largest_extracellular_loop_aa",
        "topology_confidence",
        "topology_evidence_class",
        "accessibility_class",
        "accessibility_interpretation",
        "domain_architecture_flags",
        "glycosylation_site_count",
        "disulfide_bond_count",
        "cleavage_or_shedding_flag",
        "soluble_isoform_or_secreted_flag",
        "internalization_status",
        "isoform_count",
        "mapped_uniprot_isoforms",
        "isoform_confidence",
        "isoform_resolution_status",
        "accessibility_class_score",
        "extracellular_length_score",
        "shedding_penalty",
        "soluble_decoy_penalty",
        "T_score",
        "T_rank_percentile",
        "topology_notes",
    ]
    flag_fields = [
        "hgnc_symbol",
        "ensembl_gene_id",
        "uniprot_accession",
        "isoform_or_topology_issue",
        "isoform_resolution_status",
        "mapped_transcripts_or_isoforms",
        "clinical_target_context",
        "tiering_implication",
        "evidence_basis",
        "required_followup",
    ]
    write_tsv(PROCESSED_DIR / "topology_isoforms_ecd.tsv", topology_rows, topology_fields)
    write_tsv(TABLES_DIR / "isoform_risk_flags.tsv", flag_rows, flag_fields)
    plot_ecd_distribution(topology_rows)
    write_notes(topology_rows, flag_rows, metadata)
    print("Wrote Fase 9 topology/isoform/accessibility outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
