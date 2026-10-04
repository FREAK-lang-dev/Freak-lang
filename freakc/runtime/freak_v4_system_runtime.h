#pragma once

#include <stdint.h>

/* Compiler-private V4 system ABI, using the live owned word handles supplied
   by freak_v4_word_runtime. It is not a foreign ABI for FREAK word/results.

   Setup snapshots argv before source main. Count includes the program at 0.
   Each arg call returns an independent owner; out-of-range indexes return an
   owned empty word. OS argument vectors cannot contain embedded NUL bytes.
   Windows snapshots the Unicode command line, rather than narrow CRT argv.
   Setup/shutdown are entry/lifetime operations, not concurrent mutation APIs. */
void freak_v4_process_setup_args(int64_t argc, int64_t argv);
int64_t freak_v4_process_args_count(void);
int64_t freak_v4_process_arg(int64_t index);

/* Checked scalar-result adapter for the same immutable snapshot. Valid indexes,
   including valid empty arguments, return tag 1 and a fresh owned word. Negative
   and out-of-range indexes return tag 0 and a fresh nonempty owned diagnostic,
   without printing. Both nonnull output pointers must designate distinct slots;
   invalid slots are a private fatal boundary. Caller drops/transfers the payload.
   This void/outslot ABI does not expose a C struct or a public FREAK Result ABI. */
void freak_v4_process_arg_checked(int64_t index, int64_t *out_is_ok,
                                  int64_t *out_payload);
void freak_v4_process_shutdown_args(void);

/* Borrows path. Success (tag 1) and failure (tag 0) both transfer exactly one
   independently owned word to the caller. Empty readable files are success.
   Sized UTF-8 contents preserve NUL; paths reject NUL. Reads checked regular
   files, without waiting on a POSIX FIFO. Ordinary failures return nonempty
   errors without printing. Allocation failure preventing any error owner is
   fatal. Both output pointers are required and must designate distinct slots.
   The adapter deliberately avoids platform-dependent C struct return ABIs. */
void freak_v4_fs_read(int64_t path, int64_t *out_is_ok, int64_t *out_payload);
