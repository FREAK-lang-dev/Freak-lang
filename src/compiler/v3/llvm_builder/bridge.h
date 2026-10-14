#ifndef FREAK_EXPERIMENTAL_LLVM_BUILDER_BRIDGE_H
#define FREAK_EXPERIMENTAL_LLVM_BUILDER_BRIDGE_H

#include "freak_runtime.h"

/* This experimental compiler host is built through V3 --c. Words therefore
 * use freak_word, never the shipping LLVM integer-word ABI. Every other
 * boundary value is int64_t; native LLVM references remain private to C. */
int64_t freak_ib_session_new(freak_word name, int64_t optimization);
freak_word freak_ib_error(int64_t session);
int64_t freak_ib_session_release(int64_t session);
int64_t freak_ib_live_sessions(void);
int64_t freak_ib_live_tickets(void);
int64_t freak_ib_function(int64_t session, freak_word name, int64_t parameters,
                          int64_t returns_integer);
int64_t freak_ib_parameter(int64_t session, int64_t function, int64_t index);
int64_t freak_ib_block(int64_t session, int64_t function, freak_word name);
int64_t freak_ib_position(int64_t session, int64_t block);
int64_t freak_ib_integer(int64_t session, int64_t value);
int64_t freak_ib_boolean(int64_t session, int64_t value);
int64_t freak_ib_slot(int64_t session);
int64_t freak_ib_load(int64_t session, int64_t slot);
int64_t freak_ib_store(int64_t session, int64_t slot, int64_t value);
int64_t freak_ib_arithmetic(int64_t session, int64_t operation,
                           int64_t left, int64_t right);
int64_t freak_ib_negate(int64_t session, int64_t value);
int64_t freak_ib_compare(int64_t session, int64_t operation,
                        int64_t left, int64_t right);
int64_t freak_ib_not(int64_t session, int64_t value);
int64_t freak_ib_call_begin(int64_t session, int64_t function);
int64_t freak_ib_call_argument(int64_t session, int64_t value);
int64_t freak_ib_call_end(int64_t session);
int64_t freak_ib_say(int64_t session, int64_t value);
int64_t freak_ib_jump(int64_t session, int64_t destination);
int64_t freak_ib_branch(int64_t session, int64_t condition,
                       int64_t then_block, int64_t else_block);
int64_t freak_ib_return(int64_t session, int64_t value);
int64_t freak_ib_unreachable(int64_t session);
int64_t freak_ib_native_main(int64_t session, int64_t function);
int64_t freak_ib_emit_object(int64_t session, freak_word output);

#endif
