"""Creating a project and reading and writing its state file, tortoise.json."""

import json
import os
import tempfile
from pathlib import Path

# The stages in order, with the name the author sees.
STAGES = {
    "prd-review": "PRD review",
    "ideas": "Ideas",
    "spec": "Spec",
    "architecture": "Architecture",
    "plan": "Plan",
    "build": "Build",
    "gate": "Milestone gate",
    "final-checks": "Final checks",
}

EMPTY_DECISION_LOG = """# Decisions

Every material decision for this project, in the order it was made. A model
can only propose a decision; only the author settles one.

## Glossary
"""


def init_project(root: Path, name: str, test_command: str) -> dict[str, list[str]]:
    """Create the state file and an empty decision log, never overwriting a file.

    Works in a new or an existing repository. Returns which files were created
    and which already existed and were left alone.
    """
    (root / "docs").mkdir(exist_ok=True)
    state = {
        "name": name,
        "stage": "prd-review",
        "test_command": test_command,
        "approvals": [],
    }
    files = {
        "tortoise.json": json.dumps(state, indent=2) + "\n",
        "docs/DECISIONS.md": EMPTY_DECISION_LOG,
    }
    result: dict[str, list[str]] = {"created": [], "kept": []}
    for relative, text in files.items():
        try:
            # Mode "x" fails if the file exists, so an existing file is never replaced.
            with open(root / relative, "x") as handle:
                handle.write(text)
            result["created"].append(relative)
        except FileExistsError:
            result["kept"].append(relative)
    return result


def write_safely(path: Path, text: str) -> None:
    """Replace a file's contents so a crash leaves either the old or the new version, never half of one.

    The new text goes to a temporary file in the same folder, then one rename swaps it in.
    """
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(handle, "w") as file:
            file.write(text)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    except BaseException:
        os.unlink(temporary)
        raise


def load_state(root: Path) -> dict:
    return json.loads((root / "tortoise.json").read_text())
