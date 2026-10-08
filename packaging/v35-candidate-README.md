# V3.5 candidate archives

This packager assembles explicitly supplied native V3 tools and the exact payload
listed in packaging/distribution-files.manifest. It does not rebuild, install,
tag, publish, or replace the shipping tools. Python 3.10 or newer runs the
packager and independent test driver; native product use needs no Python compiler.

Run this as one command:

    python packaging/create_candidate_archive.py --repo /absolute/clean-checkout --freak /absolute/reconstruction/freak --hangar /absolute/reconstruction/hangar --build-record /absolute/reconstruction.json --output /absolute/candidate.tar.gz

Windows native images use the .exe tool names; an output ending in .zip selects
ZIP. Both formats contain one freak/ product directory, fixed timestamps,
canonical permissions and sorted entries. Atomic publication refuses existing
output. The output parent must already exist; final output must be outside the
checkout. The same inputs and packager produce the same archive bytes.

Final mode requires a clean checkout at the build record's exact source commit
and tree. The successful reconstruction must record identical before/after
hashes for all compiler and CLI sources, their manifest, runtime, vendor and
standard library inputs, distribution sources and manifest, VERSION, and the
actual seed C input. Diagnostic embedding inputs must also be inventoried when
present. Product version and build-time tool fingerprints are required. Supplied
native tools must match their recorded hashes; the packager selects no fallback.

An explicit --provisional creates an interim component archive. It still checks
every recorded input and native binary hash. Both its external report and its
internal metadata say provisional: true, disclose checkout state, and list
inputs the original reconstruction did not record. This mode cannot substitute
a newer payload for an older recorded payload or provide final acceptance proof.

The archive includes the raw build record and distribution manifest,
build-info.json, payload-inventory.json and SHA256SUMS. The payload inventory
describes product files; SHA256SUMS additionally covers metadata except itself.
Build info identifies version, compiler generation, capability markers, source
commit and Git tree, native image architecture, recorded build host/tools, and
input digests. The packager's JSON output reports the archive SHA256, which cannot
be included inside that same archive. Missing legacy tool fingerprints remain
unrecorded in provisional mode. These inventories verify bytes, not authenticity.

Run the independent gate with explicit inputs:

    python tests/v3_v35_candidate_archive.py --repo /absolute/checkout --freak /absolute/reconstruction/freak --hangar /absolute/reconstruction/hangar --build-record /absolute/reconstruction.json --clang /absolute/clang --evidence /absolute/archive-gate.json

Add --provisional for an interim reconstruction. The driver checks reproducible
exact contents in both formats, extracts outside the repository, invokes native
version and Doctor JSON commands, and confirms public build failure with missing
runtime payload. Rejection controls cover stale inputs/tools, unsafe and duplicate
destinations, symlinks, incomplete final inventory, disguised scripts, existing
output, failed private writes and a concurrent destination creator.
