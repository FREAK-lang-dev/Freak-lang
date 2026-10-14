/* Experimental LLVM 19 compiler-host bridge. No application links this file. */
#include "bridge.h"
#include <llvm-c/Analysis.h>
#include <llvm-c/Core.h>
#include <llvm-c/Error.h>
#include <llvm-c/Target.h>
#include <llvm-c/TargetMachine.h>
#include <llvm-c/Transforms/PassBuilder.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define IB_MAX_SESSIONS 8
#define IB_MAX_TICKETS 65535
#define IB_MAX_ARGUMENTS 64
#define IB_MAX_TEXT 4096

enum ib_kind { IB_EMPTY, IB_SESSION, IB_FUNCTION, IB_BLOCK, IB_VALUE, IB_SLOT };
struct ib_ticket {
    uint32_t generation;
    enum ib_kind kind;
    int64_t session;
    void *reference;
    LLVMValueRef function;
};
struct ib_session {
    int64_t ticket;
    LLVMContextRef context;
    LLVMModuleRef module;
    LLVMBuilderRef builder;
    LLVMTypeRef integer, boolean;
    int optimization;
    int finished;
    char error[IB_MAX_TEXT];
    LLVMValueRef pending_function;
    LLVMValueRef pending_arguments[IB_MAX_ARGUMENTS];
    unsigned pending_count;
};
static struct ib_ticket ib_tickets[IB_MAX_TICKETS];
static struct ib_session ib_sessions[IB_MAX_SESSIONS];
static char ib_global_error[IB_MAX_TEXT];
static size_t ib_ticket_hint;

static void ib_fail(struct ib_session *s, const char *message) {
    char *destination = s ? s->error : ib_global_error;
    if (!*destination) snprintf(destination, IB_MAX_TEXT, "%s", message);
}
static struct ib_ticket *ib_lookup(int64_t ticket, enum ib_kind kind) {
    if (ticket <= 0) return NULL;
    uint64_t bits = (uint64_t)ticket;
    unsigned slot = (unsigned)(bits & UINT64_C(0xffff));
    uint64_t generation = bits >> 16;
    if (!slot || slot > IB_MAX_TICKETS || !generation || generation > UINT32_MAX)
        return NULL;
    struct ib_ticket *entry = &ib_tickets[slot - 1];
    if (entry->kind != kind || entry->generation != generation) return NULL;
    return entry;
}
static struct ib_session *ib_get(int64_t ticket) {
    struct ib_ticket *entry = ib_lookup(ticket, IB_SESSION);
    if (!entry) { ib_fail(NULL, "invalid or released builder session"); return NULL; }
    struct ib_session *s = entry->reference;
    if (!s || s->ticket != ticket) return NULL;
    return s;
}
static int64_t ib_register(struct ib_session *s, enum ib_kind kind,
                           void *reference, LLVMValueRef function) {
    if (!reference) { ib_fail(s, "LLVM returned a null reference"); return 0; }
    for (size_t offset = 0; offset < IB_MAX_TICKETS; ++offset) {
        size_t index = (ib_ticket_hint + offset) % IB_MAX_TICKETS;
        struct ib_ticket *entry = &ib_tickets[index];
        /* Retire an exhausted generation rather than admitting an old ticket. */
        if (entry->kind != IB_EMPTY || entry->generation == UINT32_MAX) continue;
        ++entry->generation;
        entry->kind = kind;
        entry->session = s ? s->ticket : 0;
        entry->reference = reference;
        entry->function = function;
        ib_ticket_hint = (index + 1) % IB_MAX_TICKETS;
        return (int64_t)(((uint64_t)entry->generation << 16) | (index + 1));
    }
    ib_fail(s, "experimental builder ticket limit reached");
    return 0;
}
static struct ib_ticket *ib_owned(struct ib_session *s, int64_t ticket,
                                 enum ib_kind kind) {
    if (!s || *s->error) return NULL;
    if (s->finished) { ib_fail(s, "builder session is already finalized"); return NULL; }
    struct ib_ticket *entry = ib_lookup(ticket, kind);
    if (!entry || entry->session != s->ticket) {
        ib_fail(s, "wrong-kind, cross-session or released builder ticket");
        return NULL;
    }
    return entry;
}
static LLVMValueRef ib_current_function(struct ib_session *s) {
    if (!s || *s->error) return NULL;
    if (s->finished) { ib_fail(s, "builder session is already finalized"); return NULL; }
    LLVMBasicBlockRef block = LLVMGetInsertBlock(s->builder);
    if (!block || LLVMGetBasicBlockTerminator(block)) {
        ib_fail(s, "builder insertion block is missing or already terminated");
        return NULL;
    }
    return LLVMGetBasicBlockParent(block);
}
static LLVMValueRef ib_operand(struct ib_session *s, int64_t ticket,
                               LLVMTypeRef type, LLVMValueRef function) {
    struct ib_ticket *entry = ib_owned(s, ticket, IB_VALUE);
    if (!entry) return NULL;
    LLVMValueRef value = entry->reference;
    if (LLVMTypeOf(value) != type || (entry->function && entry->function != function)) {
        ib_fail(s, "builder operand type or function does not match");
        return NULL;
    }
    return value;
}
static char *ib_text(struct ib_session *s, freak_word word, int allow_empty) {
    if ((!word.data && word.length) || word.length >= IB_MAX_TEXT ||
        (!allow_empty && !word.length) ||
        (word.length && memchr(word.data, 0, word.length))) {
        ib_fail(s, "builder text is empty, contains NUL or exceeds its bound");
        return NULL;
    }
    char *copy = malloc(word.length + 1);
    if (!copy) { ib_fail(s, "builder text allocation failed"); return NULL; }
    if (word.length) memcpy(copy, word.data, word.length);
    copy[word.length] = 0;
    return copy;
}
static LLVMValueRef ib_runtime(struct ib_session *s, const char *name,
                               unsigned count, int returns_integer) {
    LLVMValueRef function = LLVMGetNamedFunction(s->module, name);
    if (function) return function;
    LLVMTypeRef arguments[IB_MAX_ARGUMENTS];
    for (unsigned i = 0; i < count; ++i) arguments[i] = s->integer;
    LLVMTypeRef type = LLVMFunctionType(returns_integer ? s->integer :
        LLVMVoidTypeInContext(s->context), arguments, count, 0);
    return LLVMAddFunction(s->module, name, type);
}

int64_t freak_ib_session_new(freak_word name, int64_t optimization) {
    ib_global_error[0] = 0;
    unsigned major = 0, minor = 0, patch = 0;
    LLVMGetVersion(&major, &minor, &patch);
    if (major != 19 || minor != 1 || patch != 7) {
        ib_fail(NULL, "experimental bridge requires LLVM 19.1.7"); return 0;
    }
    if (optimization < 0 || optimization > 3) {
        ib_fail(NULL, "experimental optimization must be 0, 1, 2 or 3"); return 0;
    }
    char *module_name = ib_text(NULL, name, 0);
    if (!module_name) return 0;
    for (unsigned i = 0; i < IB_MAX_SESSIONS; ++i) {
        struct ib_session *s = &ib_sessions[i];
        if (s->ticket) continue;
        memset(s, 0, sizeof(*s));
        s->ticket = ib_register(NULL, IB_SESSION, s, NULL);
        if (!s->ticket) { free(module_name); return 0; }
        s->context = LLVMContextCreate();
        s->module = LLVMModuleCreateWithNameInContext(module_name, s->context);
        s->builder = LLVMCreateBuilderInContext(s->context);
        s->integer = LLVMInt64TypeInContext(s->context);
        s->boolean = LLVMInt1TypeInContext(s->context);
        s->optimization = (int)optimization;
        free(module_name);
        return s->ticket;
    }
    free(module_name);
    ib_fail(NULL, "experimental builder session limit reached");
    return 0;
}
freak_word freak_ib_error(int64_t session) {
    struct ib_session *s = session ? ib_get(session) : NULL;
    const char *message = s ? s->error : ib_global_error;
    size_t length = strlen(message);
    char *copy = malloc(length + 1);
    if (!copy) return freak_word_lit("could not copy builder diagnostic");
    memcpy(copy, message, length + 1);
    return freak_word_own(copy, length);
}
int64_t freak_ib_session_release(int64_t session) {
    struct ib_session *s = ib_get(session);
    if (!s) return 0;
    for (size_t i = 0; i < IB_MAX_TICKETS; ++i) {
        struct ib_ticket *entry = &ib_tickets[i];
        if (entry->session == session ||
            (entry->kind == IB_SESSION && entry->reference == s)) {
            entry->kind = IB_EMPTY;
            entry->session = 0;
            entry->reference = NULL;
            entry->function = NULL;
        }
    }
    LLVMDisposeBuilder(s->builder);
    LLVMDisposeModule(s->module);
    LLVMContextDispose(s->context);
    memset(s, 0, sizeof(*s));
    return 1;
}
int64_t freak_ib_live_sessions(void) {
    int64_t count = 0;
    for (unsigned i = 0; i < IB_MAX_SESSIONS; ++i) if (ib_sessions[i].ticket) ++count;
    return count;
}
int64_t freak_ib_live_tickets(void) {
    int64_t count = 0;
    for (size_t i = 0; i < IB_MAX_TICKETS; ++i) if (ib_tickets[i].kind != IB_EMPTY) ++count;
    return count;
}
int64_t freak_ib_function(int64_t session, freak_word name, int64_t parameters,
                          int64_t returns_integer) {
    struct ib_session *s = ib_get(session);
    if (!s || *s->error || s->finished) return 0;
    if (parameters < 0 || parameters > IB_MAX_ARGUMENTS ||
        (returns_integer != 0 && returns_integer != 1)) {
        ib_fail(s, "invalid experimental scalar function signature"); return 0;
    }
    char *symbol = ib_text(s, name, 0);
    if (!symbol) return 0;
    if (strncmp(symbol, "__freak_user_", 13) || !symbol[13]) {
        free(symbol); ib_fail(s, "source functions require the private user prefix"); return 0;
    }
    if (LLVMGetNamedFunction(s->module, symbol)) {
        free(symbol); ib_fail(s, "duplicate builder function"); return 0;
    }
    LLVMTypeRef types[IB_MAX_ARGUMENTS];
    for (int64_t i = 0; i < parameters; ++i) types[i] = s->integer;
    LLVMTypeRef type = LLVMFunctionType(returns_integer ? s->integer :
        LLVMVoidTypeInContext(s->context), types, (unsigned)parameters, 0);
    LLVMValueRef function = LLVMAddFunction(s->module, symbol, type);
    free(symbol);
    return ib_register(s, IB_FUNCTION, function, function);
}
int64_t freak_ib_parameter(int64_t session, int64_t function, int64_t index) {
    struct ib_session *s = ib_get(session);
    struct ib_ticket *entry = ib_owned(s, function, IB_FUNCTION);
    if (!entry) return 0;
    if (index < 0 || index >= LLVMCountParams(entry->reference)) {
        ib_fail(s, "builder parameter index is outside the signature"); return 0;
    }
    return ib_register(s, IB_VALUE, LLVMGetParam(entry->reference, (unsigned)index), entry->reference);
}
int64_t freak_ib_block(int64_t session, int64_t function, freak_word name) {
    struct ib_session *s = ib_get(session);
    struct ib_ticket *entry = ib_owned(s, function, IB_FUNCTION);
    if (!entry) return 0;
    char *label = ib_text(s, name, 0);
    if (!label) return 0;
    LLVMBasicBlockRef block = LLVMAppendBasicBlockInContext(s->context, entry->reference, label);
    free(label);
    return ib_register(s, IB_BLOCK, block, entry->reference);
}
int64_t freak_ib_position(int64_t session, int64_t block) {
    struct ib_session *s = ib_get(session);
    struct ib_ticket *entry = ib_owned(s, block, IB_BLOCK);
    if (!entry) return 0;
    if (LLVMGetBasicBlockTerminator(entry->reference)) {
        ib_fail(s, "cannot append instructions to a terminated block"); return 0;
    }
    LLVMPositionBuilderAtEnd(s->builder, entry->reference);
    return 1;
}
int64_t freak_ib_integer(int64_t session, int64_t value) {
    struct ib_session *s = ib_get(session);
    if (!s || *s->error || s->finished) return 0;
    return ib_register(s, IB_VALUE, LLVMConstInt(s->integer, (uint64_t)value, 1), NULL);
}
int64_t freak_ib_boolean(int64_t session, int64_t value) {
    struct ib_session *s = ib_get(session);
    if (!s || *s->error || s->finished) return 0;
    if (value != 0 && value != 1) { ib_fail(s, "invalid boolean constant"); return 0; }
    return ib_register(s, IB_VALUE, LLVMConstInt(s->boolean, (uint64_t)value, 0), NULL);
}
int64_t freak_ib_slot(int64_t session) {
    struct ib_session *s = ib_get(session);
    LLVMValueRef function = ib_current_function(s);
    if (!function) return 0;
    LLVMBasicBlockRef entry = LLVMGetEntryBasicBlock(function);
    LLVMBuilderRef local = LLVMCreateBuilderInContext(s->context);
    LLVMValueRef first = LLVMGetFirstInstruction(entry);
    if (first) LLVMPositionBuilderBefore(local, first);
    else LLVMPositionBuilderAtEnd(local, entry);
    LLVMValueRef slot = LLVMBuildAlloca(local, s->integer, "local");
    LLVMDisposeBuilder(local);
    return ib_register(s, IB_SLOT, slot, function);
}
int64_t freak_ib_load(int64_t session, int64_t slot) {
    struct ib_session *s = ib_get(session);
    LLVMValueRef function = ib_current_function(s);
    struct ib_ticket *entry = ib_owned(s, slot, IB_SLOT);
    if (!function || !entry) return 0;
    if (entry->function != function) { ib_fail(s, "slot belongs to another function"); return 0; }
    return ib_register(s, IB_VALUE, LLVMBuildLoad2(s->builder, s->integer,
        entry->reference, "load"), function);
}
int64_t freak_ib_store(int64_t session, int64_t slot, int64_t value) {
    struct ib_session *s = ib_get(session);
    LLVMValueRef function = ib_current_function(s);
    struct ib_ticket *entry = ib_owned(s, slot, IB_SLOT);
    LLVMValueRef operand = ib_operand(s, value, s ? s->integer : NULL, function);
    if (!function || !entry || !operand) return 0;
    if (entry->function != function) { ib_fail(s, "slot belongs to another function"); return 0; }
    LLVMBuildStore(s->builder, operand, entry->reference);
    return 1;
}
int64_t freak_ib_arithmetic(int64_t session, int64_t operation,
                           int64_t left, int64_t right) {
    static const char *names[] = {"freak_int_add_checked", "freak_int_sub_checked",
        "freak_int_mul_checked", "freak_int_div_checked", "freak_int_rem_checked"};
    struct ib_session *s = ib_get(session);
    LLVMValueRef function = ib_current_function(s);
    LLVMValueRef arguments[2] = {
        ib_operand(s, left, s ? s->integer : NULL, function),
        ib_operand(s, right, s ? s->integer : NULL, function)};
    if (!function || !arguments[0] || !arguments[1]) return 0;
    if (operation < 0 || operation >= 5) { ib_fail(s, "unsupported integer operation"); return 0; }
    LLVMValueRef callee = ib_runtime(s, names[operation], 2, 1);
    return ib_register(s, IB_VALUE, LLVMBuildCall2(s->builder,
        LLVMGlobalGetValueType(callee), callee, arguments, 2, "checked"), function);
}
int64_t freak_ib_negate(int64_t session, int64_t value) {
    struct ib_session *s = ib_get(session);
    LLVMValueRef function = ib_current_function(s);
    LLVMValueRef operand = ib_operand(s, value, s ? s->integer : NULL, function);
    if (!function || !operand) return 0;
    LLVMValueRef callee = ib_runtime(s, "freak_int_neg_checked", 1, 1);
    return ib_register(s, IB_VALUE, LLVMBuildCall2(s->builder,
        LLVMGlobalGetValueType(callee), callee, &operand, 1, "negate"), function);
}
int64_t freak_ib_compare(int64_t session, int64_t operation,
                        int64_t left, int64_t right) {
    static const LLVMIntPredicate predicates[] = {
        LLVMIntEQ, LLVMIntNE, LLVMIntSLT, LLVMIntSLE, LLVMIntSGT, LLVMIntSGE};
    struct ib_session *s = ib_get(session);
    LLVMValueRef function = ib_current_function(s);
    LLVMValueRef lhs = ib_operand(s, left, s ? s->integer : NULL, function);
    LLVMValueRef rhs = ib_operand(s, right, s ? s->integer : NULL, function);
    if (!function || !lhs || !rhs) return 0;
    if (operation < 0 || operation >= 6) { ib_fail(s, "unsupported integer comparison"); return 0; }
    return ib_register(s, IB_VALUE, LLVMBuildICmp(s->builder, predicates[operation],
        lhs, rhs, "compare"), function);
}
int64_t freak_ib_not(int64_t session, int64_t value) {
    struct ib_session *s = ib_get(session);
    LLVMValueRef function = ib_current_function(s);
    LLVMValueRef operand = ib_operand(s, value, s ? s->boolean : NULL, function);
    if (!function || !operand) return 0;
    return ib_register(s, IB_VALUE, LLVMBuildNot(s->builder, operand, "not"), function);
}
int64_t freak_ib_call_begin(int64_t session, int64_t function) {
    struct ib_session *s = ib_get(session);
    struct ib_ticket *entry = ib_owned(s, function, IB_FUNCTION);
    if (!entry || !ib_current_function(s)) return 0;
    if (s->pending_function) { ib_fail(s, "unfinished builder argument list"); return 0; }
    s->pending_function = entry->reference;
    s->pending_count = 0;
    return 1;
}
int64_t freak_ib_call_argument(int64_t session, int64_t value) {
    struct ib_session *s = ib_get(session);
    LLVMValueRef function = ib_current_function(s);
    LLVMValueRef operand = ib_operand(s, value, s ? s->integer : NULL, function);
    if (!function || !operand) return 0;
    if (!s->pending_function || s->pending_count >= LLVMCountParams(s->pending_function) ||
        s->pending_count >= IB_MAX_ARGUMENTS) { ib_fail(s, "invalid builder argument count"); return 0; }
    s->pending_arguments[s->pending_count++] = operand;
    return 1;
}
int64_t freak_ib_call_end(int64_t session) {
    struct ib_session *s = ib_get(session);
    LLVMValueRef function = ib_current_function(s);
    if (!function) return 0;
    if (!s->pending_function || s->pending_count != LLVMCountParams(s->pending_function)) {
        ib_fail(s, "incomplete builder argument list"); return 0;
    }
    LLVMValueRef callee = s->pending_function;
    int returns_void = LLVMGetTypeKind(LLVMGetReturnType(LLVMGlobalGetValueType(callee))) == LLVMVoidTypeKind;
    LLVMValueRef result = LLVMBuildCall2(s->builder, LLVMGlobalGetValueType(callee),
        callee, s->pending_arguments, s->pending_count, returns_void ? "" : "call");
    s->pending_function = NULL;
    s->pending_count = 0;
    return ib_register(s, IB_VALUE, result, function);
}
int64_t freak_ib_say(int64_t session, int64_t value) {
    struct ib_session *s = ib_get(session);
    LLVMValueRef function = ib_current_function(s);
    LLVMValueRef operand = ib_operand(s, value, s ? s->integer : NULL, function);
    if (!function || !operand) return 0;
    LLVMValueRef printer = ib_runtime(s, "freak_llvm_print_int", 1, 0);
    LLVMBuildCall2(s->builder, LLVMGlobalGetValueType(printer), printer, &operand, 1, "");
    printer = ib_runtime(s, "freak_llvm_print_newline", 0, 0);
    LLVMBuildCall2(s->builder, LLVMGlobalGetValueType(printer), printer, NULL, 0, "");
    return 1;
}
int64_t freak_ib_jump(int64_t session, int64_t destination) {
    struct ib_session *s = ib_get(session);
    LLVMValueRef function = ib_current_function(s);
    struct ib_ticket *entry = ib_owned(s, destination, IB_BLOCK);
    if (!function || !entry) return 0;
    if (entry->function != function) { ib_fail(s, "branch targets another function"); return 0; }
    LLVMBuildBr(s->builder, entry->reference);
    return 1;
}
int64_t freak_ib_branch(int64_t session, int64_t condition,
                       int64_t then_block, int64_t else_block) {
    struct ib_session *s = ib_get(session);
    LLVMValueRef function = ib_current_function(s);
    LLVMValueRef test = ib_operand(s, condition, s ? s->boolean : NULL, function);
    struct ib_ticket *yes = ib_owned(s, then_block, IB_BLOCK);
    struct ib_ticket *no = ib_owned(s, else_block, IB_BLOCK);
    if (!function || !test || !yes || !no) return 0;
    if (yes->function != function || no->function != function) {
        ib_fail(s, "conditional branch targets another function"); return 0;
    }
    LLVMBuildCondBr(s->builder, test, yes->reference, no->reference);
    return 1;
}
int64_t freak_ib_return(int64_t session, int64_t value) {
    struct ib_session *s = ib_get(session);
    LLVMValueRef function = ib_current_function(s);
    if (!function) return 0;
    LLVMTypeRef result = LLVMGetReturnType(LLVMGlobalGetValueType(function));
    if (LLVMGetTypeKind(result) == LLVMVoidTypeKind && value == 0) {
        LLVMBuildRetVoid(s->builder); return 1;
    }
    LLVMValueRef operand = ib_operand(s, value, result, function);
    if (!operand) return 0;
    LLVMBuildRet(s->builder, operand);
    return 1;
}
int64_t freak_ib_native_main(int64_t session, int64_t function) {
    struct ib_session *s = ib_get(session);
    struct ib_ticket *entry = ib_owned(s, function, IB_FUNCTION);
    if (!entry) return 0;
    LLVMValueRef callee = entry->reference;
    if (LLVMCountParams(callee) || LLVMGetNamedFunction(s->module, "main")) {
        ib_fail(s, "invalid or duplicate native entry"); return 0;
    }
    LLVMTypeRef result = LLVMGetReturnType(LLVMGlobalGetValueType(callee));
    if (result != s->integer && LLVMGetTypeKind(result) != LLVMVoidTypeKind) {
        ib_fail(s, "unsupported native entry result"); return 0;
    }
    LLVMTypeRef i32 = LLVMInt32TypeInContext(s->context);
    LLVMTypeRef type = LLVMFunctionType(i32, NULL, 0, 0);
    LLVMValueRef native = LLVMAddFunction(s->module, "main", type);
    LLVMBasicBlockRef block = LLVMAppendBasicBlockInContext(s->context, native, "entry");
    LLVMPositionBuilderAtEnd(s->builder, block);
    LLVMValueRef value = LLVMBuildCall2(s->builder, LLVMGlobalGetValueType(callee),
        callee, NULL, 0, result == s->integer ? "exit.value" : "");
    if (result == s->integer) value = LLVMBuildTrunc(s->builder, value, i32, "exit.status");
    else value = LLVMConstInt(i32, 0, 0);
    LLVMBuildRet(s->builder, value);
    return 1;
}
int64_t freak_ib_unreachable(int64_t session) {
    struct ib_session *s = ib_get(session);
    if (!ib_current_function(s)) return 0;
    LLVMBuildUnreachable(s->builder);
    return 1;
}
static int ib_verify(struct ib_session *s) {
    char *message = NULL;
    int failed = LLVMVerifyModule(s->module, LLVMReturnStatusAction, &message);
    if (failed) ib_fail(s, message ? message : "LLVM module verification failed");
    LLVMDisposeMessage(message);
    return !failed;
}
int64_t freak_ib_emit_object(int64_t session, freak_word output) {
    struct ib_session *s = ib_get(session);
    if (!s || *s->error || s->finished) return 0;
    if (s->pending_function) { ib_fail(s, "unfinished builder call"); return 0; }
    char *path = ib_text(s, output, 0);
    if (!path) return 0;
    LLVMTargetMachineRef machine = NULL;
    LLVMTargetDataRef layout = NULL;
    LLVMMemoryBufferRef object = NULL;
    char *triple = NULL, *message = NULL;
    LLVMPassBuilderOptionsRef options = NULL;
    FILE *file = NULL;
    int owns_output = 0, success = 0;
    if (!ib_verify(s)) goto done;
    if (LLVMInitializeNativeTarget() || LLVMInitializeNativeAsmPrinter()) {
        ib_fail(s, "LLVM SDK has no native target/printer"); goto done;
    }
    triple = LLVMGetDefaultTargetTriple();
    LLVMTargetRef target = NULL;
    if (LLVMGetTargetFromTriple(triple, &target, &message)) {
        ib_fail(s, message ? message : "LLVM native target lookup failed"); goto done;
    }
    LLVMCodeGenOptLevel levels[] = {LLVMCodeGenLevelNone, LLVMCodeGenLevelLess,
        LLVMCodeGenLevelDefault, LLVMCodeGenLevelAggressive};
    machine = LLVMCreateTargetMachine(target, triple, "generic", "",
        levels[s->optimization], LLVMRelocPIC, LLVMCodeModelDefault);
    if (!machine) { ib_fail(s, "LLVM native target machine creation failed"); goto done; }
    LLVMSetTarget(s->module, triple);
    layout = LLVMCreateTargetDataLayout(machine);
    LLVMSetModuleDataLayout(s->module, layout);
    options = LLVMCreatePassBuilderOptions();
    LLVMPassBuilderOptionsSetVerifyEach(options, 1);
    char pipeline[16];
    snprintf(pipeline, sizeof(pipeline), "default<O%d>", s->optimization);
    LLVMErrorRef error = LLVMRunPasses(s->module, pipeline, machine, options);
    if (error) {
        char *pass_error = LLVMGetErrorMessage(error);
        ib_fail(s, pass_error ? pass_error : "LLVM optimization failed");
        LLVMDisposeErrorMessage(pass_error);
        goto done;
    }
    if (!ib_verify(s)) goto done;
    if (LLVMTargetMachineEmitToMemoryBuffer(machine, s->module, LLVMObjectFile, &message, &object)) {
        ib_fail(s, message ? message : "LLVM native object generation failed"); goto done;
    }
    /* LLVM produces the bytes. Exclusive creation avoids following an output
     * symlink; on ordinary write/close failure remove only the file we created. */
    file = fopen(path, "wbx");
    if (!file) { ib_fail(s, "could not exclusively create builder object"); goto done; }
    owns_output = 1;
    size_t size = LLVMGetBufferSize(object);
    if (!size || fwrite(LLVMGetBufferStart(object), 1, size, file) != size ||
        fflush(file) || ferror(file)) {
        ib_fail(s, "could not write complete builder object"); goto done;
    }
    if (fclose(file)) { file = NULL; ib_fail(s, "could not close builder object"); goto done; }
    file = NULL;
    s->finished = 1;
    success = 1;
done:
    if (file && fclose(file)) ib_fail(s, "could not close failed builder object");
    if (!success && owns_output && remove(path)) ib_fail(s, "could not remove failed builder object");
    if (object) LLVMDisposeMemoryBuffer(object);
    if (options) LLVMDisposePassBuilderOptions(options);
    if (layout) LLVMDisposeTargetData(layout);
    if (machine) LLVMDisposeTargetMachine(machine);
    LLVMDisposeMessage(message);
    LLVMDisposeMessage(triple);
    free(path);
    return success;
}
