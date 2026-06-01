from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote

import requests


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOKEN_ENV = "ZENODO_ACCESS_TOKEN"
PUBLISH_CONFIRMATION = "PUBLISH_ZENODO_RECORD"


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def require_token(env_name: str) -> str:
    token = os.environ.get(env_name)
    if not token:
        raise SystemExit(
            f"Missing {env_name}. Create a Zenodo personal access token with deposit "
            f"permissions and set it only in the local environment."
        )
    return token


def response_json(response: requests.Response) -> dict:
    if not response.content:
        return {}
    try:
        return response.json()
    except ValueError:
        return {"raw": response.text[:2000]}


def api_request(
    method: str,
    url: str,
    token: str,
    *,
    payload: dict | None = None,
    expected: tuple[int, ...] = (200,),
    timeout: tuple[int, int | None] = (30, 300),
) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    response = requests.request(
        method,
        url,
        headers=headers,
        json=payload,
        timeout=timeout,
    )
    if response.status_code not in expected:
        body = response_json(response)
        raise SystemExit(
            f"Zenodo API request failed: {method} {url} -> {response.status_code}\n"
            f"{json.dumps(body, indent=2, sort_keys=True)[:4000]}"
        )
    return response_json(response)


def create_draft(api_base: str, token: str) -> dict:
    return api_request(
        "POST",
        f"{api_base}/deposit/depositions",
        token,
        payload={},
        expected=(201,),
    )


def retrieve_draft(api_base: str, token: str, deposition_id: str) -> dict:
    return api_request(
        "GET",
        f"{api_base}/deposit/depositions/{deposition_id}",
        token,
        expected=(200,),
    )


def update_metadata(api_base: str, token: str, deposition_id: str, metadata: dict) -> dict:
    return api_request(
        "PUT",
        f"{api_base}/deposit/depositions/{deposition_id}",
        token,
        payload=metadata,
        expected=(200,),
    )


def upload_file(bucket_url: str, token: str, path: Path, remote_name: str | None = None) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    filename = remote_name or path.name
    url = f"{bucket_url.rstrip('/')}/{quote(filename)}"
    size_gb = path.stat().st_size / (1024**3)
    print(f"Uploading {path.name} ({size_gb:.2f} GiB) to Zenodo draft...")
    with path.open("rb") as handle:
        response = requests.put(
            url,
            data=handle,
            headers={"Authorization": f"Bearer {token}"},
            timeout=(30, None),
        )
    if response.status_code not in (200, 201):
        body = response_json(response)
        raise SystemExit(
            f"Zenodo file upload failed: {path} -> {response.status_code}\n"
            f"{json.dumps(body, indent=2, sort_keys=True)[:4000]}"
        )
    return response_json(response)


def publish_draft(api_base: str, token: str, deposition_id: str) -> dict:
    return api_request(
        "POST",
        f"{api_base}/deposit/depositions/{deposition_id}/actions/publish",
        token,
        expected=(202,),
        timeout=(30, 300),
    )


def infer_metadata_path(archive: Path) -> Path:
    return archive.with_name(f"{archive.stem}.zenodo_metadata.json")


def default_upload_files(archive: Path) -> list[Path]:
    files = [archive]
    checksum = archive.with_suffix(archive.suffix + ".sha256")
    if checksum.exists():
        files.append(checksum)
    return files


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Zenodo draft and upload the frozen data package ZIP."
    )
    parser.add_argument("archive", help="Frozen data package ZIP built by build_frozen_data_package.py.")
    parser.add_argument(
        "--metadata-json",
        help="Zenodo metadata JSON. Defaults to the archive stem plus .zenodo_metadata.json.",
    )
    parser.add_argument(
        "--extra-file",
        action="append",
        default=[],
        help="Additional file to upload to the Zenodo draft. Can be repeated.",
    )
    parser.add_argument(
        "--deposition-id",
        help="Use an existing unpublished Zenodo deposition instead of creating a new draft.",
    )
    parser.add_argument(
        "--token-env",
        default=DEFAULT_TOKEN_ENV,
        help=f"Environment variable containing the Zenodo token. Default: {DEFAULT_TOKEN_ENV}.",
    )
    parser.add_argument(
        "--sandbox",
        action="store_true",
        help="Use https://sandbox.zenodo.org instead of production Zenodo.",
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Create/update the draft metadata without uploading files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without contacting Zenodo.",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish the draft after upload. Off by default.",
    )
    parser.add_argument(
        "--confirm-publish",
        help=f"Required with --publish. Must equal {PUBLISH_CONFIRMATION}.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    archive = Path(args.archive).resolve()
    if not archive.exists():
        raise SystemExit(f"Archive not found: {archive}")
    metadata_path = Path(args.metadata_json).resolve() if args.metadata_json else infer_metadata_path(archive)
    if not metadata_path.exists():
        raise SystemExit(f"Metadata JSON not found: {metadata_path}")
    metadata = load_json(metadata_path)
    upload_files = default_upload_files(archive) + [Path(path).resolve() for path in args.extra_file]
    api_base = "https://sandbox.zenodo.org/api" if args.sandbox else "https://zenodo.org/api"

    if args.publish and args.confirm_publish != PUBLISH_CONFIRMATION:
        raise SystemExit(
            f"Refusing to publish. Re-run with --confirm-publish {PUBLISH_CONFIRMATION} "
            "only after reviewing the Zenodo draft."
        )

    print(f"Zenodo API: {api_base}")
    print(f"Archive: {archive}")
    print(f"Metadata: {metadata_path}")
    print("Files to upload:")
    for path in upload_files:
        print(f"- {path}")

    if args.dry_run:
        print("Dry run only. No Zenodo request was made.")
        return 0

    token = require_token(args.token_env)
    if args.deposition_id:
        draft = retrieve_draft(api_base, token, args.deposition_id)
    else:
        draft = create_draft(api_base, token)
    deposition_id = str(draft["id"])
    draft = update_metadata(api_base, token, deposition_id, metadata)
    if not args.skip_upload:
        bucket = draft.get("links", {}).get("bucket")
        if not bucket:
            raise SystemExit("Zenodo draft response did not include a bucket upload URL.")
        for path in upload_files:
            upload_file(bucket, token, path)
    draft = retrieve_draft(api_base, token, deposition_id)
    reserved_doi = draft.get("metadata", {}).get("prereserve_doi", {}).get("doi")
    print(f"Draft deposition id: {deposition_id}")
    print(f"Draft URL: {draft.get('links', {}).get('html')}")
    if reserved_doi:
        print(f"Reserved DOI: {reserved_doi}")

    if args.publish:
        published = publish_draft(api_base, token, deposition_id)
        print(f"Published record URL: {published.get('links', {}).get('html')}")
        doi = published.get("metadata", {}).get("doi") or reserved_doi
        if doi:
            print(f"Published DOI: {doi}")
    else:
        print("Not published. Review the draft in Zenodo before publishing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
