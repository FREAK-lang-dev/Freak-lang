/* Byte-exact stdio for the Maverick language server (tools/lsp_server.fk).
   LSP frames are Content-Length counted bytes, so the server cannot use the
   line-oriented `say`/`process::input` runtime calls. Protocol logic stays in
   FREAK; this file only moves bytes and handles JSON string escapes. */
#ifndef FREAK_LSP_STDIO_H
#define FREAK_LSP_STDIO_H

#include <stdbool.h>
#include <stdint.h>
#include "freak_runtime.h"

void lspio_init(void);
bool lspio_at_eof(void);
freak_word lspio_read_line(void);
freak_word lspio_read_exact(int64_t count);
void lspio_write_message(freak_word body);
void lspio_log(freak_word message);
int64_t lspio_byte_at(freak_word text, int64_t index);
int64_t lspio_find_byte(freak_word text, int64_t byte_value, int64_t start);
int64_t lspio_json_string_end(freak_word text, int64_t start);
freak_word lspio_json_unescape(freak_word text, int64_t start);
freak_word lspio_json_escape(freak_word text);
bool lspio_is_windows(void);
freak_word lspio_uri_to_path(freak_word uri);
bool lspio_file_exists(freak_word path);
freak_word lspio_run_capture(freak_word command);

bool lspio_is_worker(void);
int64_t lspio_env_int(freak_word name, int64_t fallback);
int64_t lspio_rss_mb(void);
bool lspio_worker_spawn(void);
void lspio_worker_send(freak_word body);
freak_word lspio_worker_read_line(void);
freak_word lspio_worker_read_exact(int64_t count);
bool lspio_worker_at_eof(void);
int64_t lspio_worker_wait(void);

#endif
