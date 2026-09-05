# V3 performance workloads

Run the quick C/LLVM matrix with an exact compiler and Clang:

```text
python -u tools/v3_performance_lab.py --cli <freak> --clang <clang> --quick --profile O2 --backend c --backend llvm --output quick.json
python -u tools/v3_performance_lab.py --validate-output quick.json --cli <freak>
```

The compiler must have its matching runtime and standard library in its normal
installed or checkout location. The lab intentionally discards inherited
`FREAK_HOME`, compiler flags, and unrelated environment variables.

Omit `--quick` for the sizes below. Select a case explicitly for large runs, for
example `--case word_repeated_100m --samples 1 --warmups 0 --timeout 120`.
Without case/profile filters the lab runs every workload and supported profile.
Full-size runs require available memory and a deliberate resource budget;
`bytes_copy_1gb` alone needs about 2 GB of live payload storage plus runtime,
allocator, compiler and operating-system headroom. A decimal GB means
1,000,000,000 bytes here.

| Case | Default size | Quick size | Comparison class |
|---|---:|---:|---|
| word_dynamic_append | 1,000,000 appends | 1,000 | same-work |
| word_dynamic_append_100m | 100,000,000 appends | 4,096 | same-work |
| word_repeated_100m | 100,000,000 bytes | 4,096 | idiomatic-fast |
| word_builder_known_capacity | 100,000,000 one-byte appends, reserved | 4,096 | idiomatic-fast |
| word_builder_unknown_capacity | 100,000,000 one-byte appends, geometric growth | 4,096 | idiomatic-fast |
| bytes_write_100m | 100,000,000 byte writes, unreserved | 4,096 | same-work |
| bytes_copy_1gb | one independent 1,000,000,000-byte slice copy | 65,536 | idiomatic-fast |
| bytes_sequential_write | 100,000,000 bytes in signed int64 records | 4,096 | same-work |
| bytes_sequential_read | four reads of 100,000,000 bytes in int64 records | 4 × 4,096 | same-work |
| bytes_endian_roundtrip | 1,000,000 signed LE/BE pairs, 16 MB | 256 pairs | same-work |

The original CPU, startup and compile fixtures remain registered. The manifest
is the authority for arguments, source hashes, exact output and mode metadata.
No schema change is needed: comparison class, declared call counts and byte
counts are scalar workload parameters preserved in existing result evidence.

Every timing covers the entire process, including setup, content verification
and cleanup. For example, the copy fixture constructs its input and checks every
copied byte through the word checksum; it does not report isolated memcpy
throughput. The sequential-read case includes a write setup and four read
passes. Report those scopes when comparing languages or APIs.

Word checksums use FNV-1a 64-bit with the sign bit masked. Byte writes use an
ordered polynomial checksum (base 131, modulus 1,000,000,007). Sequential int64
work uses an independently calculated sum of the modulo-65,521 pattern. Endian
pairs validate every decoded value, then report their sum. These are deterministic
correctness oracles, not cryptographic authenticity claims. Output remains small
even for full-size inputs; lengths, final cursors and successful buffer statuses
are checked where applicable. The copy fixture releases the original before
checking copied contents, exercising independent ownership.

Call/byte counts in workload parameters describe the requested algorithm; they
are not measured allocation counters. Runtime counters remain explicitly
unavailable unless the runtime stats sentinel is emitted. Existing ownership and
growth-complexity tests belong to the foundation regression suites. This patch
does not claim allocation measurements or performance wins from quick runs.

Further categories remain to be added: common word operations, collections,
JSON, filesystem/process workloads, TCP and HTTP. External language comparisons
must preserve the distinction between same-work algorithms and idiomatic APIs.
