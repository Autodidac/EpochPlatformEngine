"""Audit tracked public source only; never upload build products or credentials."""
from pathlib import Path
import hashlib
import json
import subprocess

root = Path(__file__).resolve().parent.parent
files = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"]).decode().split("\0")
for required in ("LICENSE", "NOTICE", "TRADEMARKS.md", "CONTRIBUTOR_LICENSE.md"):
    if not (root / required).is_file():
        raise SystemExit("Missing license: " + required)
forbidden = {".env", ".codex", ".aws", ".ssh", "credentials.json", "auth.json", "EpochSelfCoding"}
records = []
for name in filter(None, files):
    path = Path(name)
    if any(part in forbidden or part.startswith(".env.") for part in path.parts):
        raise SystemExit("Private file in public source: " + name)
    if path.suffix.lower() in {".exe", ".dll", ".pdb", ".obj", ".gguf", ".safetensors", ".zip", ".pem", ".pfx"}:
        raise SystemExit("Non-source payload in public source: " + name)
    records.append({"path": name, "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()})
receipt = {"commit": subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"]).decode().strip(),
           "license": "MPL-2.0", "files": records,
           "scope": "Tracked source path/license audit; no binary publication or runtime acceptance"}
(root / "source-audit.json").write_text(json.dumps(receipt, indent=2) + "\n")
