"""Source inventory for native programs emitted by the V4 compiler.

The bootstrap C compiler continues to link the legacy core runtime. Native V4
programs also need the LLVM adapter and the compiler-private checked helpers.
Keep the adapter before the core for the established compatibility link order.
"""

SOURCE_NAMES = (
    "freak_llvm_runtime.c",
    "freak_v4_word_runtime.c",
    "freak_v4_numeric_runtime.c",
    "freak_v4_unicode_runtime.c",
    "freak_v4_system_runtime.c",
    "freak_v4_panic_runtime.c",
    "freak_runtime.c",
)

HEADER_NAMES = (
    "freak_runtime.h",
    "freak_v4_word_runtime.h",
    "freak_v4_numeric_runtime.h",
    "freak_v4_unicode_runtime.h",
    "freak_v4_unicode_lower_tables.h",
    "freak_v4_system_runtime.h",
    "freak_v4_panic_runtime.h",
)
