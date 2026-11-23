/* V3.5 C-host adapter for the LLVM bridge: word-taking entry points.
   Passed to the tool build with -include, like tools/lsp_stdio.h. */
#ifndef FREAK_LLVM_BRIDGE_V35_H
#define FREAK_LLVM_BRIDGE_V35_H

#include "freak_runtime.h"
#include "freak_llvm_bridge.h"

int64_t freak_lb35_session_new(freak_word triple, freak_word name, int64_t opt);
freak_word freak_lb35_error(int64_t session);
int64_t freak_lb35_struct_begin(int64_t session, freak_word name);
int64_t freak_lb35_function(int64_t session, freak_word name, int64_t fn_type, int64_t linkage);
int64_t freak_lb35_global_bytes(int64_t session, freak_word name, freak_word bytes, int64_t linkage);
int64_t freak_lb35_block(int64_t session, int64_t function, freak_word name);
int64_t freak_lb35_attribute(int64_t session, int64_t function, int64_t index, freak_word name);
int64_t freak_lb35_emit(int64_t session, int64_t format, freak_word path);

#endif
