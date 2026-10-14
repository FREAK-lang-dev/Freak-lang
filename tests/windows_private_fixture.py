"""Prepare explicitly fresh Python fixture directories for checked publication.

The Windows public contract requires caller-owned private destination parents.
Create this facade immediately after an exclusive TemporaryDirectory, then name
only fresh Python-created children before their first public use. Runtime-created
directories, existing directories, and mutable output walks are outside its scope.
The bootstrap helper performs all native held-identity and token-default checks.
"""
from __future__ import annotations

import os
from pathlib import Path


class WindowsPrivateFixture:
    def __init__(self, root: Path, evidence: Path | None = None) -> None:
        self.root = root
        self.evidence = evidence
        self.report: dict | None = None
        if os.name == 'nt':
            from v3_v35_bootstrap_native import windows_private_root
            self.report = windows_private_root(root, evidence)

    def claim_fresh_directories(self, *directories: Path) -> None:
        """Claim only caller-declared fresh children, never runtime outputs."""
        if os.name == 'nt':
            from v3_v35_bootstrap_native import windows_claim_fixture_directories
            if self.report is None:
                raise RuntimeError('Windows private fixture root was not prepared')
            windows_claim_fixture_directories(self.root, set(directories), self.evidence, self.report)
