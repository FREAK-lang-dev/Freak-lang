/* In-process LLVM for V4: the backend delivery lane's B2 bridge.
 *
 * FREAK code drives LLVM's IRBuilder through LLVM's C API without any
 * LLVM pointer crossing into FREAK. Every LLVM object lives in a session;
 * FREAK holds int64 tickets that name a session, an object kind and a slot.
 *
 * Contract (see BACKEND_DELIVERY.md, "B2: the LLVM bridge"):
 * - One session owns one LLVM context, module, builder and target machine.
 *   Releasing the session disposes all of them and invalidates every ticket
 *   it handed out; a ticket from a released or other session is refused.
 * - Every call returns int64. A ticket is > 0. 0 means success for calls
 *   that produce nothing. A negative value is an error code (FREAK_LB_E_*),
 *   and freak_lb_error_text() returns the session's last message.
 * - Kinds are checked before LLVM is called: passing a type where a value
 *   belongs, a block of another function, or a non-pointer to load is an
 *   error result, never undefined behaviour inside LLVM.
 * - No C++ exception crosses this boundary: only LLVM's C API is used, and
 *   LLVM is built without exceptions. LLVM fatal errors (out of memory,
 *   broken backend invariants) still end the process, through LLVM's own
 *   handler; the bridge installs one that names the bridge first.
 * - Names and paths are byte strings with an explicit length. The bytes are
 *   copied; the caller keeps ownership. Adapters for each FREAK word ABI
 *   live in separate files (freak_llvm_bridge_v35.c for the V3.5 C host).
 * - Single threaded. Bounded: FREAK_LB_MAX_SESSIONS sessions and
 *   FREAK_LB_MAX_TICKETS tickets per session.
 */
#ifndef FREAK_LLVM_BRIDGE_H
#define FREAK_LLVM_BRIDGE_H

#include <stddef.h>
#include <stdint.h>

#define FREAK_LB_MAX_SESSIONS 16
#define FREAK_LB_MAX_TICKETS (1 << 24)

/* Error results. */
#define FREAK_LB_E_SESSION   (-1)  /* unknown, released or foreign session */
#define FREAK_LB_E_TICKET    (-2)  /* unknown ticket or one of another session */
#define FREAK_LB_E_KIND      (-3)  /* ticket of the wrong kind or type */
#define FREAK_LB_E_ARGUMENT  (-4)  /* argument out of range */
#define FREAK_LB_E_LIMIT     (-5)  /* session or ticket bound reached */
#define FREAK_LB_E_TARGET    (-6)  /* unknown triple or no target machine */
#define FREAK_LB_E_VERIFY    (-7)  /* module or function failed verification */
#define FREAK_LB_E_PASSES    (-8)  /* the pass pipeline reported an error */
#define FREAK_LB_E_EMIT      (-9)  /* object or IR could not be written */
#define FREAK_LB_E_STATE     (-10) /* call out of order (no open call, no block) */
#define FREAK_LB_E_MEMORY    (-11) /* allocation failed */

/* Integer and float binary operations (freak_lb_binary). */
enum {
    FREAK_LB_ADD = 1, FREAK_LB_SUB, FREAK_LB_MUL, FREAK_LB_SDIV, FREAK_LB_UDIV,
    FREAK_LB_SREM, FREAK_LB_UREM, FREAK_LB_AND, FREAK_LB_OR, FREAK_LB_XOR,
    FREAK_LB_SHL, FREAK_LB_LSHR, FREAK_LB_ASHR,
    FREAK_LB_FADD, FREAK_LB_FSUB, FREAK_LB_FMUL, FREAK_LB_FDIV, FREAK_LB_FREM
};

/* Integer predicates (freak_lb_icmp), in LLVM's order. */
enum {
    FREAK_LB_EQ = 1, FREAK_LB_NE, FREAK_LB_UGT, FREAK_LB_UGE, FREAK_LB_ULT,
    FREAK_LB_ULE, FREAK_LB_SGT, FREAK_LB_SGE, FREAK_LB_SLT, FREAK_LB_SLE
};

/* Float predicates (freak_lb_fcmp): ordered comparisons, plus UNE for !=. */
enum {
    FREAK_LB_FOEQ = 1, FREAK_LB_FONE, FREAK_LB_FOGT, FREAK_LB_FOGE,
    FREAK_LB_FOLT, FREAK_LB_FOLE, FREAK_LB_FUNE
};

/* Casts (freak_lb_cast). */
enum {
    FREAK_LB_TRUNC = 1, FREAK_LB_ZEXT, FREAK_LB_SEXT, FREAK_LB_FPTOSI,
    FREAK_LB_FPTOUI, FREAK_LB_SITOFP, FREAK_LB_UITOFP, FREAK_LB_FPTRUNC,
    FREAK_LB_FPEXT, FREAK_LB_PTRTOINT, FREAK_LB_INTTOPTR, FREAK_LB_BITCAST
};

/* Linkage (freak_lb_function, freak_lb_global). */
enum { FREAK_LB_EXTERNAL = 1, FREAK_LB_INTERNAL, FREAK_LB_PRIVATE };

/* Object file formats are the target's; IR output is text. */
enum { FREAK_LB_OBJECT = 1, FREAK_LB_ASSEMBLY, FREAK_LB_IR_TEXT };

/* Sessions. triple: canonical target triple. opt: 0..3, used for the target
   machine's code generation level. */
int64_t freak_lb_session_new(const char* triple, size_t triple_len,
                             const char* name, size_t name_len, int64_t opt);
int64_t freak_lb_session_release(int64_t session);
int64_t freak_lb_live_sessions(void);
int64_t freak_lb_live_tickets(int64_t session);
/* The last error message of a session (or of session creation when
   session <= 0). Valid until the next bridge call. */
const char* freak_lb_error_text(int64_t session, size_t* length);
int64_t freak_lb_llvm_major(void);

/* Types. */
int64_t freak_lb_type_int(int64_t session, int64_t bits);
int64_t freak_lb_type_double(int64_t session);
int64_t freak_lb_type_float(int64_t session);
int64_t freak_lb_type_ptr(int64_t session);
int64_t freak_lb_type_void(int64_t session);
int64_t freak_lb_type_array(int64_t session, int64_t element, int64_t count);
/* Struct and function types are built in steps: begin, add members, end.
   A named struct (name_len > 0) is identified by name and may be built once. */
int64_t freak_lb_struct_begin(int64_t session, const char* name, size_t name_len);
int64_t freak_lb_struct_field(int64_t session, int64_t type);
int64_t freak_lb_struct_end(int64_t session, int64_t packed);
int64_t freak_lb_fn_type_begin(int64_t session, int64_t return_type);
int64_t freak_lb_fn_type_param(int64_t session, int64_t type);
int64_t freak_lb_fn_type_end(int64_t session, int64_t variadic);

/* Target layout questions, answered by the session's target data layout. */
int64_t freak_lb_type_size(int64_t session, int64_t type);       /* ABI size, bytes */
int64_t freak_lb_type_align(int64_t session, int64_t type);      /* ABI alignment */
int64_t freak_lb_field_offset(int64_t session, int64_t struct_type, int64_t field);

/* Functions, globals and blocks. */
int64_t freak_lb_function(int64_t session, const char* name, size_t name_len,
                          int64_t fn_type, int64_t linkage);
int64_t freak_lb_param(int64_t session, int64_t function, int64_t index);
int64_t freak_lb_global_bytes(int64_t session, const char* name, size_t name_len,
                              const char* bytes, size_t length, int64_t linkage);
int64_t freak_lb_block(int64_t session, int64_t function, const char* name, size_t name_len);
int64_t freak_lb_position(int64_t session, int64_t block);
int64_t freak_lb_current_block(int64_t session);
int64_t freak_lb_block_terminated(int64_t session, int64_t block);

/* Constants. */
int64_t freak_lb_const_int(int64_t session, int64_t type, int64_t value);
int64_t freak_lb_const_double_bits(int64_t session, int64_t type, int64_t bits);
int64_t freak_lb_const_null(int64_t session, int64_t type);
int64_t freak_lb_const_zero(int64_t session, int64_t type);
int64_t freak_lb_type_of(int64_t session, int64_t value);

/* Instructions at the builder's position. */
int64_t freak_lb_alloca(int64_t session, int64_t type);
int64_t freak_lb_load(int64_t session, int64_t type, int64_t pointer);
int64_t freak_lb_store(int64_t session, int64_t value, int64_t pointer);
int64_t freak_lb_binary(int64_t session, int64_t op, int64_t left, int64_t right);
int64_t freak_lb_neg(int64_t session, int64_t value);
int64_t freak_lb_icmp(int64_t session, int64_t predicate, int64_t left, int64_t right);
int64_t freak_lb_fcmp(int64_t session, int64_t predicate, int64_t left, int64_t right);
int64_t freak_lb_cast(int64_t session, int64_t op, int64_t value, int64_t type);
int64_t freak_lb_select(int64_t session, int64_t condition, int64_t yes, int64_t no);
int64_t freak_lb_field_ptr(int64_t session, int64_t struct_type, int64_t pointer, int64_t field);
int64_t freak_lb_element_ptr(int64_t session, int64_t element_type, int64_t pointer, int64_t index);
int64_t freak_lb_extract(int64_t session, int64_t aggregate, int64_t index);
int64_t freak_lb_insert(int64_t session, int64_t aggregate, int64_t value, int64_t index);
/* Calls: begin with the callee and its function type, add arguments, end. */
int64_t freak_lb_call_begin(int64_t session, int64_t fn_type, int64_t callee);
int64_t freak_lb_call_arg(int64_t session, int64_t value);
int64_t freak_lb_call_end(int64_t session);
/* Phi nodes: create, then add (value, block) pairs. */
int64_t freak_lb_phi(int64_t session, int64_t type);
int64_t freak_lb_phi_incoming(int64_t session, int64_t phi, int64_t value, int64_t block);
/* Terminators. */
int64_t freak_lb_br(int64_t session, int64_t block);
int64_t freak_lb_cond_br(int64_t session, int64_t condition, int64_t yes, int64_t no);
int64_t freak_lb_ret(int64_t session, int64_t value);
int64_t freak_lb_ret_void(int64_t session);
int64_t freak_lb_unreachable(int64_t session);

/* Function attributes by LLVM name (nounwind, noreturn, ...): index -1 is the
   function, 0 the return value, 1.. the parameters. */
int64_t freak_lb_attribute(int64_t session, int64_t function, int64_t index,
                           const char* name, size_t name_len);

/* Whole module. */
int64_t freak_lb_verify(int64_t session);
int64_t freak_lb_optimize(int64_t session, int64_t level);  /* default<O0..O3> */
int64_t freak_lb_emit(int64_t session, int64_t format, const char* path, size_t path_len);

#endif
