#!/usr/bin/env python3
"""
Validates data-manifest.json:
- Valid JSON format
- version is integer >= 1
- files is non-empty list
- Each file has:
  - id (non-empty string)
  - url (valid URL)
  - size (integer > 0)
  - sha256 (64 hex characters)
  - extract_to (non-empty string)
  - HTTP HEAD returns 200 (following redirects)
  - Content-Length matches size
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

def validate_manifest(manifest_path: Path) -> None:
    print(f"[*] Validating manifest at {manifest_path}...")
    if not manifest_path.exists():
        raise SystemExit(f"[-] Manifest file not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data.get("version"), int) or data["version"] < 1:
        raise SystemExit(f"[-] Invalid version: {data.get('version')}. Must be an integer >= 1.")

    if not isinstance(data.get("title"), str) or not data["title"].strip():
        raise SystemExit(f"[-] Invalid title: {data.get('title')}. Must be non-empty string.")

    files = data.get("files")
    if not isinstance(files, list) or len(files) == 0:
        raise SystemExit(f"[-] 'files' must be a non-empty list.")

    sha_pattern = re.compile(r"^[0-9a-fA-F]{64}$")

    for i, file_info in enumerate(files):
        file_id = file_info.get("id")
        if not isinstance(file_id, str) or not file_id.strip():
            raise SystemExit(f"[-] File at index {i} has invalid id: {file_id}")

        url = file_info.get("url")
        if not isinstance(url, str) or not (url.startswith("http://") or url.startswith("https://")):
            raise SystemExit(f"[-] File {file_id} has invalid url: {url}")

        size = file_info.get("size")
        if not isinstance(size, int) or size <= 0:
            raise SystemExit(f"[-] File {file_id} has invalid size: {size}. Must be positive integer.")

        sha256 = file_info.get("sha256")
        if not isinstance(sha256, str) or not sha_pattern.match(sha256):
            raise SystemExit(f"[-] File {file_id} has invalid sha256: {sha256}. Must be 64 hex characters.")

        extract_to = file_info.get("extract_to")
        if not isinstance(extract_to, str) or not extract_to.strip():
            raise SystemExit(f"[-] File {file_id} has invalid extract_to: {extract_to}")

        print(f"[*] Validating URL for '{file_id}': {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "ViceSideClient/1.0"})
        req.get_method = lambda: "HEAD"
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status_code = resp.status
                content_length_header = resp.headers.get("Content-Length")
                if status_code != 200:
                    raise SystemExit(f"[-] URL returned status {status_code}, expected 200: {url}")
                if content_length_header is not None:
                    content_length = int(content_length_header)
                    if content_length != size:
                        raise SystemExit(
                            f"[-] File {file_id} size mismatch: manifest says {size}, server Content-Length is {content_length}"
                        )
                    print(f"    [+] Content-Length verified: {content_length} bytes == {size}")
                else:
                    print(f"    [!] Warning: Server did not return Content-Length header, HEAD status 200 OK.")
        except Exception as e:
            raise SystemExit(f"[-] Failed to verify URL for {file_id}: {e}")

    print(f"[SUCCESS] data-manifest.json is completely valid! ({len(files)} files checked)")

if __name__ == "__main__":
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data-manifest.json").resolve()
    validate_manifest(path)
