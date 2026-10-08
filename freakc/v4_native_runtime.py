"""Read the closed native V4 runtime inventory used by bootstrap and packaging."""
from pathlib import Path, PurePosixPath

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "src/compiler/v4/native-runtime.manifest"

def read_inventory(path: Path = MANIFEST_PATH) -> tuple[tuple[str, str], ...]:
    rows = []
    seen = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        fields = raw.split(" ")
        if len(fields) != 2 or fields[0] not in {"source", "header", "asset", "marker"}:
            raise ValueError("invalid native runtime inventory record")
        role, name = fields
        components = name.split("/")
        if (not name.isascii() or "\\" in name or ":" in name or
                PurePosixPath(name).is_absolute() or
                any(part in {"", ".", ".."} for part in components) or name.casefold() in seen):
            raise ValueError("unsafe or duplicate native runtime inventory path")
        if role == "source" and not name.endswith(".c"):
            raise ValueError("native runtime source must be C")
        seen.add(name.casefold())
        rows.append((role, name))
    if not rows or not any(role == "source" for role, _ in rows):
        raise ValueError("empty native runtime inventory")
    return tuple(rows)

RUNTIME_INVENTORY = read_inventory()
SOURCE_NAMES = tuple(name for role, name in RUNTIME_INVENTORY if role == "source")
# Existing build gates resolve these names below freakc/runtime; vendor records
# are carried in the complete inventory and resolved by runtime_file instead.
HEADER_NAMES = tuple(name for role, name in RUNTIME_INVENTORY
                     if role == "header" and not name.startswith("third_party/"))
RUNTIME_FILE_NAMES = tuple(name for _, name in RUNTIME_INVENTORY)

def runtime_file(runtime_root: Path, name: str) -> Path:
    if name not in RUNTIME_FILE_NAMES:
        raise ValueError("file is not in the native runtime inventory")
    direct = runtime_root / name
    if direct.is_file():
        return direct
    if runtime_root.parts[-2:] == ("freakc", "runtime") and name.startswith("third_party/"):
        return runtime_root.parents[1] / name
    return direct
