/* In-process LLVM for V4 (B2 bridge). Contract: freak_llvm_bridge.h. */
#include "freak_llvm_bridge.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <llvm-c/Analysis.h>
#include <llvm-c/Core.h>
#include <llvm-c/Error.h>
#include <llvm-c/ErrorHandling.h>
#include <llvm-c/Target.h>
#include <llvm-c/TargetMachine.h>
#include <llvm-c/Transforms/PassBuilder.h>

#ifndef FREAK_LB_LLVM_MAJOR
#define FREAK_LB_LLVM_MAJOR 0
#endif

/* Ticket layout: bit 62..56 kind, 55..48 session slot, 47..24 session
   generation (24 bits), 23..0 index + 1. */
enum { K_TYPE = 1, K_VALUE, K_FUNCTION, K_BLOCK };

typedef struct {
    int kind;
    union { LLVMTypeRef type; LLVMValueRef value; LLVMBasicBlockRef block; } ref;
    LLVMTypeRef fn_type;      /* K_FUNCTION: its function type */
    LLVMValueRef owner;       /* K_BLOCK: its function */
} lb_slot;

typedef struct {
    int live;
    uint32_t generation;
    LLVMContextRef context;
    LLVMModuleRef module;
    LLVMBuilderRef builder;
    LLVMTargetMachineRef machine;
    LLVMTargetDataRef layout;
    int64_t opt;
    lb_slot* slots;
    size_t count, capacity;
    char error[4096];
    /* Open multi-step builds. */
    LLVMTypeRef* members; size_t member_count, member_capacity;
    LLVMTypeRef open_struct; int struct_open;
    LLVMTypeRef fn_return; int fn_open;
    LLVMTypeRef call_type; LLVMValueRef call_callee; int call_open;
    LLVMValueRef* args; size_t arg_count, arg_capacity;
    int has_block;
} lb_session;

static lb_session sessions[FREAK_LB_MAX_SESSIONS];
static uint32_t next_generation = 1;
static char global_error[4096];
static int initialised;

static void lb_fatal(const char* reason) {
    fprintf(stderr, "freak llvm bridge: LLVM fatal error: %s\n", reason);
    fflush(stderr);
}

static void lb_init(void) {
    if (initialised) return;
    initialised = 1;
    /* The release targets only (x86-64 and AArch64), so a tool links just
       those two code generators. */
    LLVMInitializeX86TargetInfo();
    LLVMInitializeX86Target();
    LLVMInitializeX86TargetMC();
    LLVMInitializeX86AsmPrinter();
    LLVMInitializeAArch64TargetInfo();
    LLVMInitializeAArch64Target();
    LLVMInitializeAArch64TargetMC();
    LLVMInitializeAArch64AsmPrinter();
    LLVMInstallFatalErrorHandler(lb_fatal);
}

static int64_t fail(lb_session* s, int64_t code, const char* message, const char* detail) {
    char* out = s ? s->error : global_error;
    snprintf(out, sizeof s->error, "%s%s%s", message, detail ? ": " : "", detail ? detail : "");
    return code;
}

static lb_session* session_of(int64_t ticket) {
    if (ticket <= 0) return NULL;
    uint64_t t = (uint64_t)ticket;
    size_t slot = (size_t)((t >> 48) & 0xff);
    uint32_t generation = (uint32_t)((t >> 24) & 0xffffff);
    if (slot >= FREAK_LB_MAX_SESSIONS) return NULL;
    lb_session* s = &sessions[slot];
    if (!s->live || s->generation != generation) return NULL;
    return s;
}

/* Sessions are tickets of kind 0 with index 0. */
static int64_t session_ticket(size_t slot, uint32_t generation) {
    return (int64_t)(((uint64_t)slot << 48) | ((uint64_t)generation << 24));
}

static int64_t add_slot(lb_session* s, lb_slot slot) {
    if (s->count >= FREAK_LB_MAX_TICKETS - 1) return fail(s, FREAK_LB_E_LIMIT, "ticket limit reached", NULL);
    if (s->count == s->capacity) {
        size_t capacity = s->capacity ? s->capacity * 2 : 256;
        lb_slot* grown = realloc(s->slots, capacity * sizeof *grown);
        if (!grown) return fail(s, FREAK_LB_E_MEMORY, "out of memory for tickets", NULL);
        s->slots = grown;
        s->capacity = capacity;
    }
    s->slots[s->count++] = slot;
    size_t index = (size_t)(s - sessions);
    return (int64_t)(((uint64_t)slot.kind << 56) | ((uint64_t)index << 48) |
                     ((uint64_t)s->generation << 24) | (uint64_t)s->count);
}

static lb_slot* get_slot(lb_session* s, int64_t ticket, int kind, int64_t* error) {
    uint64_t t = (uint64_t)ticket;
    if (ticket <= 0 || session_of(ticket) != s) { *error = fail(s, FREAK_LB_E_TICKET, "ticket is not from this session", NULL); return NULL; }
    size_t index = (size_t)(t & 0xffffff);
    int ticket_kind = (int)((t >> 56) & 0x7f);
    if (index == 0 || index > s->count) { *error = fail(s, FREAK_LB_E_TICKET, "unknown ticket", NULL); return NULL; }
    lb_slot* slot = &s->slots[index - 1];
    if (slot->kind != ticket_kind) { *error = fail(s, FREAK_LB_E_TICKET, "corrupt ticket", NULL); return NULL; }
    if (kind && slot->kind != kind && !(kind == K_VALUE && slot->kind == K_FUNCTION)) {
        *error = fail(s, FREAK_LB_E_KIND, "ticket has the wrong kind", NULL);
        return NULL;
    }
    return slot;
}

#define SESSION(sv) lb_session* s = session_of(sv); \
    if (!s || (((uint64_t)(sv)) & 0xffffff) != 0 || (((uint64_t)(sv)) >> 56) != 0) \
        return fail(NULL, FREAK_LB_E_SESSION, "unknown or released session", NULL)
#define TYPE(var, ticket) LLVMTypeRef var; { int64_t e_ = 0; lb_slot* sl_ = get_slot(s, ticket, K_TYPE, &e_); if (!sl_) return e_; var = sl_->ref.type; }
#define VALUE(var, ticket) LLVMValueRef var; { int64_t e_ = 0; lb_slot* sl_ = get_slot(s, ticket, K_VALUE, &e_); if (!sl_) return e_; var = sl_->ref.value; }
#define BLOCK(var, ticket) LLVMBasicBlockRef var; { int64_t e_ = 0; lb_slot* sl_ = get_slot(s, ticket, K_BLOCK, &e_); if (!sl_) return e_; var = sl_->ref.block; }
#define NEED_BLOCK() if (!s->has_block) return fail(s, FREAK_LB_E_STATE, "no insertion block; call freak_lb_position first", NULL)

static int64_t type_ticket(lb_session* s, LLVMTypeRef type) {
    lb_slot slot = { .kind = K_TYPE }; slot.ref.type = type;
    return add_slot(s, slot);
}

static int64_t value_ticket(lb_session* s, LLVMValueRef value) {
    if (!value) return fail(s, FREAK_LB_E_ARGUMENT, "LLVM produced no value", NULL);
    lb_slot slot = { .kind = K_VALUE }; slot.ref.value = value;
    return add_slot(s, slot);
}

static char* copy_name(const char* bytes, size_t length) {
    char* out = malloc(length + 1);
    if (!out) return NULL;
    if (length) memcpy(out, bytes, length);
    out[length] = 0;
    return out;
}

static LLVMTypeKind kind_of(LLVMValueRef v) { return LLVMGetTypeKind(LLVMTypeOf(v)); }
static int is_int(LLVMValueRef v) { return kind_of(v) == LLVMIntegerTypeKind; }
static int is_float(LLVMValueRef v) { LLVMTypeKind k = kind_of(v); return k == LLVMDoubleTypeKind || k == LLVMFloatTypeKind; }
static int is_ptr(LLVMValueRef v) { return kind_of(v) == LLVMPointerTypeKind; }
static int sized(LLVMTypeRef t) { return LLVMGetTypeKind(t) != LLVMVoidTypeKind && LLVMGetTypeKind(t) != LLVMFunctionTypeKind && LLVMTypeIsSized(t); }

static int64_t grow(lb_session* s, void** items, size_t* capacity, size_t count, size_t size) {
    if (count < *capacity) return 0;
    size_t next = *capacity ? *capacity * 2 : 16;
    void* grown = realloc(*items, next * size);
    if (!grown) return fail(s, FREAK_LB_E_MEMORY, "out of memory", NULL);
    *items = grown;
    *capacity = next;
    return 0;
}

/* ---- sessions ------------------------------------------------------- */

int64_t freak_lb_llvm_major(void) {
    unsigned major = 0, minor = 0, patch = 0;
    LLVMGetVersion(&major, &minor, &patch);
    return (int64_t)major;
}

int64_t freak_lb_session_new(const char* triple, size_t triple_len, const char* name, size_t name_len, int64_t opt) {
    lb_init();
    if (opt < 0 || opt > 3) return fail(NULL, FREAK_LB_E_ARGUMENT, "optimisation level must be 0 to 3", NULL);
    size_t slot = 0;
    while (slot < FREAK_LB_MAX_SESSIONS && sessions[slot].live) slot++;
    if (slot == FREAK_LB_MAX_SESSIONS) return fail(NULL, FREAK_LB_E_LIMIT, "session limit reached", NULL);
    char* triple_z = copy_name(triple, triple_len);
    char* name_z = copy_name(name, name_len);
    if (!triple_z || !name_z) { free(triple_z); free(name_z); return fail(NULL, FREAK_LB_E_MEMORY, "out of memory", NULL); }
    LLVMTargetRef target = NULL;
    char* message = NULL;
    if (LLVMGetTargetFromTriple(triple_z, &target, &message)) {
        int64_t code = fail(NULL, FREAK_LB_E_TARGET, "unknown target triple", message);
        LLVMDisposeMessage(message);
        free(triple_z); free(name_z);
        return code;
    }
    static const LLVMCodeGenOptLevel levels[] = { LLVMCodeGenLevelNone, LLVMCodeGenLevelLess, LLVMCodeGenLevelDefault, LLVMCodeGenLevelAggressive };
    LLVMTargetMachineRef machine = LLVMCreateTargetMachine(target, triple_z, "generic", "", levels[opt], LLVMRelocPIC, LLVMCodeModelDefault);
    if (!machine) { free(triple_z); free(name_z); return fail(NULL, FREAK_LB_E_TARGET, "no target machine for triple", NULL); }
    lb_session* s = &sessions[slot];
    memset(s, 0, sizeof *s);
    s->generation = next_generation;
    next_generation = (next_generation % 0xffffff) + 1;
    s->context = LLVMContextCreate();
    s->module = LLVMModuleCreateWithNameInContext(name_z, s->context);
    s->builder = LLVMCreateBuilderInContext(s->context);
    s->machine = machine;
    s->layout = LLVMCreateTargetDataLayout(machine);
    s->opt = opt;
    LLVMSetTarget(s->module, triple_z);
    LLVMSetModuleDataLayout(s->module, s->layout);
    s->live = 1;
    free(triple_z); free(name_z);
    return session_ticket(slot, s->generation);
}

int64_t freak_lb_session_release(int64_t session) {
    SESSION(session);
    LLVMDisposeBuilder(s->builder);
    LLVMDisposeModule(s->module);
    LLVMDisposeTargetData(s->layout);
    LLVMDisposeTargetMachine(s->machine);
    LLVMContextDispose(s->context);
    free(s->slots); free(s->members); free(s->args);
    uint32_t generation = s->generation;
    memset(s, 0, sizeof *s);
    s->generation = generation;  /* keeps released tickets distinct from a reused slot */
    return 0;
}

int64_t freak_lb_live_sessions(void) {
    int64_t n = 0;
    for (size_t i = 0; i < FREAK_LB_MAX_SESSIONS; i++) n += sessions[i].live;
    return n;
}

int64_t freak_lb_live_tickets(int64_t session) {
    SESSION(session);
    return (int64_t)s->count;
}

const char* freak_lb_error_text(int64_t session, size_t* length) {
    lb_session* s = session_of(session);
    const char* text = s ? s->error : global_error;
    if (length) *length = strlen(text);
    return text;
}

/* ---- types ---------------------------------------------------------- */

int64_t freak_lb_type_int(int64_t session, int64_t bits) {
    SESSION(session);
    if (bits < 1 || bits > 128) return fail(s, FREAK_LB_E_ARGUMENT, "integer width must be 1 to 128 bits", NULL);
    return type_ticket(s, LLVMIntTypeInContext(s->context, (unsigned)bits));
}

int64_t freak_lb_type_double(int64_t session) { SESSION(session); return type_ticket(s, LLVMDoubleTypeInContext(s->context)); }
int64_t freak_lb_type_float(int64_t session) { SESSION(session); return type_ticket(s, LLVMFloatTypeInContext(s->context)); }
int64_t freak_lb_type_ptr(int64_t session) { SESSION(session); return type_ticket(s, LLVMPointerTypeInContext(s->context, 0)); }
int64_t freak_lb_type_void(int64_t session) { SESSION(session); return type_ticket(s, LLVMVoidTypeInContext(s->context)); }

int64_t freak_lb_type_array(int64_t session, int64_t element, int64_t count) {
    SESSION(session);
    TYPE(type, element);
    if (count < 0) return fail(s, FREAK_LB_E_ARGUMENT, "array length is negative", NULL);
    if (!sized(type)) return fail(s, FREAK_LB_E_KIND, "array element type has no size", NULL);
    return type_ticket(s, LLVMArrayType2(type, (uint64_t)count));
}

int64_t freak_lb_struct_begin(int64_t session, const char* name, size_t name_len) {
    SESSION(session);
    if (s->struct_open || s->fn_open) return fail(s, FREAK_LB_E_STATE, "a struct or function type is already open", NULL);
    s->open_struct = NULL;
    if (name_len) {
        char* name_z = copy_name(name, name_len);
        if (!name_z) return fail(s, FREAK_LB_E_MEMORY, "out of memory", NULL);
        LLVMTypeRef existing = LLVMGetTypeByName2(s->context, name_z);
        if (existing) { free(name_z); return fail(s, FREAK_LB_E_ARGUMENT, "named struct already exists", NULL); }
        s->open_struct = LLVMStructCreateNamed(s->context, name_z);
        free(name_z);
    }
    s->member_count = 0;
    s->struct_open = 1;
    return 0;
}

static int64_t add_member(lb_session* s, LLVMTypeRef type) {
    int64_t e = grow(s, (void**)&s->members, &s->member_capacity, s->member_count, sizeof *s->members);
    if (e) return e;
    s->members[s->member_count++] = type;
    return 0;
}

int64_t freak_lb_struct_field(int64_t session, int64_t type) {
    SESSION(session);
    TYPE(t, type);
    if (!s->struct_open) return fail(s, FREAK_LB_E_STATE, "no struct type is open", NULL);
    if (!sized(t)) return fail(s, FREAK_LB_E_KIND, "struct field type has no size", NULL);
    return add_member(s, t);
}

int64_t freak_lb_struct_end(int64_t session, int64_t packed) {
    SESSION(session);
    if (!s->struct_open) return fail(s, FREAK_LB_E_STATE, "no struct type is open", NULL);
    s->struct_open = 0;
    LLVMTypeRef type = s->open_struct;
    if (type) LLVMStructSetBody(type, s->members, (unsigned)s->member_count, packed != 0);
    else type = LLVMStructTypeInContext(s->context, s->members, (unsigned)s->member_count, packed != 0);
    return type_ticket(s, type);
}

int64_t freak_lb_fn_type_begin(int64_t session, int64_t return_type) {
    SESSION(session);
    TYPE(t, return_type);
    if (s->struct_open || s->fn_open) return fail(s, FREAK_LB_E_STATE, "a struct or function type is already open", NULL);
    if (LLVMGetTypeKind(t) == LLVMFunctionTypeKind) return fail(s, FREAK_LB_E_KIND, "a function cannot return a function type", NULL);
    s->fn_return = t;
    s->member_count = 0;
    s->fn_open = 1;
    return 0;
}

int64_t freak_lb_fn_type_param(int64_t session, int64_t type) {
    SESSION(session);
    TYPE(t, type);
    if (!s->fn_open) return fail(s, FREAK_LB_E_STATE, "no function type is open", NULL);
    if (!sized(t)) return fail(s, FREAK_LB_E_KIND, "parameter type has no size", NULL);
    return add_member(s, t);
}

int64_t freak_lb_fn_type_end(int64_t session, int64_t variadic) {
    SESSION(session);
    if (!s->fn_open) return fail(s, FREAK_LB_E_STATE, "no function type is open", NULL);
    s->fn_open = 0;
    return type_ticket(s, LLVMFunctionType(s->fn_return, s->members, (unsigned)s->member_count, variadic != 0));
}

int64_t freak_lb_type_size(int64_t session, int64_t type) {
    SESSION(session);
    TYPE(t, type);
    if (!sized(t)) return fail(s, FREAK_LB_E_KIND, "type has no size", NULL);
    return (int64_t)LLVMABISizeOfType(s->layout, t);
}

int64_t freak_lb_type_align(int64_t session, int64_t type) {
    SESSION(session);
    TYPE(t, type);
    if (!sized(t)) return fail(s, FREAK_LB_E_KIND, "type has no size", NULL);
    return (int64_t)LLVMABIAlignmentOfType(s->layout, t);
}

int64_t freak_lb_field_offset(int64_t session, int64_t struct_type, int64_t field) {
    SESSION(session);
    TYPE(t, struct_type);
    if (LLVMGetTypeKind(t) != LLVMStructTypeKind || LLVMIsOpaqueStruct(t)) return fail(s, FREAK_LB_E_KIND, "not a struct with a body", NULL);
    if (field < 0 || field >= (int64_t)LLVMCountStructElementTypes(t)) return fail(s, FREAK_LB_E_ARGUMENT, "no such field", NULL);
    return (int64_t)LLVMOffsetOfElement(s->layout, t, (unsigned)field);
}

/* ---- functions, globals, blocks -------------------------------------- */

static LLVMLinkage linkage_of(int64_t linkage, int* ok) {
    *ok = 1;
    switch (linkage) {
    case FREAK_LB_EXTERNAL: return LLVMExternalLinkage;
    case FREAK_LB_INTERNAL: return LLVMInternalLinkage;
    case FREAK_LB_PRIVATE: return LLVMPrivateLinkage;
    default: *ok = 0; return LLVMExternalLinkage;
    }
}

int64_t freak_lb_function(int64_t session, const char* name, size_t name_len, int64_t fn_type, int64_t linkage) {
    SESSION(session);
    TYPE(t, fn_type);
    int ok;
    LLVMLinkage l = linkage_of(linkage, &ok);
    if (!ok) return fail(s, FREAK_LB_E_ARGUMENT, "unknown linkage", NULL);
    if (LLVMGetTypeKind(t) != LLVMFunctionTypeKind) return fail(s, FREAK_LB_E_KIND, "not a function type", NULL);
    if (name_len == 0 || memchr(name, 0, name_len)) return fail(s, FREAK_LB_E_ARGUMENT, "function name is empty or holds a NUL byte", NULL);
    char* name_z = copy_name(name, name_len);
    if (!name_z) return fail(s, FREAK_LB_E_MEMORY, "out of memory", NULL);
    if (LLVMGetNamedFunction(s->module, name_z) || LLVMGetNamedGlobal(s->module, name_z)) {
        int64_t code = fail(s, FREAK_LB_E_ARGUMENT, "symbol already defined", name_z);
        free(name_z);
        return code;
    }
    LLVMValueRef fn = LLVMAddFunction(s->module, name_z, t);
    free(name_z);
    LLVMSetLinkage(fn, l);
    lb_slot slot = { .kind = K_FUNCTION, .fn_type = t }; slot.ref.value = fn;
    return add_slot(s, slot);
}

int64_t freak_lb_param(int64_t session, int64_t function, int64_t index) {
    SESSION(session);
    int64_t e = 0;
    lb_slot* f = get_slot(s, function, K_FUNCTION, &e);
    if (!f) return e;
    if (f->kind != K_FUNCTION) return fail(s, FREAK_LB_E_KIND, "not a function", NULL);
    if (index < 0 || index >= (int64_t)LLVMCountParams(f->ref.value)) return fail(s, FREAK_LB_E_ARGUMENT, "no such parameter", NULL);
    return value_ticket(s, LLVMGetParam(f->ref.value, (unsigned)index));
}

int64_t freak_lb_global_bytes(int64_t session, const char* name, size_t name_len, const char* bytes, size_t length, int64_t linkage) {
    SESSION(session);
    int ok;
    LLVMLinkage l = linkage_of(linkage, &ok);
    if (!ok) return fail(s, FREAK_LB_E_ARGUMENT, "unknown linkage", NULL);
    if (name_len == 0 || memchr(name, 0, name_len)) return fail(s, FREAK_LB_E_ARGUMENT, "global name is empty or holds a NUL byte", NULL);
    char* name_z = copy_name(name, name_len);
    if (!name_z) return fail(s, FREAK_LB_E_MEMORY, "out of memory", NULL);
    if (LLVMGetNamedFunction(s->module, name_z) || LLVMGetNamedGlobal(s->module, name_z)) {
        int64_t code = fail(s, FREAK_LB_E_ARGUMENT, "symbol already defined", name_z);
        free(name_z);
        return code;
    }
    LLVMValueRef init = LLVMConstStringInContext2(s->context, bytes, length, 1);
    LLVMValueRef global = LLVMAddGlobal(s->module, LLVMTypeOf(init), name_z);
    free(name_z);
    LLVMSetInitializer(global, init);
    LLVMSetGlobalConstant(global, 1);
    LLVMSetLinkage(global, l);
    if (l == LLVMPrivateLinkage) LLVMSetUnnamedAddress(global, LLVMGlobalUnnamedAddr);
    return value_ticket(s, global);
}

int64_t freak_lb_block(int64_t session, int64_t function, const char* name, size_t name_len) {
    SESSION(session);
    int64_t e = 0;
    lb_slot* f = get_slot(s, function, K_FUNCTION, &e);
    if (!f) return e;
    if (f->kind != K_FUNCTION) return fail(s, FREAK_LB_E_KIND, "not a function", NULL);
    char* name_z = copy_name(name, name_len);
    if (!name_z) return fail(s, FREAK_LB_E_MEMORY, "out of memory", NULL);
    LLVMBasicBlockRef block = LLVMAppendBasicBlockInContext(s->context, f->ref.value, name_z);
    free(name_z);
    lb_slot slot = { .kind = K_BLOCK, .owner = f->ref.value }; slot.ref.block = block;
    return add_slot(s, slot);
}

int64_t freak_lb_position(int64_t session, int64_t block) {
    SESSION(session);
    BLOCK(b, block);
    LLVMPositionBuilderAtEnd(s->builder, b);
    s->has_block = 1;
    return 0;
}

int64_t freak_lb_current_block(int64_t session) {
    SESSION(session);
    NEED_BLOCK();
    LLVMBasicBlockRef b = LLVMGetInsertBlock(s->builder);
    for (size_t i = 0; i < s->count; i++)
        if (s->slots[i].kind == K_BLOCK && s->slots[i].ref.block == b) {
            size_t index = (size_t)(s - sessions);
            return (int64_t)(((uint64_t)K_BLOCK << 56) | ((uint64_t)index << 48) | ((uint64_t)s->generation << 24) | (uint64_t)(i + 1));
        }
    return fail(s, FREAK_LB_E_STATE, "insertion block has no ticket", NULL);
}

int64_t freak_lb_block_terminated(int64_t session, int64_t block) {
    SESSION(session);
    BLOCK(b, block);
    return LLVMGetBasicBlockTerminator(b) != NULL;
}

/* ---- constants ------------------------------------------------------ */

int64_t freak_lb_const_int(int64_t session, int64_t type, int64_t value) {
    SESSION(session);
    TYPE(t, type);
    if (LLVMGetTypeKind(t) != LLVMIntegerTypeKind) return fail(s, FREAK_LB_E_KIND, "not an integer type", NULL);
    return value_ticket(s, LLVMConstInt(t, (unsigned long long)value, 1));
}

int64_t freak_lb_const_double_bits(int64_t session, int64_t type, int64_t bits) {
    SESSION(session);
    TYPE(t, type);
    double d;
    memcpy(&d, &bits, sizeof d);
    LLVMTypeKind k = LLVMGetTypeKind(t);
    if (k != LLVMDoubleTypeKind && k != LLVMFloatTypeKind) return fail(s, FREAK_LB_E_KIND, "not a float type", NULL);
    return value_ticket(s, LLVMConstReal(t, d));
}

int64_t freak_lb_const_null(int64_t session, int64_t type) {
    SESSION(session);
    TYPE(t, type);
    if (LLVMGetTypeKind(t) != LLVMPointerTypeKind) return fail(s, FREAK_LB_E_KIND, "not a pointer type", NULL);
    return value_ticket(s, LLVMConstPointerNull(t));
}

int64_t freak_lb_const_zero(int64_t session, int64_t type) {
    SESSION(session);
    TYPE(t, type);
    if (!sized(t)) return fail(s, FREAK_LB_E_KIND, "type has no size", NULL);
    return value_ticket(s, LLVMConstNull(t));
}

int64_t freak_lb_type_of(int64_t session, int64_t value) {
    SESSION(session);
    VALUE(v, value);
    return type_ticket(s, LLVMTypeOf(v));
}

/* ---- instructions ---------------------------------------------------- */

int64_t freak_lb_alloca(int64_t session, int64_t type) {
    SESSION(session);
    TYPE(t, type);
    NEED_BLOCK();
    if (!sized(t)) return fail(s, FREAK_LB_E_KIND, "alloca type has no size", NULL);
    /* Entry-block allocas keep mem2reg effective at every level. */
    LLVMBasicBlockRef current = LLVMGetInsertBlock(s->builder);
    LLVMBasicBlockRef entry = LLVMGetEntryBasicBlock(LLVMGetBasicBlockParent(current));
    LLVMBuilderRef b = LLVMCreateBuilderInContext(s->context);
    LLVMValueRef first = LLVMGetFirstInstruction(entry);
    if (first) LLVMPositionBuilderBefore(b, first); else LLVMPositionBuilderAtEnd(b, entry);
    LLVMValueRef slot = LLVMBuildAlloca(b, t, "");
    LLVMDisposeBuilder(b);
    return value_ticket(s, slot);
}

int64_t freak_lb_load(int64_t session, int64_t type, int64_t pointer) {
    SESSION(session);
    TYPE(t, type);
    VALUE(p, pointer);
    NEED_BLOCK();
    if (!is_ptr(p)) return fail(s, FREAK_LB_E_KIND, "load needs a pointer", NULL);
    if (!sized(t)) return fail(s, FREAK_LB_E_KIND, "load type has no size", NULL);
    return value_ticket(s, LLVMBuildLoad2(s->builder, t, p, ""));
}

int64_t freak_lb_store(int64_t session, int64_t value, int64_t pointer) {
    SESSION(session);
    VALUE(v, value);
    VALUE(p, pointer);
    NEED_BLOCK();
    if (!is_ptr(p)) return fail(s, FREAK_LB_E_KIND, "store needs a pointer", NULL);
    if (!sized(LLVMTypeOf(v))) return fail(s, FREAK_LB_E_KIND, "stored value has no size", NULL);
    LLVMBuildStore(s->builder, v, p);
    return 0;
}

int64_t freak_lb_binary(int64_t session, int64_t op, int64_t left, int64_t right) {
    SESSION(session);
    VALUE(l, left);
    VALUE(r, right);
    NEED_BLOCK();
    if (LLVMTypeOf(l) != LLVMTypeOf(r)) return fail(s, FREAK_LB_E_KIND, "binary operands have different types", NULL);
    int floating = op >= FREAK_LB_FADD;
    if (op < FREAK_LB_ADD || op > FREAK_LB_FREM) return fail(s, FREAK_LB_E_ARGUMENT, "unknown binary operation", NULL);
    if (floating ? !is_float(l) : !is_int(l)) return fail(s, FREAK_LB_E_KIND, floating ? "float operation on non-float operands" : "integer operation on non-integer operands", NULL);
    static const LLVMOpcode codes[] = { 0, LLVMAdd, LLVMSub, LLVMMul, LLVMSDiv, LLVMUDiv, LLVMSRem, LLVMURem,
        LLVMAnd, LLVMOr, LLVMXor, LLVMShl, LLVMLShr, LLVMAShr, LLVMFAdd, LLVMFSub, LLVMFMul, LLVMFDiv, LLVMFRem };
    return value_ticket(s, LLVMBuildBinOp(s->builder, codes[op], l, r, ""));
}

int64_t freak_lb_neg(int64_t session, int64_t value) {
    SESSION(session);
    VALUE(v, value);
    NEED_BLOCK();
    if (is_int(v)) return value_ticket(s, LLVMBuildNeg(s->builder, v, ""));
    if (is_float(v)) return value_ticket(s, LLVMBuildFNeg(s->builder, v, ""));
    return fail(s, FREAK_LB_E_KIND, "negation needs a number", NULL);
}

int64_t freak_lb_icmp(int64_t session, int64_t predicate, int64_t left, int64_t right) {
    SESSION(session);
    VALUE(l, left);
    VALUE(r, right);
    NEED_BLOCK();
    if (predicate < FREAK_LB_EQ || predicate > FREAK_LB_SLE) return fail(s, FREAK_LB_E_ARGUMENT, "unknown integer predicate", NULL);
    if (LLVMTypeOf(l) != LLVMTypeOf(r) || !(is_int(l) || is_ptr(l))) return fail(s, FREAK_LB_E_KIND, "icmp needs two integers or two pointers of one type", NULL);
    static const LLVMIntPredicate preds[] = { 0, LLVMIntEQ, LLVMIntNE, LLVMIntUGT, LLVMIntUGE, LLVMIntULT, LLVMIntULE, LLVMIntSGT, LLVMIntSGE, LLVMIntSLT, LLVMIntSLE };
    return value_ticket(s, LLVMBuildICmp(s->builder, preds[predicate], l, r, ""));
}

int64_t freak_lb_fcmp(int64_t session, int64_t predicate, int64_t left, int64_t right) {
    SESSION(session);
    VALUE(l, left);
    VALUE(r, right);
    NEED_BLOCK();
    if (predicate < FREAK_LB_FOEQ || predicate > FREAK_LB_FUNE) return fail(s, FREAK_LB_E_ARGUMENT, "unknown float predicate", NULL);
    if (LLVMTypeOf(l) != LLVMTypeOf(r) || !is_float(l)) return fail(s, FREAK_LB_E_KIND, "fcmp needs two floats of one type", NULL);
    static const LLVMRealPredicate preds[] = { 0, LLVMRealOEQ, LLVMRealONE, LLVMRealOGT, LLVMRealOGE, LLVMRealOLT, LLVMRealOLE, LLVMRealUNE };
    return value_ticket(s, LLVMBuildFCmp(s->builder, preds[predicate], l, r, ""));
}

/* LLVM's C API has no cast check, so the scalar rules are spelled out. */
static unsigned float_bits(LLVMTypeRef t) {
    LLVMTypeKind k = LLVMGetTypeKind(t);
    return k == LLVMDoubleTypeKind ? 64 : k == LLVMFloatTypeKind ? 32 : 0;
}

static int cast_valid(int64_t op, LLVMTypeRef from, LLVMTypeRef to) {
    int from_int = LLVMGetTypeKind(from) == LLVMIntegerTypeKind, to_int = LLVMGetTypeKind(to) == LLVMIntegerTypeKind;
    int from_ptr = LLVMGetTypeKind(from) == LLVMPointerTypeKind, to_ptr = LLVMGetTypeKind(to) == LLVMPointerTypeKind;
    unsigned from_fp = float_bits(from), to_fp = float_bits(to);
    unsigned from_w = from_int ? LLVMGetIntTypeWidth(from) : from_fp, to_w = to_int ? LLVMGetIntTypeWidth(to) : to_fp;
    switch (op) {
    case FREAK_LB_TRUNC: return from_int && to_int && from_w > to_w;
    case FREAK_LB_ZEXT: case FREAK_LB_SEXT: return from_int && to_int && from_w < to_w;
    case FREAK_LB_FPTOSI: case FREAK_LB_FPTOUI: return from_fp && to_int;
    case FREAK_LB_SITOFP: case FREAK_LB_UITOFP: return from_int && to_fp;
    case FREAK_LB_FPTRUNC: return from_fp && to_fp && from_fp > to_fp;
    case FREAK_LB_FPEXT: return from_fp && to_fp && from_fp < to_fp;
    case FREAK_LB_PTRTOINT: return from_ptr && to_int;
    case FREAK_LB_INTTOPTR: return from_int && to_ptr;
    case FREAK_LB_BITCAST: return (from_int || from_fp) && (to_int || to_fp) && from_w == to_w;
    default: return 0;
    }
}

int64_t freak_lb_cast(int64_t session, int64_t op, int64_t value, int64_t type) {
    SESSION(session);
    VALUE(v, value);
    TYPE(t, type);
    NEED_BLOCK();
    if (op < FREAK_LB_TRUNC || op > FREAK_LB_BITCAST) return fail(s, FREAK_LB_E_ARGUMENT, "unknown cast", NULL);
    static const LLVMOpcode codes[] = { 0, LLVMTrunc, LLVMZExt, LLVMSExt, LLVMFPToSI, LLVMFPToUI, LLVMSIToFP,
        LLVMUIToFP, LLVMFPTrunc, LLVMFPExt, LLVMPtrToInt, LLVMIntToPtr, LLVMBitCast };
    if (!cast_valid(op, LLVMTypeOf(v), t)) return fail(s, FREAK_LB_E_KIND, "cast is not valid for these types", NULL);
    return value_ticket(s, LLVMBuildCast(s->builder, codes[op], v, t, ""));
}

int64_t freak_lb_select(int64_t session, int64_t condition, int64_t yes, int64_t no) {
    SESSION(session);
    VALUE(c, condition);
    VALUE(a, yes);
    VALUE(b, no);
    NEED_BLOCK();
    if (LLVMTypeOf(c) != LLVMInt1TypeInContext(s->context)) return fail(s, FREAK_LB_E_KIND, "select condition must be i1", NULL);
    if (LLVMTypeOf(a) != LLVMTypeOf(b)) return fail(s, FREAK_LB_E_KIND, "select arms have different types", NULL);
    return value_ticket(s, LLVMBuildSelect(s->builder, c, a, b, ""));
}

int64_t freak_lb_field_ptr(int64_t session, int64_t struct_type, int64_t pointer, int64_t field) {
    SESSION(session);
    TYPE(t, struct_type);
    VALUE(p, pointer);
    NEED_BLOCK();
    if (LLVMGetTypeKind(t) != LLVMStructTypeKind || LLVMIsOpaqueStruct(t)) return fail(s, FREAK_LB_E_KIND, "not a struct with a body", NULL);
    if (!is_ptr(p)) return fail(s, FREAK_LB_E_KIND, "field address needs a pointer", NULL);
    if (field < 0 || field >= (int64_t)LLVMCountStructElementTypes(t)) return fail(s, FREAK_LB_E_ARGUMENT, "no such field", NULL);
    return value_ticket(s, LLVMBuildStructGEP2(s->builder, t, p, (unsigned)field, ""));
}

int64_t freak_lb_element_ptr(int64_t session, int64_t element_type, int64_t pointer, int64_t index) {
    SESSION(session);
    TYPE(t, element_type);
    VALUE(p, pointer);
    VALUE(i, index);
    NEED_BLOCK();
    if (!sized(t)) return fail(s, FREAK_LB_E_KIND, "element type has no size", NULL);
    if (!is_ptr(p) || !is_int(i)) return fail(s, FREAK_LB_E_KIND, "element address needs a pointer and an integer index", NULL);
    return value_ticket(s, LLVMBuildInBoundsGEP2(s->builder, t, p, &i, 1, ""));
}

static int aggregate(LLVMValueRef v, int64_t index) {
    LLVMTypeRef t = LLVMTypeOf(v);
    if (index < 0) return 0;
    if (LLVMGetTypeKind(t) == LLVMStructTypeKind) return !LLVMIsOpaqueStruct(t) && index < (int64_t)LLVMCountStructElementTypes(t);
    if (LLVMGetTypeKind(t) == LLVMArrayTypeKind) return (uint64_t)index < LLVMGetArrayLength2(t);
    return 0;
}

int64_t freak_lb_extract(int64_t session, int64_t aggregate_value, int64_t index) {
    SESSION(session);
    VALUE(a, aggregate_value);
    NEED_BLOCK();
    if (!aggregate(a, index)) return fail(s, FREAK_LB_E_KIND, "extract needs an aggregate and an index inside it", NULL);
    return value_ticket(s, LLVMBuildExtractValue(s->builder, a, (unsigned)index, ""));
}

int64_t freak_lb_insert(int64_t session, int64_t aggregate_value, int64_t value, int64_t index) {
    SESSION(session);
    VALUE(a, aggregate_value);
    VALUE(v, value);
    NEED_BLOCK();
    if (!aggregate(a, index)) return fail(s, FREAK_LB_E_KIND, "insert needs an aggregate and an index inside it", NULL);
    LLVMTypeRef t = LLVMTypeOf(a);
    LLVMTypeRef member = LLVMGetTypeKind(t) == LLVMStructTypeKind ? LLVMStructGetTypeAtIndex(t, (unsigned)index) : LLVMGetElementType(t);
    if (member != LLVMTypeOf(v)) return fail(s, FREAK_LB_E_KIND, "inserted value has the wrong type", NULL);
    return value_ticket(s, LLVMBuildInsertValue(s->builder, a, v, (unsigned)index, ""));
}

int64_t freak_lb_call_begin(int64_t session, int64_t fn_type, int64_t callee) {
    SESSION(session);
    TYPE(t, fn_type);
    VALUE(c, callee);
    NEED_BLOCK();
    if (s->call_open) return fail(s, FREAK_LB_E_STATE, "a call is already open", NULL);
    if (LLVMGetTypeKind(t) != LLVMFunctionTypeKind) return fail(s, FREAK_LB_E_KIND, "not a function type", NULL);
    if (!is_ptr(c)) return fail(s, FREAK_LB_E_KIND, "callee is not a function or pointer", NULL);
    if (LLVMIsAFunction(c) && LLVMGlobalGetValueType(c) != t) return fail(s, FREAK_LB_E_KIND, "callee's type differs from the call's function type", NULL);
    s->call_type = t;
    s->call_callee = c;
    s->arg_count = 0;
    s->call_open = 1;
    return 0;
}

int64_t freak_lb_call_arg(int64_t session, int64_t value) {
    SESSION(session);
    VALUE(v, value);
    if (!s->call_open) return fail(s, FREAK_LB_E_STATE, "no call is open", NULL);
    unsigned fixed = LLVMCountParamTypes(s->call_type);
    if (s->arg_count < fixed) {
        LLVMTypeRef* params = malloc(fixed * sizeof *params);
        if (!params) return fail(s, FREAK_LB_E_MEMORY, "out of memory", NULL);
        LLVMGetParamTypes(s->call_type, params);
        int same = params[s->arg_count] == LLVMTypeOf(v);
        free(params);
        if (!same) return fail(s, FREAK_LB_E_KIND, "argument type differs from the parameter type", NULL);
    } else if (!LLVMIsFunctionVarArg(s->call_type)) {
        return fail(s, FREAK_LB_E_ARGUMENT, "too many arguments", NULL);
    }
    int64_t e = grow(s, (void**)&s->args, &s->arg_capacity, s->arg_count, sizeof *s->args);
    if (e) return e;
    s->args[s->arg_count++] = v;
    return 0;
}

int64_t freak_lb_call_end(int64_t session) {
    SESSION(session);
    if (!s->call_open) return fail(s, FREAK_LB_E_STATE, "no call is open", NULL);
    s->call_open = 0;
    if (s->arg_count < LLVMCountParamTypes(s->call_type)) return fail(s, FREAK_LB_E_ARGUMENT, "too few arguments", NULL);
    LLVMValueRef call = LLVMBuildCall2(s->builder, s->call_type, s->call_callee, s->args, (unsigned)s->arg_count, "");
    /* A void call still gets a ticket so callers can add call attributes later. */
    return value_ticket(s, call);
}

int64_t freak_lb_phi(int64_t session, int64_t type) {
    SESSION(session);
    TYPE(t, type);
    NEED_BLOCK();
    if (!sized(t)) return fail(s, FREAK_LB_E_KIND, "phi type has no size", NULL);
    return value_ticket(s, LLVMBuildPhi(s->builder, t, ""));
}

int64_t freak_lb_phi_incoming(int64_t session, int64_t phi, int64_t value, int64_t block) {
    SESSION(session);
    VALUE(p, phi);
    VALUE(v, value);
    BLOCK(b, block);
    if (!LLVMIsAPHINode(p)) return fail(s, FREAK_LB_E_KIND, "not a phi node", NULL);
    if (LLVMTypeOf(p) != LLVMTypeOf(v)) return fail(s, FREAK_LB_E_KIND, "incoming value has the wrong type", NULL);
    LLVMAddIncoming(p, &v, &b, 1);
    return 0;
}

static int64_t terminate(lb_session* s) {
    LLVMBasicBlockRef current = LLVMGetInsertBlock(s->builder);
    if (LLVMGetBasicBlockTerminator(current)) return fail(s, FREAK_LB_E_STATE, "block already has a terminator", NULL);
    return 0;
}

int64_t freak_lb_br(int64_t session, int64_t block) {
    SESSION(session);
    BLOCK(b, block);
    NEED_BLOCK();
    int64_t e = terminate(s); if (e) return e;
    if (LLVMGetBasicBlockParent(b) != LLVMGetBasicBlockParent(LLVMGetInsertBlock(s->builder))) return fail(s, FREAK_LB_E_KIND, "branch target is in another function", NULL);
    LLVMBuildBr(s->builder, b);
    return 0;
}

int64_t freak_lb_cond_br(int64_t session, int64_t condition, int64_t yes, int64_t no) {
    SESSION(session);
    VALUE(c, condition);
    BLOCK(a, yes);
    BLOCK(b, no);
    NEED_BLOCK();
    int64_t e = terminate(s); if (e) return e;
    LLVMValueRef fn = LLVMGetBasicBlockParent(LLVMGetInsertBlock(s->builder));
    if (LLVMGetBasicBlockParent(a) != fn || LLVMGetBasicBlockParent(b) != fn) return fail(s, FREAK_LB_E_KIND, "branch target is in another function", NULL);
    if (LLVMTypeOf(c) != LLVMInt1TypeInContext(s->context)) return fail(s, FREAK_LB_E_KIND, "branch condition must be i1", NULL);
    LLVMBuildCondBr(s->builder, c, a, b);
    return 0;
}

static LLVMTypeRef current_return_type(lb_session* s) {
    LLVMValueRef fn = LLVMGetBasicBlockParent(LLVMGetInsertBlock(s->builder));
    return LLVMGetReturnType(LLVMGlobalGetValueType(fn));
}

int64_t freak_lb_ret(int64_t session, int64_t value) {
    SESSION(session);
    VALUE(v, value);
    NEED_BLOCK();
    int64_t e = terminate(s); if (e) return e;
    if (current_return_type(s) != LLVMTypeOf(v)) return fail(s, FREAK_LB_E_KIND, "returned value has the wrong type", NULL);
    LLVMBuildRet(s->builder, v);
    return 0;
}

int64_t freak_lb_ret_void(int64_t session) {
    SESSION(session);
    NEED_BLOCK();
    int64_t e = terminate(s); if (e) return e;
    if (LLVMGetTypeKind(current_return_type(s)) != LLVMVoidTypeKind) return fail(s, FREAK_LB_E_KIND, "function does not return void", NULL);
    LLVMBuildRetVoid(s->builder);
    return 0;
}

int64_t freak_lb_unreachable(int64_t session) {
    SESSION(session);
    NEED_BLOCK();
    int64_t e = terminate(s); if (e) return e;
    LLVMBuildUnreachable(s->builder);
    return 0;
}

int64_t freak_lb_attribute(int64_t session, int64_t function, int64_t index, const char* name, size_t name_len) {
    SESSION(session);
    int64_t e = 0;
    lb_slot* f = get_slot(s, function, K_FUNCTION, &e);
    if (!f) return e;
    if (f->kind != K_FUNCTION) return fail(s, FREAK_LB_E_KIND, "not a function", NULL);
    if (index < -1 || index > (int64_t)LLVMCountParams(f->ref.value)) return fail(s, FREAK_LB_E_ARGUMENT, "no such attribute position", NULL);
    unsigned kind = LLVMGetEnumAttributeKindForName(name, name_len);
    if (kind == 0) return fail(s, FREAK_LB_E_ARGUMENT, "unknown enum attribute", NULL);
    LLVMAttributeRef attribute = LLVMCreateEnumAttribute(s->context, kind, 0);
    LLVMAttributeIndex position = index == -1 ? LLVMAttributeFunctionIndex : (LLVMAttributeIndex)index;
    LLVMAddAttributeAtIndex(f->ref.value, position, attribute);
    return 0;
}

/* ---- module --------------------------------------------------------- */

int64_t freak_lb_verify(int64_t session) {
    SESSION(session);
    if (s->struct_open || s->fn_open || s->call_open) return fail(s, FREAK_LB_E_STATE, "a type or call is still open", NULL);
    char* message = NULL;
    if (LLVMVerifyModule(s->module, LLVMReturnStatusAction, &message)) {
        int64_t code = fail(s, FREAK_LB_E_VERIFY, "module failed verification", message);
        LLVMDisposeMessage(message);
        return code;
    }
    LLVMDisposeMessage(message);
    return 0;
}

int64_t freak_lb_optimize(int64_t session, int64_t level) {
    SESSION(session);
    if (level < 0 || level > 3) return fail(s, FREAK_LB_E_ARGUMENT, "optimisation level must be 0 to 3", NULL);
    int64_t verified = freak_lb_verify(session);
    if (verified) return verified;
    static const char* pipelines[] = { "default<O0>", "default<O1>", "default<O2>", "default<O3>" };
    LLVMPassBuilderOptionsRef options = LLVMCreatePassBuilderOptions();
    LLVMErrorRef error = LLVMRunPasses(s->module, pipelines[level], s->machine, options);
    LLVMDisposePassBuilderOptions(options);
    if (error) {
        char* message = LLVMGetErrorMessage(error);
        int64_t code = fail(s, FREAK_LB_E_PASSES, "pass pipeline failed", message);
        LLVMDisposeErrorMessage(message);
        return code;
    }
    return freak_lb_verify(session);
}

int64_t freak_lb_emit(int64_t session, int64_t format, const char* path, size_t path_len) {
    SESSION(session);
    if (path_len == 0 || memchr(path, 0, path_len)) return fail(s, FREAK_LB_E_ARGUMENT, "output path is empty or holds a NUL byte", NULL);
    int64_t verified = freak_lb_verify(session);
    if (verified) return verified;
    char* path_z = copy_name(path, path_len);
    if (!path_z) return fail(s, FREAK_LB_E_MEMORY, "out of memory", NULL);
    char* message = NULL;
    int failed;
    if (format == FREAK_LB_IR_TEXT) {
        failed = LLVMPrintModuleToFile(s->module, path_z, &message);
    } else if (format == FREAK_LB_OBJECT || format == FREAK_LB_ASSEMBLY) {
        failed = LLVMTargetMachineEmitToFile(s->machine, s->module, path_z,
                                             format == FREAK_LB_OBJECT ? LLVMObjectFile : LLVMAssemblyFile, &message);
    } else {
        free(path_z);
        return fail(s, FREAK_LB_E_ARGUMENT, "unknown output format", NULL);
    }
    free(path_z);
    if (failed) {
        int64_t code = fail(s, FREAK_LB_E_EMIT, "could not write output", message);
        LLVMDisposeMessage(message);
        return code;
    }
    if (message) LLVMDisposeMessage(message);
    return 0;
}
