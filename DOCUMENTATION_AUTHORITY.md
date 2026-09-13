# Documentation Authority

Which document owns which truth, who keeps it honest, and how stale docs get
caught. Ownership here means *stewardship* (reviewing, updating, flagging
drift) — enforced via `CODEOWNERS` team review, not personal fiefdoms.

## Per-subject owners

| Subject | Authority | Steward |
|---|---|---|
| Language semantics (normative) | `freak-full-bible.md` | Maintainers |
| Bible-vs-implementation status | `freak-conformance-audit.md` + `freakc/auditor.py` | Maintainers |
| V4 architecture & crate protocols | `src/compiler/v4/README.md` | Maintainers |
| V3 architecture & reconstruction | `src/compiler/v3/README.md` | Maintainers |
| Public usage & installation | `README.md` | Maintainers |
| Contributing, labels, local gates | `CONTRIBUTING.md`, `.github/labels.yml`, `tools/check_contributor.py` | Maintainers |
| Package authoring | `docs/hangar-authoring.md` | Ministry of the Shelves |
| Compiler history | `docs/history/pioneers.md` | Ministry of the Record |
| Culture (non-normative) | `docs/ministry-culture.md` | Ministry of Welcome |
| Color/output contract (decision) | `docs/decision-terminal-color.md` | Ministry of the Shelves |
| Bootstrap pointers & exit phases | `docs/bootstrap-map.md` | Ministry of the Record |
| Authorship record | Git history (`AUTHORS.md` explains, history decides) | — |

Rules of precedence: the bible wins over implementations; executable checks
win over status prose; owner READMEs win over pointer docs like
`docs/bootstrap-map.md`; culture docs win over nothing.

## Freshness contract

1. **Behavior PRs update docs in the same PR.** A compiler/stdlib/CLI change
   without its doc delta is incomplete review-wise.
2. **Status claims cite evidence.** "Complete" means a named executable check
   passes; link it. Anything weaker says "partial" and names the boundary.
3. **Stale markers.** A doc known to lag its implementation gets a
   `> STALE as of <date>: <what drifted>` banner at the top instead of silent
   rot. Removing the banner requires fixing the drift, not deleting it.
4. **Quarterly sweep.** The Ministry of the Record re-runs
   `tools/check_contributor.py` and `python -u -m freakc audit-conformance`,
   samples each authority doc against the tree, and files issues for drift.
5. **Lore below tech.** Flavor (ramen, Freakium, spectral jokes) never
   precedes or buries instructions in contributor-facing docs.
