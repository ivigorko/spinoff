"""Small Git data/secret guard. No client exports should be staged."""
import re
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
paths = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root).decode().split("\0")
errors = []
patterns = [rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", rb"gh[pousr]_[A-Za-z0-9]{30,}", rb"sk-proj-[A-Za-z0-9_-]{30,}"]
for name in set(paths) - {""}:
    path = root / name
    parts = Path(name).parts
    if any(p in {"workspace", "client-data", "raw", "exports", "reports", "tokens", "cookies"} for p in parts) or path.suffix in {".db", ".sqlite3", ".log"} or path.name.startswith(".env") and path.name != ".env.example":
        errors.append(name + ": private path must not be tracked")
    candidates = [path.read_bytes()] if path.is_file() else []
    indexed = subprocess.run(["git", "show", ":" + name], cwd=root, capture_output=True)
    if indexed.returncode == 0:
        candidates.append(indexed.stdout)
    if any(re.search(pattern, data) for pattern in patterns for data in candidates):
        errors.append(name + ": probable secret")
if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print("Repository guard passed (limited patterns; review staged files before committing).")
